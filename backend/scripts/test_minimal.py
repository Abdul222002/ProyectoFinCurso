"""
Probando con EXACTAMENTE el mismo include que usó el usuario
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')
MATCH_ID = 18535655

base_url = f"https://api.sportmonks.com/v3/football/fixtures/{MATCH_ID}"

# EXACTAMENTE como en el script del usuario
params = {
    "api_token": API_TOKEN,
    "include": "lineups.player.statistics"  # Sin scores ni participants
}

print(f"\n📡 Probando include: {params['include']}\n")

response = requests.get(base_url, params=params, timeout=30)

print(f"Status Code: {response.status_code}\n")

if response.status_code == 200:
    data = response.json().get('data', {})
    lineups = data.get('lineups', [])
    
    print(f"✅ Lineups obtenidos: {len(lineups)}")
    
    if lineups:
        primer_jugador = lineups[0]
        print("\n📊 Primer jugador:")
        print(f"   Nombre: {primer_jugador.get('player_name')}")
        print(f"   Statistics: {primer_jugador.get('statistics', [])[:3]}")  # Primeras 3 stats
else:
    print(f"❌ Error: {response.text}")
