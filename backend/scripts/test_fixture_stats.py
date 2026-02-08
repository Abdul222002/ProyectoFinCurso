"""
Obtener un fixture específico conocido y extraer stats
"""

import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')

# Vamos a probar con un ID de fixture que sabemos existe (del 2/8/25)
# Kilmarnock vs Livingston fue el primer partido
# Intentemos buscar por equipo

print("\n🔍 BUSCANDO PARTIDOS DE EQUIPOS ESCOCESES\n")
print("="*80)

# IDs de equipos escoceses conocidos
CELTIC_ID = 412
RANGERS_ID = 413

url = f"https://api.sportmonks.com/v3/football/teams/{CELTIC_ID}"
params = {
    "api_token": API_TOKEN,
    "include": "latest"  # Últimos partidos
}

try:
    response = requests.get(url, params=params, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Datos del Celtic obtenidos")
        print(json.dumps(data, indent=2)[:2000])
    else:
        print(f"\n❌ Error {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"\n❌ Error: {e}")

# Plan B: Usar un fixture ID conocido directamente
print("\n\n" + "="*80)
print("📋 PLAN B: Probando con fixture específico")
print("="*80)

# Fixture de ejemplo (puedes cambiarlo)
FIXTURE_ID = 19381095  # Un ID de ejemplo

url_fixture = f"https://api.sportmonks.com/v3/football/fixtures/{FIXTURE_ID}"
params_fixture = {
    "api_token": API_TOKEN,
    "include": "lineups.player;lineups.details;scores;participants"
}

try:
    response2 = requests.get(url_fixture, params=params_fixture, timeout=30)
    
    if response2.status_code == 200:
        fixture_data = response2.json().get('data', {})
        
        print(f"\n✅ Fixture obtenido!")
        
        # Info del partido
        participants = fixture_data.get('participants', [])
        if len(participants) >= 2:
            print(f"\n🏟️  {participants[0].get('name')} vs {participants[1].get('name')}")
        
        # Lineups
        lineups = fixture_data.get('lineups', [])
        print(f"\n👥 {len(lineups)} jugadores en el partido")
        
        if lineups:
            print("\n📊 Primer jugador de ejemplo:")
            print("="*70)
            primer_jugador = lineups[0]
            
            player_info = primer_jugador.get('player', {})
            details = primer_jugador.get('details', [])
            
            print(f"  Nombre: {player_info.get('display_name')}")
            print(f"  Posición ID: {primer_jugador.get('position_id')}")
            print(f"\n  Estadísticas disponibles:")
            
            for detail in details:
                type_info = detail.get('type', {})
                value_info = detail.get('value', {})
                print(f"    - {type_info.get('name', 'N/A'):30} = {value_info.get('total', 'N/A')}")
                
        else:
            print("\n⚠️ No hay lineups disponibles para este fixture")
            print("\nPosibles razones:")
            print("  1. El partido aún no se ha jugado")
            print("  2. Los datos detallados no están en el plan free")
            print("  3. El ID del fixture no es correcto")
    else:
        print(f"\n❌ Error {response2.status_code}")
        print(response2.text[:500])

except Exception as e:
    print(f"\n❌ Error: {e}")
