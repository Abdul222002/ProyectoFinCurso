"""
DEBUG SIMPLIFICADO: Ver stats crudos de jugadores problemáticos
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')

# Función para ver stats raw
def ver_stats_raw(fixture_id, nombre):
    url = f"https://api.sportmonks.com/v3/football/fixtures/{fixture_id}"
    params = {
        "api_token": API_TOKEN,
        "include": "lineups.details.type"
    }
    
    response = requests.get(url, params=params, timeout=30)
    data = response.json().get('data', {})
    lineups = data.get('lineups', [])
    
    for player in lineups:
        if nombre.lower() in player.get('player_name', '').lower():
            name = player.get('player_name')
            details = player.get('details', [])
            
            print(f"\n{'='*80}")
            print(f"👤 {name}")
            print(f"{'='*80}\n")
            
            # Stats importantes
            stats_importantes = [
                'MINUTES_PLAYED', 'GOALS', 'ASSISTS', 'RATING',
                'YELLOWCARDS', 'REDCARDS',
                'SHOTS_ON_TARGET', 'SUCCESSFUL_DRIBBLES', 'ACCURATE_CROSSES',
                'BALL_RECOVERY', 'CLEARANCES',
                'TACKLES', 'INTERCEPTIONS', 'DUELS_WON', 'ACCURATE_PASSES',
                'FOULS', 'DISPOSSESSED', 'POSSESSION_LOST', 'TURN_OVER'
            ]
            
            print(f"{'STAT':<25} | VALOR")
            print("-" * 80)
            
            for stat_name in stats_importantes:
                for stat in details:
                    if stat.get('type', {}).get('developer_name') == stat_name:
                        valor = stat.get('data', {}).get('value')
                        if valor is not None and valor != 0:
                            print(f"{stat_name:<25} | {valor}")
                        break
            
            return

# Casos problemáticos
print("\n" + "="*80)
print("🔍 STATS RAW DE CASOS PROBLEMÁTICOS")
print("="*80)

print("\n1️⃣  PANUTCHE CAMARA (19 pts con 1 asistencia):")
ver_stats_raw(19428041, "Panutche Camara")

print("\n2️⃣  KIERON BOWIE (14 pts con 2 goles):")
ver_stats_raw(19428042, "Kieron Bowie")

print("\n3️⃣  GEORGE STANGER (4 pts con expulsión):")
ver_stats_raw(19428039, "George Stanger")

print("\n" + "="*80 + "\n")
