"""
Script para descubrir TODOS los developer_names disponibles en la API
y mapearlos a los campos de PlayerMatchStats
"""

import os
import requests
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')
FIXTURE_ID = 19428171  # Aberdeen vs Livingston

url = f"https://api.sportmonks.com/v3/football/fixtures/{FIXTURE_ID}"
params = {
    "api_token": API_TOKEN,
    "include": "lineups.details.type"
}

print(f"\n{'='*80}")
print(f"🔍 DESCUBRIENDO TODOS LOS DEVELOPER_NAMES DISPONIBLES")
print(f"{'='*80}\n")

response = requests.get(url, params=params, timeout=30)

if response.status_code == 200:
    data = response.json().get('data', {})
    lineups = data.get('lineups', [])
    
    # Recopilar TODOS los developer_names únicos
    all_stats = defaultdict(set)  # {developer_name: {valores posibles}}
    
    for player in lineups:
        details = player.get('details', [])
        
        for stat in details:
            type_info = stat.get('type', {})
            developer_name = type_info.get('developer_name', '')
            data_wrapper = stat.get('data', {})
            valor = data_wrapper.get('value')
            
            if developer_name and valor is not None:
                all_stats[developer_name].add(str(valor)[:50])  # Primeros 50 chars
    
    # Ordenar alfabéticamente
    sorted_stats = sorted(all_stats.items())
    
    print(f"✅ {len(sorted_stats)} developer_names encontrados:\n")
    print(f"{'DEVELOPER_NAME':<40} | EJEMPLOS DE VALORES")
    print("-" * 80)
    
    for stat_name, valores in sorted_stats:
        ejemplos = ', '.join(list(valores)[:3])  # Primeros 3 ejemplos
        print(f"{stat_name:<40} | {ejemplos}")
    
    print("\n" + "="*80)
    print("\n📋 MAPEO SUGERIDO A PlayerMatchStats:\n")
    
    # Crear mapeo
    mapeo = {
        # Básicos
        "MINUTES_PLAYED": "minutes_played",
        "RATING": "rating",
        
        # Ataque
        "GOALS": "goals",
        "ASSISTS": "assists",
        "SHOTS_ON_TARGET": "shots_on_target",
        
        # Defensa
        "GOALS_CONCEDED": "goals_conceded",
        "SAVES": "saves",
        "PENALTY_SAVE": "penalties_saved",
        
        # Tarjetas
        "YELLOWCARDS": "yellow_cards",
        "REDCARDS": "red_cards",
        "OWNGOALS": "own_goals",
        
        # Penaltis
        "PENALTY_MISS": "penalties_missed",
        "PENALTY_WON": "penalties_won",
        
        # Stats avanzadas
        "DRIBBLES_SUCCESS": "successful_dribbles",
        "BALL_RECOVERIES": "ball_recoveries",
        "CLEARANCES_EFFECTIVE": "effective_clearances",
        "CROSSES_ACCURATE": "accurate_crosses",
        "DISPOSSESSED": "dispossessed",
    }
    
    print("```python")
    print("# Mapeo completo de API → BD")
    print("STAT_MAPPING = {")
    for api_name, db_field in mapeo.items():
        disponible = "✅" if api_name in all_stats else "❌"
        print(f"    '{api_name}': '{db_field}',  # {disponible}")
    print("}")
    print("```")
    
    print("\n" + "="*80)
    
else:
    print(f"❌ Error {response.status_code}: {response.text[:500]}")
