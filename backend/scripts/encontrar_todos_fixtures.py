"""
Script para encontrar TODOS los fixtures de las jornadas 1, 2 y 3
de la Scottish Premiership 2024-25
"""

import requests

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
SEASON_ID = 21787

# Fixtures conocidos por jornada
KNOWN_FIXTURES = {
    1: 19428039,  # Jornada 1
    2: 19428044,  # Jornada 2
    3: 19428049,  # Jornada 3
}

print("=" * 80)
print("BUSCANDO TODOS LOS FIXTURES POR JORNADA")
print("=" * 80 + "\n")

all_fixtures_by_gameweek = {}

for gameweek_num, known_fixture_id in KNOWN_FIXTURES.items():
    print(f"Jornada {gameweek_num}: Usando fixture conocido {known_fixture_id}")
    
    # Obtener info del fixture conocido
    url = f"https://api.sportmonks.com/v3/football/fixtures/{known_fixture_id}"
    params = {
        "api_token": API_TOKEN,
        "include": "round"
    }
    
    response = requests.get(url, params=params, timeout=30)
    
    if response.status_code != 200:
        print(f"  ERROR obteniendo fixture {known_fixture_id}: {response.status_code}")
        continue
    
    data = response.json().get('data', {})
    round_info = data.get('round', {})
    round_id = round_info.get('id')
    round_name = round_info.get('name')
    
    print(f"  Round: {round_name} (ID: {round_id})")
    
    # Obtener TODOS los fixtures de ese round
    url_round = f"https://api.sportmonks.com/v3/football/fixtures"
    params_round = {
        "api_token": API_TOKEN,
        "filters": f"fixtureRounds:{round_id}",
        "include": "participants;state"
    }
    
    response_round = requests.get(url_round, params=params_round, timeout=30)
    
    if response_round.status_code != 200:
        print(f"  ERROR obteniendo fixtures del round: {response_round.status_code}")
        continue
    
    fixtures_data = response_round.json().get('data', [])
    
    print(f"  {len(fixtures_data)} partidos encontrados\n")
    
    fixture_ids = []
    
    for idx, fixture in enumerate(fixtures_data, 1):
        fix_id = fixture.get('id')
        state = fixture.get('state', {}).get('state', 'N/A')
        participants = fixture.get('participants', [])
        
        if len(participants) >= 2:
            home = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
            away = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
            
            home_name = home.get('name', 'Home')
            away_name = away.get('name', 'Away')
            
            fixture_ids.append(fix_id)
            
            print(f"  {idx}. [{fix_id}] {home_name} vs {away_name} ({state})")
    
    all_fixtures_by_gameweek[gameweek_num] = fixture_ids
    print()

# Resultado final
print("=" * 80)
print("RESULTADO FINAL")
print("=" * 80 + "\n")

print("FIXTURES_BY_GAMEWEEK = {")
for gw, fixtures in sorted(all_fixtures_by_gameweek.items()):
    print(f"    {gw}: {fixtures},")
print("}\n")

print(f"Total jornadas: {len(all_fixtures_by_gameweek)}")
for gw, fixtures in sorted(all_fixtures_by_gameweek.items()):
    print(f"Jornada {gw}: {len(fixtures)} partidos")

print("\n" + "=" * 80)
