"""
OBTENER FIXTURES - Método alternativo para plan gratuito
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')

print("\n" + "="*80)
print("🔍 BUSCANDO FIXTURES DE LA SCOTTISH PREMIERSHIP")
print("="*80 + "\n")

# Método 1: Buscar partido conocido (Aberdeen vs Livingston)
FIXTURE_ID_CONOCIDO = 19428171

print(f"✅ Usando fixture conocido: {FIXTURE_ID_CONOCIDO}")

url = f"https://api.sportmonks.com/v3/football/fixtures/{FIXTURE_ID_CONOCIDO}"
params = {
    "api_token": API_TOKEN,
    "include": "round"
}

response = requests.get(url, params=params, timeout=30)

if response.status_code == 200:
    data = response.json().get('data', {})
    round_info = data.get('round', {})
    round_id = round_info.get('id')
    round_name = round_info.get('name')
    season_id = data.get('season_id')
    league_id = data.get('league_id')
    
    print(f"📊 Información del partido:")
    print(f"   - Liga ID: {league_id}")
    print(f"   - Temporada ID: {season_id}")
    print(f"   - Round: {round_name} (ID: {round_id})\n")
    
    # Ahora obtener TODOS los fixtures de ese round
    print(f"🔄 Obteniendo TODOS los partidos del {round_name}...\n")
    
    url_round = f"https://api.sportmonks.com/v3/football/fixtures"
    params_round = {
        "api_token": API_TOKEN,
        "filters": f"fixtureRounds:{round_id}",
        "include": "participants;scores"
    }
    
    response_round = requests.get(url_round, params=params_round, timeout=30)
    
    if response_round.status_code == 200:
        fixtures_data = response_round.json().get('data', [])
        
        print(f"✅ {len(fixtures_data)} partidos encontrados en {round_name}\n")
        print("="*80)
        print(f"📋 PARTIDOS - {round_name.upper()}")
        print("="*80 + "\n")
        
        for idx, fixture in enumerate(fixtures_data, 1):
            fix_id = fixture.get('id')
            state = fixture.get('state', {}).get('state', 'N/A')
            participants = fixture.get('participants', [])
            scores = fixture.get('scores', [])
            
            if len(participants) >= 2:
                home = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
                away = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
                
                home_score = next((s['score']['goals'] for s in scores 
                                  if s['description'] == 'CURRENT' and s['participant_id'] == home.get('id')), '-')
                away_score = next((s['score']['goals'] for s in scores 
                                  if s['description'] == 'CURRENT' and s['participant_id'] == away.get('id')), '-')
                
                estado_emoji = "✅" if state == "FT" else "⏳" if state == "NS" else "⚽"
                
                print(f"{idx}. {estado_emoji} [{fix_id}] {home.get('name', 'Home'):<22} {home_score}-{away_score} {away.get('name', 'Away'):<22} ({state})")
        
        print("\n" + "="*80)
        print(f"✅ JORNADA ENCONTRADA: {round_name}")
        print(f"   Total partidos: {len(fixtures_data)}")
        
        finalizados = [f for f in fixtures_data if f.get('state', {}).get('state') == 'FT']
        print(f"   Finalizados: {len(finalizados)}")
        print(f"   Pendientes: {len(fixtures_data) - len(finalizados)}")
        print("="*80 + "\n")
        
        if finalizados:
            print("📝 IDs de partidos finalizados para procesar:")
            for f in finalizados:
                print(f"   - {f.get('id')}")
        
    else:
        print(f"❌ Error obteniendo fixtures del round: {response_round.status_code}")
        print(response_round.text[:300])
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text[:300])

print("\n" + "="*80 + "\n")
