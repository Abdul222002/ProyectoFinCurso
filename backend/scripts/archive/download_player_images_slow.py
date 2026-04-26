"""
Script: download_player_images_slow.py
Descarga LENTA de las imágenes de jugadores y leyendas para evitar HTTP 429 (Google ban).
Usa un solo hilo y un retraso entre peticiones.
Solo procesa jugadores cuya URL externa no haya sido migrada (= NO empieza por /static/).
"""

import sys
import os
import time
import requests
import urllib.parse

# Añadir el directorio raíz del backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.models import Player

import random

OUTPUT_DIR = "static/players"
MIN_IMG_SIZE = 500

# Wikimedia prefers a Referer to avoid hotlinking blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}

IMAGE_MAGIC = [
    b"\xff\xd8\xff",       # JPEG
    b"\x89PNG",            # PNG
    b"GIF8",               # GIF
    b"RIFF",               # WebP (RIFF....WEBP)
    b"\x00\x00\x01\x00",  # ICO
    b"BM",                 # BMP
]

def is_valid_image(content: bytes) -> bool:
    if len(content) < MIN_IMG_SIZE: return False
    for magic in IMAGE_MAGIC:
        if content.startswith(magic): return True
    return False

def download_slow():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    db = SessionLocal()
    
    # Obtener jugadores (normales y leyendas) que aún tienen URL externa
    players = db.query(Player).filter(
        Player.image_url.isnot(None),
        ~Player.image_url.like('/static/%')
    ).all()

    total = len(players)
    if total == 0:
        print("✅ No hay jugadores pendientes de migrar. Todos usan /static/.")
        db.close()
        return

    print(f"\n🐢 Iniciando descarga LENTA de {total} jugadores/leyendas pendientes")
    print(f"   Demora aleatoria para evitar políticas anti-bot de Wikimedia/Google")
    print("=" * 60)

    ok, fail = 0, 0
    total_bytes = 0

    # --- HELPER FUNCTIONS FOR WIKIMEDIA API ---
    def get_wikimedia_direct_url(url: str) -> str:
        """
        Convierte una URL de Wikimedia a su URL de descarga directa
        usando la API de Commons.
        """
        if 'wikimedia.org' not in url and 'wikipedia.org' not in url:
            return url
        
        try:
            filename = url.split('/')[-1]
            filename = urllib.parse.unquote(filename)
            
            # Usar la API de COMMONS por defecto para archivos en /commons/
            api_url = "https://commons.wikimedia.org/w/api.php"
            params = {
                "action": "query",
                "titles": f"File:{filename}",
                "prop": "imageinfo",
                "iiprop": "url",
                "format": "json"
            }
            # Usar un User-Agent simple para la API para evitar conflictos de headers de imagen
            api_headers = {"User-Agent": HEADERS["User-Agent"]}
            r = requests.get(api_url, params=params, timeout=10, headers=api_headers)
            # print(f"  [DEBUG] API URL: {r.url}") # Comentar debug tras verificar
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            
            for page in pages.values():
                imageinfo = page.get("imageinfo", [])
                if imageinfo:
                    direct_url = imageinfo[0]["url"]
                    return direct_url
                
            # Si no está en commons, probar en wikipedia (ej. archivos locales)
            if 'wikipedia.org' in url:
                lang = url.split('.')[0].split('/')[-1] if 'wikipedia.org' in url else 'en'
                api_url = f"https://{lang}.wikipedia.org/w/api.php" if len(lang) == 2 else "https://en.wikipedia.org/w/api.php"
                r = requests.get(api_url, params=params, timeout=10, headers=api_headers)
                data = r.json()
                pages = data.get("query", {}).get("pages", {})
                for page in pages.values():
                    imageinfo = page.get("imageinfo", [])
                    if imageinfo:
                        return imageinfo[0]["url"]
        
        except Exception as e:
            print(f"  [API Wikimedia falló: {e}]")
        
        return url

    def get_commons_direct_url(url: str) -> str:
        """Simplificado: redirige al resolvedor general"""
        return get_wikimedia_direct_url(url)
    # --- END HELPER FUNCTIONS ---

    for i, player in enumerate(players, 1):
        filename = f"{player.id}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        new_url = f"/static/players/{filename}"
        
        url = player.image_url
        name_tag = f"[{'LEYENDA' if player.is_legend else 'NORMAL'}] {player.name}"

        # Configurar headers dinámicos
        current_headers = HEADERS.copy()
        if "tmssl.akamaized.net" in url:
            current_headers["Referer"] = "https://www.transfermarkt.com/"

        # Evitar procesar URLs que ya son locales
        if url.startswith('/static') or url.startswith('static/'):
            # Si el archivo existe físicamente, nos aseguramos de que el DB esté actualizado también
            if os.path.exists(filepath):
                if player.image_url != new_url:
                    player.image_url = new_url
                    db.commit()
            print(f"[{i:03d}/{total}] Ya es local {name_tag[:15]}... ⏭️  (Ignorando)")
            continue

        # --- OPTIMIZACIÓN: Saltarse descarga si el archivo ya existe ---
        if os.path.exists(filepath):
            try:
                with open(filepath, "rb") as f:
                    content = f.read()
                if is_valid_image(content):
                    print(f"[{i:03d}/{total}] Archivo ya existe {name_tag[:15]}... ✅ (Se asocia ID={player.id} -> {filename})")
                    player.image_url = new_url
                    db.commit()
                    ok += 1
                    continue
            except Exception:
                pass
        # --- FIN OPTIMIZACIÓN ---

        # Saltar SVGs ya que no manejamos vectores o librerías externas de renderizado
        if url.lower().endswith('.svg'):
            print(f"[{i:03d}/{total}] Saltando {name_tag[:15]}... ⏭️  (SVG no soportado)")
            continue

        # Resolver URL real si es Wikimedia
        if 'wikimedia.org' in url or 'wikipedia.org' in url:
            resolved_url = get_commons_direct_url(url)
            if resolved_url != url:
                print(f"\n  → Resuelto via API: {resolved_url[-40:]}")
            safe_url = resolved_url
        else:
            parsed = urllib.parse.urlparse(url)
            quoted_path = urllib.parse.quote(parsed.path)
            safe_url = urllib.parse.urlunparse(parsed._replace(path=quoted_path))

        print(f"[{i:03d}/{total}] Descargando {name_tag[:30]:<30} ... ", end="", flush=True)

        attempts = 2
        success = False
        while attempts > 0:
            try:
                r = requests.get(safe_url, timeout=20, headers=current_headers)
                if r.status_code == 200:
                    content = r.content
                    if is_valid_image(content):
                        with open(filepath, "wb") as f:
                            f.write(content)
                        player.image_url = new_url
                        db.commit()
                        ok += 1
                        total_bytes += len(content)
                        print(f"✅ OK ({len(content)//1024} KB)")
                        success = True
                        break
                    else:
                        fail += 1
                        print(f"❌ No es imagen real ({len(content)} bytes)")
                        attempts = 0 # No reintentar si no es imagen
                elif r.status_code == 429:
                    print("⚠️  429 Detectado. Esperando 60s...")
                    time.sleep(60)
                    attempts -= 1
                elif r.status_code == 403:
                    print(f"❌ HTTP 403 (Forbidden) - Wikimedia/Server bloqueó el bot.")
                    attempts = 0
                else:
                    print(f"❌ HTTP {r.status_code}")
                    attempts = 0
                    
            except Exception as e:
                print(f"❌ Error: {str(e)[:20]}")
                attempts = 0

        if not success and attempts == 0:
            # Si después de los reintentos falló de nuevo el 429
            if r.status_code == 429:
                print("🛑 Bloqueo persistente 429. Abortando script.")
                break
            fail += 1

        # Pausa aleatoria para parecer humano (5-12 seg)
        if i < total:
            time.sleep(random.uniform(5.5, 12.0))

    db.close()
    
    mb = total_bytes / (1024 * 1024)
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL DESCAGA LENTA")
    print("=" * 60)
    print(f"  ✅ Descargadas correctamente : {ok}")
    print(f"  ❌ Fallidas / Rate-Limited   : {fail}")
    print(f"  💾 Espacio ocupado           : {mb:.1f} MB")
    print("=" * 60)

if __name__ == "__main__":
    start = time.time()
    download_slow()
    elapsed = time.time() - start
    print(f"\n⏱️  Tiempo total: {elapsed:.1f}s")
