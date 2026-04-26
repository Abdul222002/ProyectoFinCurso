"""
Script para buscar el ID correcto de la temporada Scottish Premiership
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')
LEAGUE_ID = 501  # Scottish Premiership

print("\n🔍 BUSCANDO TEMPORADA CORRECTA - SCOTTISH PREMIERSHIP\n")
print("="*80)

url = "https://api.sportmonks.com/v3/football/seasons"
params = {
    "api_token": API_TOKEN,
    "filters": f"leagueId:{LEAGUE_ID}"
}

try:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    seasons = data.get('data', [])
    
    print(f"\n✅ {len(seasons)} temporadas encontradas:\n")
    
    for season in seasons[-5:]:  # Últimas 5 temporadas
        print(f"  ID: {season['id']:6} | {season['name']:20} | {season.get('starting_at')} - {season.get('ending_at')}")
    
    # Buscar temporada actual (2025/26)
    current = [s for s in seasons if '2025' in s['name'] or '2026' in s['name']]
    
    if current:
        print(f"\n🎯 TEMPORADA 2025/26 ENCONTRADA:")
        print(f"   ID: {current[0]['id']}")
        print(f"   Nombre: {current[0]['name']}")
    else:
        print("\n⚠️ No se encontró temporada 2025/26 explícitamente")
        print(f"   Usando la última disponible: ID {seasons[-1]['id']}")

except Exception as e:
    print(f"❌ Error: {e}")
