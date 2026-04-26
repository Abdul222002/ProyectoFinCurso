"""
MIGRACIÓN JORNADA 1 - Scottish Premiership
Obtener todos los partidos de la jornada 1 y calcular puntos fantasy
"""

import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')

# IDs conocidos
LEAGUE_ID = 501  # Scottish Premiership
SEASON_ID = 23614  # Temporada 2024/25

print("\n" + "="*100)
print("📅 MIGRACIÓN JORNADA 1 - Scottish Premiership 2024/25")
print("="*100 + "\n")

# ========================================
# PASO 1: Obtener fixtures de la jornada 1
# ========================================

url = "https://api.sportmonks.com/v3/football/fixtures"
params = {
    "api_token": API_TOKEN,
    "filters": f"fixtureLeagues:{LEAGUE_ID};fixtureSeasons:{SEASON_ID}",
    "include": "scores;participants"
}

print("🔍 Obteniendo fixtures de la temporada...")
response = requests.get(url, params=params, timeout=30)

if response.status_code != 200:
    print(f"❌ Error {response.status_code}: {response.text[:500]}")
    exit(1)

data = response.json()
all_fixtures = data.get('data', [])

print(f"✅ Total fixtures encontrados: {len(all_fixtures)}\n")

# Filtrar solo jornada 1
jornada_1 = [f for f in all_fixtures if f.get('round_id') == 274954]  # Round 1

if not jornada_1:
    # Intentar encontrar el round correcto
    rounds = {}
    for f in all_fixtures:
        round_id = f.get('round_id')
        round_name = f.get('round', {}).get('name', 'Unknown')
        if round_id not in rounds:
            rounds[round_id] = round_name
    
    print("⚠️  No se encontró la jornada 1 con round_id 274954")
    print("\nRounds disponibles (primeros 10):")
    for i, (rid, rname) in enumerate(list(rounds.items())[:10]):
        print(f"  - Round ID {rid}: {rname}")
    
    # Usar el primer round que encuentre con nombre "1" o similar
    for f in all_fixtures:
        if 'round' in f and str(f.get('round', {}).get('name', '')).strip() in ['1', 'Round 1', 'Matchweek 1']:
            jornada_1.append(f)

if not jornada_1:
    print("\n❌ No se pudo encontrar la jornada 1")
    print("\nMostrando primeros 3 fixtures para debug:")
    for f in all_fixtures[:3]:
        print(f"\n  Fixture ID: {f.get('id')}")
        print(f"  Round: {f.get('round', {}).get('name', 'N/A')}")
        print(f"  Round ID: {f.get('round_id')}")
        print(f"  State: {f.get('state', {}).get('state', 'N/A')}")
        participants = f.get('participants', [])
        if len(participants) >= 2:
            print(f"  Match: {participants[0].get('name')} vs {participants[1].get('name')}")
    exit(1)

print(f"✅ Jornada 1 encontrada: {len(jornada_1)} partidos\n")

# ========================================
# PASO 2: Mostrar partidos de la jornada 1
# ========================================

print("📊 PARTIDOS DE LA JORNADA 1:")
print("-" * 100)

for idx, fixture in enumerate(jornada_1, 1):
    fixture_id = fixture.get('id')
    state = fixture.get('state', {}).get('state', 'N/A')
    
    # Obtener equipos y marcador
    participants = fixture.get('participants', [])
    scores = fixture.get('scores', [])
    
    if len(participants) >= 2:
        home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
        away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
        
        home_score = next((s['score']['goals'] for s in scores 
                          if s['description'] == 'CURRENT' and s['participant_id'] == home_team.get('id')), '-')
        away_score = next((s['score']['goals'] for s in scores 
                          if s['description'] == 'CURRENT' and s['participant_id'] == away_team.get('id')), '-')
        
        print(f"{idx}. [{fixture_id}] {home_team.get('name', 'Home'):<20} {home_score}-{away_score} {away_team.get('name', 'Away'):<20} ({state})")

print("\n" + "="*100)

# ========================================
# PASO 3: Intentar procesar el primer partido
# ========================================

if jornada_1 and len(jornada_1) > 0:
    primer_partido = jornada_1[0]
    fixture_id = primer_partido.get('id')
    
    print(f"\n🔬 PROCESANDO PRIMER PARTIDO (ID: {fixture_id})...\n")
    
    # Obtener detalles completos con lineups
    url_detail = f"https://api.sportmonks.com/v3/football/fixtures/{fixture_id}"
    params_detail = {
        "api_token": API_TOKEN,
        "include": "lineups.details.type;participants;scores"
    }
    
    response_detail = requests.get(url_detail, params=params_detail, timeout=30)
    
    if response_detail.status_code == 200:
        detail_data = response_detail.json().get('data', {})
        lineups = detail_data.get('lineups', [])
        
        print(f"✅ Lineups encontrados: {len(lineups)} jugadores\n")
        
        if len(lineups) > 0:
            print("📋 PRIMEROS 5 JUGADORES CON STATS:")
            print("-" * 100)
            
            for player_entry in lineups[:5]:
                player_name = player_entry.get('player_name', 'N/A')
                details = player_entry.get('details', [])
                
                print(f"\n  {player_name}:")
                
                # Mostrar stats básicas
                stats_importantes = ['MINUTES_PLAYED', 'GOALS', 'ASSISTS', 'RATING', 'YELLOWCARDS', 'REDCARDS']
                for stat_name in stats_importantes:
                    for stat in details:
                        if stat.get('type', {}).get('developer_name') == stat_name:
                            valor = stat.get('data', {}).get('value')
                            if valor is not None and valor != 0:
                                print(f"    - {stat_name}: {valor}")
                            break
            
            print("\n" + "="*100)
            print("✅ DATOS DISPONIBLES PARA PROCESAMIENTO")
            print("="*100)
        else:
            print("⚠️  No hay lineups disponibles (partido no finalizado o sin datos)")
    else:
        print(f"❌ Error al obtener detalles: {response_detail.status_code}")

print("\n📝 SIGUIENTE PASO: Implementar script completo de migración con cálculo de puntos\n")
