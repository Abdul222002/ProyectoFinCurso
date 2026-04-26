"""
Script FINAL - Obtiene datos completos de jugadores de Sportmonks
Hace llamadas individuales para cada player_id
"""

import requests
import json
import time

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
SEASON_ID = 21787

print("="*60)
print("🔍 OBTENIENDO DATOS COMPLETOS DE JUGADORES")
print("="*60 + "\n")

# 1. Obtener equipos con player_ids
print("📋 Paso 1: Obteniendo equipos y player_ids...")
url = f"https://api.sportmonks.com/v3/football/teams/seasons/{SEASON_ID}"
params = {
    "api_token": API_TOKEN,
    "include": "players"
}

response = requests.get(url, params=params, timeout=30)
teams_data = response.json().get('data', [])

print(f"✅ {len(teams_data)} equipos encontrados\n")

# Recopilar todos los player_ids
all_player_ids = []
team_mapping = {}  # player_id -> team_name

for team in teams_data:
    team_name = team.get('name')
    players = team.get('players', [])
    
    print(f"   {team_name}: {len(players)} jugadores")
    
    for player_data in players:
        player_id = player_data.get('player_id')
        if player_id:
            all_player_ids.append(player_id)
            team_mapping[player_id] = team_name

print(f"\n✅ Total player_ids: {len(all_player_ids)}\n")

# 2. Obtener datos completos de los primeros 10 jugadores (PRUEBA)
print("📡 Paso 2: Obteniendo datos completos (probando con 10 jugadores)...\n")

complete_players = []

for i, player_id in enumerate(all_player_ids[:10]):  # Solo 10 para probar
    try:
        url_player = f"https://api.sportmonks.com/v3/football/players/{player_id}"
        params_player = {"api_token": API_TOKEN}
        
        response = requests.get(url_player, params=params_player, timeout=10)
        
        if response.status_code == 200:
            player_data = response.json().get('data', {})
            player_name = player_data.get('display_name') or player_data.get('common_name') or player_data.get('name', 'Unknown')
            team_name = team_mapping.get(player_id, 'Unknown')
            
            complete_players.append({
                'id': player_id,
                'name': player_name,
                'team': team_name,
                'data': player_data
            })
            
            print(f"   ✅ {i+1}/10: {player_name} - {team_name}")
        else:
            print(f"   ❌ {i+1}/10: Error {response.status_code} para player_id {player_id}")
        
        # Respetar rate limit
        time.sleep(0.3)
        
    except Exception as e:
        print(f"   ❌ {i+1}/10: Excepción - {e}")

# 3. Guardar resultados
if complete_players:
    with open('jugadores_completos_sample.json', 'w', encoding='utf-8') as f:
        json.dump(complete_players, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Datos guardados en: jugadores_completos_sample.json")
    print(f"\n📋 Ejemplo del primer jugador:")
    print(f"   Nombre: {complete_players[0]['name']}")
    print(f"   Equipo: {complete_players[0]['team']}")
    print(f"   Claves disponibles: {list(complete_players[0]['data'].keys())[:15]}...")

print("\n" + "="*60)
print("💡 CONCLUSIÓN")
print("="*60)
print(f"Total de jugadores en la liga: {len(all_player_ids)}")
print(f"Jugadores probados: {len(complete_players)}")
print(f"\n⚠️  Para obtener TODOS los jugadores necesitas:")
print(f"   - Hacer {len(all_player_ids)} llamadas a la API")
print(f"   - Tiempo estimado: ~{len(all_player_ids) * 0.3 / 60:.1f} minutos")
print(f"   - Rate limit: {3000} llamadas disponibles")
print("\n✅ ¿Proceder con la importación completa? (Crear script separado)")
