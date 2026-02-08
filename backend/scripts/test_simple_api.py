"""
Script simplificado para obtener partidos recientes - Free Plan compatible
"""

import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')

print("\n🔍 PROBANDO DIFERENTES ENDPOINTS\n")
print("="*80)

# Intentar obtener partidos directamente
print("\n1️⃣ Intentando obtener fixtures recientes...")

url = "https://api.sportmonks.com/v3/football/fixtures"
params = {
    "api_token": API_TOKEN,
   "include": "lineups.player;lineups.details;scores;participants"
}

try:
    response = requests.get(url, params=params, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        fixtures = data.get('data', [])
        
        print(f"\n✅ {len(fixtures)} partidos obtenidos")
        
        # Buscar un partido finalizado de Scottish Premiership
        for fixture in fixtures:
            participants = fixture.get('participants', [])
            
            # Buscar partidos escoceses
            home = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
            home_name = home.get('name', '')
            
            if any(team in home_name for team in ['Celtic', 'Rangers', 'Aberdeen', 'Hearts', 'Kilmarnock']):
                print(f"\n🏴 Partido escocés encontrado!")
                print(f"   ID: {fixture['id']}")
                print(json.dumps(fixture, indent=2))
                break
    else:
        print(f"\n❌ Error {response.status_code}: {response.text[:200]}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
