"""
Script para investigar PROFUNDAMENTE la API de Sportmonks
Probando diferentes endpoints e includes para obtener posiciones
"""

import requests
import json

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"

# IDs de ejemplo
PLAYER_ID = 2015  # Callum McGregor
TEAM_ID = 2033    # Celtic
SEASON_ID = 21787

def probar_endpoint(nombre, url, params):
    """Prueba un endpoint y muestra los resultados"""
    print(f"\n{'='*60}")
    print(f"🔍 {nombre}")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Params: {params}\n")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Guardar respuesta completa
            filename = f"api_response_{nombre.replace(' ', '_').lower()}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Status: {response.status_code}")
            print(f"💾 Guardado en: {filename}")
            
            # Mostrar estructura
            if 'data' in data:
                if isinstance(data['data'], list):
                    print(f"📊 Tipo: Lista con {len(data['data'])} elementos")
                    if len(data['data']) > 0:
                        print(f"🔑 Claves primer elemento:")
                        print(f"   {list(data['data'][0].keys())[:15]}")
                elif isinstance(data['data'], dict):
                    print(f"📊 Tipo: Diccionario")
                    print(f"🔑 Claves:")
                    print(f"   {list(data['data'].keys())[:15]}")
            
            return data
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Error: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return None


def investigar_api():
    """Investiga diferentes formas de obtener posiciones"""
    
    print("="*60)
    print("🔬 INVESTIGACIÓN PROFUNDA API SPORTMONKS")
    print("="*60)
    
    # 1. Player individual con TODOS los includes posibles
    print("\n\n" + "🧪 PRUEBA 1: Player con includes completos")
    url = f"https://api.sportmonks.com/v3/football/players/{PLAYER_ID}"
    params = {
        "api_token": API_TOKEN,
        "include": "position;detailedPosition;nationality;country;team;statistics"
    }
    probar_endpoint("Player_Full_Includes", url, params)
    
    # 2. Player solo con position
    print("\n\n" + "🧪 PRUEBA 2: Player con include=position")
    params = {
        "api_token": API_TOKEN,
        "include": "position"
    }
    probar_endpoint("Player_Position", url, params)
    
    # 3. Player con detailedPosition
    print("\n\n" + "🧪 PRUEBA 3: Player con include=detailedPosition")
    params = {
        "api_token": API_TOKEN,
        "include": "detailedPosition"
    }
    probar_endpoint("Player_DetailedPosition", url, params)
    
    # 4. Squad del equipo con includes
    print("\n\n" + "🧪 PRUEBA 4: Squad con includes")
    url = f"https://api.sportmonks.com/v3/football/squads/seasons/{SEASON_ID}/teams/{TEAM_ID}"
    params = {
        "api_token": API_TOKEN,
        "include": "player;position;detailedPosition"
    }
    probar_endpoint("Squad_Full", url, params)
    
    # 5. Team con squad y players
    print("\n\n" + "🧪 PRUEBA 5: Team con squad.player.position")
    url = f"https://api.sportmonks.com/v3/football/teams/{TEAM_ID}"
    params = {
        "api_token": API_TOKEN,
        "include": "activeSeasons;squad.player;squad.position"
    }
    probar_endpoint("Team_Squad_Position", url, params)
    
    # 6. Positions endpoint (si existe)
    print("\n\n" + "🧪 PRUEBA 6: Positions endpoint")
    url = f"https://api.sportmonks.com/v3/football/positions"
    params = {
        "api_token": API_TOKEN
    }
    probar_endpoint("Positions_List", url, params)
    
    # 7. Player statistics con position
    print("\n\n" + "🧪 PRUEBA 7: Player statistics")
    url = f"https://api.sportmonks.com/v3/football/players/{PLAYER_ID}"
    params = {
        "api_token": API_TOKEN,
        "include": "statistics;statistics.details;statistics.position"
    }
    probar_endpoint("Player_Statistics", url, params)
    
    print("\n\n" + "="*60)
    print("✅ INVESTIGACIÓN COMPLETADA")
    print("="*60)
    print("\n💡 Revisa los archivos JSON generados para encontrar las posiciones")
    print("📁 Archivos: api_response_*.json")


if __name__ == "__main__":
    investigar_api()
