"""
Script para exportar todos los jugadores de Sportmonks a CSV
Para poder contrastar con el CSV de FIFA
"""

import requests
import csv
import time
from datetime import datetime

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
SEASON_ID = 21787

# Mapeo de position_id a nombre legible
POSITION_NAMES = {
    24: 'GK',
    25: 'DEF', 26: 'DEF', 27: 'DEF',  # Defender types
    28: 'MID', 29: 'MID', 30: 'MID',  # Midfielder types
    31: 'FWD', 32: 'FWD', 33: 'FWD',  # Forward types
}

def obtener_position_name(position_id):
    """Convierte position_id a nombre"""
    return POSITION_NAMES.get(position_id, 'MID')


def exportar_sportmonks_a_csv():
    """Exporta datos de Sportmonks a CSV"""
    
    print("="*60)
    print("📤 EXPORTAR SPORTMONKS A CSV")
    print("="*60 + "\n")
    
    # 1. Obtener player_ids
    print("📋 Paso 1: Obteniendo equipos y player_ids...")
    url = f"https://api.sportmonks.com/v3/football/teams/seasons/{SEASON_ID}"
    params = {
        "api_token": API_TOKEN,
        "include": "players"
    }
    
    response = requests.get(url, params=params, timeout=30)
    teams_data = response.json().get('data', [])
    
    print(f"✅ {len(teams_data)} equipos encontrados\n")
    
    # Recopilar player_ids y team_mapping
    all_player_ids = []
    team_mapping = {}
    position_mapping = {}
    
    for team in teams_data:
        team_name = team.get('name')
        players = team.get('players', [])
        
        print(f"   {team_name}: {len(players)} jugadores")
        
        for player_data in players:
            player_id = player_data.get('player_id')
            position_id = player_data.get('position_id')
            
            if player_id:
                all_player_ids.append(player_id)
                team_mapping[player_id] = team_name
                position_mapping[player_id] = position_id
    
    print(f"\n✅ Total player_ids: {len(all_player_ids)}\n")
    
    # 2. Obtener datos completos
    print("📡 Paso 2: Obteniendo datos completos de jugadores...")
    print(f"⏱️  Esto tomará aproximadamente {len(all_player_ids) * 0.3 / 60:.1f} minutos\n")
    
    jugadores_exportar = []
    errores = 0
    
    for i, player_id in enumerate(all_player_ids, 1):
        try:
            url_player = f"https://api.sportmonks.com/v3/football/players/{player_id}"
            params_player = {"api_token": API_TOKEN}
            
            response = requests.get(url_player, params=params_player, timeout=10)
            
            if response.status_code == 200:
                player_data = response.json().get('data', {})
                
                # Extraer datos
                nombre = player_data.get('display_name') or player_data.get('common_name') or player_data.get('name', 'Unknown')
                team_name = team_mapping.get(player_id, 'Unknown')
                position_id = position_mapping.get(player_id, 28)
                position_name = obtener_position_name(position_id)
                
                # Edad
                dob = player_data.get('date_of_birth')
                edad = ''
                if dob:
                    try:
                        birth_year = int(dob.split('-')[0])
                        edad = datetime.now().year - birth_year
                    except:
                        pass
                
                # Nacionalidad
                nationality_data = player_data.get('nationality', {})
                nacionalidad = nationality_data.get('name', '') if isinstance(nationality_data, dict) else ''
                
                jugadores_exportar.append({
                    'id': player_id,
                    'name': nombre,
                    'position': position_name,
                    'team': team_name,
                    'age': edad,
                    'nationality': nacionalidad
                })
                
                if i % 50 == 0:
                    print(f"   Procesados: {i}/{len(all_player_ids)}")
            else:
                errores += 1
            
            # Respetar rate limit
            time.sleep(0.3)
            
        except Exception as e:
            errores += 1
            if errores <= 5:
                print(f"   ❌ Error con player_id {player_id}: {e}")
    
    print(f"\n✅ Datos obtenidos: {len(jugadores_exportar)} jugadores")
    print(f"❌ Errores: {errores}\n")
    
    # 3. Guardar a CSV
    print("💾 Paso 3: Guardando a CSV...")
    
    csv_filename = 'sportmonks_players.csv'
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'name', 'position', 'team', 'age', 'nationality']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for jugador in jugadores_exportar:
            writer.writerow(jugador)
    
    print(f"✅ CSV guardado: {csv_filename}")
    
    # 4. Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    print(f"Total jugadores: {len(jugadores_exportar)}")
    print(f"Errores: {errores}")
    print(f"Archivo: {csv_filename}")
    
    # Distribución por posición
    from collections import Counter
    pos_count = Counter([j['position'] for j in jugadores_exportar])
    print(f"\n📋 Distribución por posición:")
    for pos, count in pos_count.most_common():
        porcentaje = (count / len(jugadores_exportar)) * 100
        print(f"   {pos}: {count} ({porcentaje:.1f}%)")
    
    # Distribución por equipo
    team_count = Counter([j['team'] for j in jugadores_exportar])
    print(f"\n🏆 Distribución por equipo:")
    for team, count in team_count.most_common():
        print(f"   {team}: {count}")
    
    print("\n" + "="*60)
    print("✅ EXPORTACIÓN COMPLETADA")
    print("="*60)


if __name__ == "__main__":
    exportar_sportmonks_a_csv()
