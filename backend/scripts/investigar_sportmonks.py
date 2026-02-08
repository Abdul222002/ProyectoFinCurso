"""
Script para encontrar la temporada correcta de la Scottish Premiership
y verificar qué datos están disponibles
"""

import requests
import json

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"

def buscar_liga_escocesa():
    """Busca la liga escocesa"""
    print("🔍 Buscando liga escocesa...")
    url = "https://api.sportmonks.com/v3/football/leagues/search/scottish"
    params = {"api_token": API_TOKEN}
    
    response = requests.get(url, params=params, timeout=15)
    if response.status_code == 200:
        data = response.json()
        ligas = data.get('data', [])
        print(f"✅ Encontradas {len(ligas)} ligas\n")
        
        for liga in ligas:
            print(f"📋 {liga.get('name')} (ID: {liga.get('id')})")
            print(f"   País: {liga.get('country', {}).get('name', 'N/A')}")
            print()
        
        return ligas
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text[:500])
    return []


def obtener_temporadas_liga(league_id):
    """Obtiene las temporadas de una liga"""
    print(f"\n🔍 Obteniendo temporadas de liga {league_id}...")
    url = f"https://api.sportmonks.com/v3/football/seasons/leagues/{league_id}"
    params = {"api_token": API_TOKEN}
    
    response = requests.get(url, params=params, timeout=15)
    if response.status_code == 200:
        data = response.json()
        temporadas = data.get('data', [])
        print(f"✅ Encontradas {len(temporadas)} temporadas\n")
        
        # Mostrar las últimas 5 temporadas
        for temp in temporadas[-5:]:
            print(f"📅 {temp.get('name')} (ID: {temp.get('id')})")
            print(f"   Inicio: {temp.get('starting_at')}")
            print(f"   Fin: {temp.get('ending_at')}")
            print()
        
        return temporadas
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text[:500])
    return []


def probar_endpoint_teams_con_include(season_id):
    """Prueba el endpoint de teams con diferentes includes"""
    print(f"\n🧪 Probando endpoint teams/seasons/{season_id} con includes...")
    
    includes_to_test = [
        None,
        "players",
        "squad",
        "activeSeasons",
    ]
    
    for include in includes_to_test:
        url = f"https://api.sportmonks.com/v3/football/teams/seasons/{season_id}"
        params = {"api_token": API_TOKEN}
        if include:
            params["include"] = include
        
        print(f"\n   Testing include='{include}'...")
        
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                teams = data.get('data', [])
                print(f"   ✅ {len(teams)} equipos")
                
                if teams and include:
                    first_team = teams[0]
                    print(f"   📋 Claves del primer equipo: {list(first_team.keys())[:10]}...")
                    
                    # Guardar para inspección
                    filename = f"teams_include_{include or 'none'}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(first_team, f, indent=2, ensure_ascii=False)
                    print(f"   💾 Guardado en: {filename}")
            else:
                print(f"   ❌ Error {response.status_code}")
                error_data = response.json()
                if 'message' in error_data:
                    print(f"   Mensaje: {error_data['message'][:100]}")
        except Exception as e:
            print(f"   ❌ Excepción: {e}")


def probar_endpoint_fixtures(season_id):
    """Prueba obtener partidos (fixtures) de la temporada"""
    print(f"\n🧪 Probando endpoint fixtures/seasons/{season_id}...")
    
    url = f"https://api.sportmonks.com/v3/football/fixtures/seasons/{season_id}"
    params = {
        "api_token": API_TOKEN,
        "per_page": 5  # Solo los primeros 5 para probar
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            fixtures = data.get('data', [])
            print(f"   ✅ {len(fixtures)} partidos encontrados")
            
            if fixtures:
                with open("fixtures_sample.json", 'w', encoding='utf-8') as f:
                    json.dump(fixtures[0], f, indent=2, ensure_ascii=False)
                print(f"   💾 Primer partido guardado en: fixtures_sample.json")
                print(f"   📋 Claves disponibles: {list(fixtures[0].keys())}")
        else:
            print(f"   ❌ Error {response.status_code}")
    except Exception as e:
        print(f"   ❌ Excepción: {e}")


def main():
    print("="*60)
    print("🔎 INVESTIGACIÓN PROFUNDA - SPORTMONKS API")
    print("="*60 + "\n")
    
    # 1. Buscar la liga escocesa
    ligas = buscar_liga_escocesa()
    
    if not ligas:
        print("\n⚠️  No se encontró la liga escocesa")
        return
    
    # Usar la primera liga (debería ser Scottish Premiership)
    liga_id = ligas[0]['id']
    print(f"\n✅ Usando liga: {ligas[0]['name']} (ID: {liga_id})")
    
    # 2. Obtener temporadas
    temporadas = obtener_temporadas_liga(liga_id)
    
    if not temporadas:
        print("\n⚠️  No se encontraron temporadas")
        return
    
    # Usar la temporada más reciente
    temporada_actual = temporadas[-1]
    season_id = temporada_actual['id']
    print(f"\n✅ Usando temporada: {temporada_actual['name']} (ID: {season_id})")
    
    # 3. Probar diferentes includes
    probar_endpoint_teams_con_include(season_id)
    
    # 4. Probar endpoint de fixtures
    probar_endpoint_fixtures(season_id)
    
    print("\n" + "="*60)
    print("✅ Investigación completada")
    print("="*60)
    print("\n💡 Revisa los archivos JSON generados para ver qué datos están disponibles")


if __name__ == "__main__":
    main()
