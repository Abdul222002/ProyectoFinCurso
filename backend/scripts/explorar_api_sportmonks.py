"""
Script para explorar los endpoints disponibles de Sportmonks API
y encontrar la mejor forma de obtener los jugadores
"""

import requests
import json

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
SEASON_ID = 21787  # Scottish Premiership

def test_endpoint(name, url, params):
    """Prueba un endpoint y muestra los resultados"""
    print(f"\n{'='*60}")
    print(f"🔍 Probando: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, params=params, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Guardar respuesta completa
            filename = f"{name.replace(' ', '_').lower()}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Respuesta guardada en: {filename}")
            
            # Mostrar estructura
            if 'data' in data:
                items = data['data']
                if isinstance(items, list):
                    print(f"📊 Elementos encontrados: {len(items)}")
                    if len(items) > 0:
                        print(f"\n📋 Estructura del primer elemento:")
                        print(json.dumps(items[0], indent=2)[:500] + "...")
                elif isinstance(items, dict):
                    print(f"📦 Objeto único encontrado")
                    print(f"\n📋 Claves disponibles: {list(items.keys())}")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Respuesta: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False


def main():
    print("="*60)
    print("🚀 EXPLORADOR DE API SPORTMONKS")
    print("="*60)
    
    # 1. Obtener equipos de la temporada
    test_endpoint(
        "Teams Season",
        f"https://api.sportmonks.com/v3/football/teams/seasons/{SEASON_ID}",
        {"api_token": API_TOKEN}
    )
    
    # 2. Intentar obtener jugadores directamente de un equipo específico
    # Primero necesitamos un team_id, usemos Celtic (ID común: 2)
    test_endpoint(
        "Team Players Celtic",
        "https://api.sportmonks.com/v3/football/players/teams/2",
        {"api_token": API_TOKEN}
    )
    
    # 3. Probar endpoint de squad
    test_endpoint(
        "Squad Season Team",
        f"https://api.sportmonks.com/v3/football/squads/seasons/{SEASON_ID}/teams/2",
        {"api_token": API_TOKEN}
    )
    
    # 4. Buscar jugadores por nombre (ejemplo)
    test_endpoint(
        "Search Player",
        "https://api.sportmonks.com/v3/football/players/search/Kyogo",
        {"api_token": API_TOKEN}
    )
    
    # 5. Probar obtener info de temporada
    test_endpoint(
        "Season Info",
        f"https://api.sportmonks.com/v3/football/seasons/{SEASON_ID}",
        {"api_token": API_TOKEN}
    )
    
    print("\n" + "="*60)
    print("✅ Exploración completada")
    print("="*60)
    print("\n💡 Revisa los archivos JSON generados para ver qué datos están disponibles")


if __name__ == "__main__":
    main()
