"""
Script: download_player_images.py
Descarga las imágenes de todos los jugadores desde sus URLs externas (Google/Sportmonks)
y las guarda en static/players/{player_id}.png, actualizando la BD.

Mejoras sobre la versión base:
- Reintentos automáticos (hasta 3 intentos por jugador)
- Validación de que el contenido descargado es realmente una imagen
- Descarga paralela con ThreadPoolExecutor para velocidad
- Progress bar con estadísticas en tiempo real
- Resumen detallado al final
- Idempotente: omite jugadores ya migrados (image_url empieza con /static/)
"""

import sys
import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Añadir el directorio raíz del backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.models import Player

# ============================================================
# CONFIGURACIÓN
# ============================================================
OUTPUT_DIR    = "static/players"
MAX_WORKERS   = 8          # Descargas en paralelo
MAX_RETRIES   = 3          # Intentos por jugador
TIMEOUT       = 15         # Segundos por petición
MIN_IMG_SIZE  = 500        # Bytes mínimos para considerar imagen válida

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/",
}

# Cabeceras mágicas comunes de formatos de imagen
IMAGE_MAGIC = [
    b"\xff\xd8\xff",       # JPEG
    b"\x89PNG",            # PNG
    b"GIF8",               # GIF
    b"RIFF",               # WebP (RIFF....WEBP)
    b"\x00\x00\x01\x00",  # ICO
    b"BM",                 # BMP
]


def is_valid_image(content: bytes) -> bool:
    """Comprueba que los bytes descargados empiezan con una cabecera de imagen conocida."""
    if len(content) < MIN_IMG_SIZE:
        return False
    for magic in IMAGE_MAGIC:
        if content.startswith(magic):
            return True
    return False


def download_one(player_id: int, player_name: str, url: str) -> dict:
    """
    Descarga la imagen de un jugador con reintentos.
    Devuelve un dict con: status ('ok'|'skip'|'fail'), filepath o error.
    """
    filename = f"{player_id}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    new_url   = f"/static/players/{filename}"

    # Ya migrada
    if url.startswith("/static/"):
        return {"status": "skip", "player_id": player_id, "new_url": url}

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
            if r.status_code == 200:
                content = r.content
                if not is_valid_image(content):
                    last_error = f"Contenido no es imagen válida ({len(content)} bytes)"
                    time.sleep(1)
                    continue
                with open(filepath, "wb") as f:
                    f.write(content)
                return {
                    "status": "ok",
                    "player_id": player_id,
                    "new_url": new_url,
                    "bytes": len(content),
                }
            else:
                last_error = f"HTTP {r.status_code}"
                time.sleep(attempt)  # Backoff
        except requests.exceptions.Timeout:
            last_error = f"Timeout (intento {attempt}/{MAX_RETRIES})"
            time.sleep(attempt)
        except Exception as e:
            last_error = str(e)
            time.sleep(attempt)

    return {
        "status": "fail",
        "player_id": player_id,
        "player_name": player_name,
        "error": last_error,
    }


def download_all(output_dir: str = OUTPUT_DIR):
    os.makedirs(output_dir, exist_ok=True)

    db = SessionLocal()
    try:
        players = db.query(Player).filter(Player.image_url.isnot(None)).all()
    finally:
        db.close()

    total = len(players)
    print(f"\n🚀 Iniciando descarga de imágenes para {total} jugadores")
    print(f"   Workers: {MAX_WORKERS} | Reintentos: {MAX_RETRIES} | Carpeta: {output_dir}")
    print("=" * 60)

    # Preparar trabajos: (player_id, name, url)
    jobs = [(p.id, p.name, p.image_url) for p in players]

    # Descargar en paralelo
    results = {}  # player_id -> result
    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(download_one, pid, name, url): pid
            for pid, name, url in jobs
        }
        for future in as_completed(future_map):
            result = future.result()
            results[result["player_id"]] = result
            completed += 1

            # Progress cada 20 o al terminar
            if completed % 20 == 0 or completed == total:
                ok    = sum(1 for r in results.values() if r["status"] == "ok")
                skip  = sum(1 for r in results.values() if r["status"] == "skip")
                fail  = sum(1 for r in results.values() if r["status"] == "fail")
                print(
                    f"  [{completed:>3}/{total}] "
                    f"✅ {ok} descargadas | ⏭️  {skip} ya migradas | ❌ {fail} fallidas",
                    flush=True,
                )

    # ── Actualizar BD en bloque ──────────────────────────────
    print("\n💾 Actualizando base de datos...")
    db = SessionLocal()
    try:
        updated = 0
        for player in db.query(Player).filter(Player.image_url.isnot(None)).all():
            res = results.get(player.id)
            if res and res["status"] == "ok":
                player.image_url = res["new_url"]
                updated += 1
        db.commit()
        print(f"   Registros actualizados: {updated}")
    except Exception as e:
        db.rollback()
        print(f"❌ Error al hacer commit: {e}")
        raise
    finally:
        db.close()

    # ── Resumen final ────────────────────────────────────────
    ok    = sum(1 for r in results.values() if r["status"] == "ok")
    skip  = sum(1 for r in results.values() if r["status"] == "skip")
    fail  = sum(1 for r in results.values() if r["status"] == "fail")

    total_bytes = sum(r.get("bytes", 0) for r in results.values() if r["status"] == "ok")
    mb = total_bytes / (1024 * 1024)

    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL")
    print("=" * 60)
    print(f"  ✅ Descargadas correctamente : {ok}")
    print(f"  ⏭️  Ya estaban migradas       : {skip}")
    print(f"  ❌ Fallidas                  : {fail}")
    print(f"  💾 Espacio ocupado           : {mb:.1f} MB")
    print("=" * 60)

    if fail > 0:
        print("\n⚠️  Jugadores con error:")
        for r in results.values():
            if r["status"] == "fail":
                print(f"   ID {r['player_id']:>4} | {r.get('player_name','?'):<30} | {r['error']}")

    return ok, skip, fail


if __name__ == "__main__":
    start = time.time()
    ok, skip, fail = download_all()
    elapsed = time.time() - start
    print(f"\n⏱️  Tiempo total: {elapsed:.1f}s")
    sys.exit(0 if fail == 0 else 1)
