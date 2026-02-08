"""
DEBUG: Ver qué fixtures se encuentran en las fechas de jornada 1
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')

START_DATE = "2025-08-02"
END_DATE = "2025-08-03"

url = f"https://api.sportmonks.com/v3/football/fixtures/between/{START_DATE}/{END_DATE}"
params = {
    "api_token": API_TOKEN,
    "include": "participants"
}

print(f"\n🔍 Buscando fixtures entre {START_DATE} y {END_DATE}...\n")

response = requests.get(url, params=params, timeout=30)

if response.status_code == 200:
    data = response.json().get('data', [])
    
    print(f"✅ Total fixtures encontrados: {len(data)}\n")
    
    # Filtrar Scottish Premiership
    spl = [f for f in data if f.get('league_id') == 501]
    
    print(f"📊 Scottish Premiership (501): {len(spl)} fixtures\n")
    
    if spl:
        print("FIXTURES ENCONTRADOS:")
        print("-" * 120)
        for idx, f in enumerate(spl, 1):
            fix_id = f.get('id')
            state = f.get('state', {}).get('state', 'N/A')
            league_id = f.get('league_id')
            participants = f.get('participants', [])
            
            home = next((p.get('name') for p in participants if p.get('meta', {}).get('location') == 'home'), 'N/A')
            away = next((p.get('name') for p in participants if p.get('meta', {}).get('location') == 'away'), 'N/A')
            
            print(f"{idx}. [{fix_id}] {home} vs {away} - Estado: {state}, League: {league_id}")
    else:
        print("⚠️  No se encontraron fixtures de Scottish Premiership")
        print("\nTodos los fixtures encontrados:")
        for idx, f in enumerate(data[:10], 1):
            print(f"{idx}. ID: {f.get('id')}, League: {f.get('league_id')}, State: {f.get('state', {}).get('state')}")
else:
    print(f"❌ Error {response.status_code}: {response.text[:500]}")
