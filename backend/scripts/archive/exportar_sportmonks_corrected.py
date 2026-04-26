"""
Script para crear un mapeo correcto de position_ids
Basado en la documentación de Sportmonks y los IDs observados
"""

import requests
import csv
import time
from collections import Counter

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
SEASON_ID = 21787

# Mapeo correcto basado en documentación Sportmonks
# https://docs.sportmonks.com/football/tutorials-and-guides/filters/positions
POSITION_MAP_CORRECTO = {
    # Porteros
    24: 'GK',
    
    # Defensas
    25: 'DEF',  # Defender (genérico)
    26: 'DEF',  # Centre-Back
    27: 'DEF',  # Left-Back / Right-Back
    28: 'DEF',  # Wing-Back
    
    # Centrocampistas
    29: 'MID',  # Midfielder (genérico)
    30: 'MID',  # Defensive Midfielder
    31: 'MID',  # Central Midfielder
    32: 'MID',  # Attacking Midfielder
    33: 'MID',  # Left/Right Midfielder
    34: 'MID',  # Winger (algunos pueden ser FWD)
    
    # Delanteros
    35: 'FWD',  # Attacker (genérico)
    36: 'FWD',  # Forward
    37: 'FWD',  # Striker
    38: 'FWD',  # Centre-Forward
}

def crear_csv_con_mapeo_correcto():
    """Crea CSV con el mapeo correcto de posiciones"""
    
    print("="*60)
    print("📤 EXPORTAR SPORTMONKS CON MAPEO CORRECTO")
    print("="*60 + "\n")
    
    # 1. Obtener player_ids y position_ids del squad
    print("📋 Obteniendo datos del squad...")
    url = f"https://api.sportmonks.com/v3/football/teams/seasons/{SEASON_ID}"
    params = {"api_token": API_TOKEN, "include": "players"}
    
    response = requests.get(url, params=params, timeout=30)
    teams_data = response.json().get('data', [])
    
    print(f"✅ {len(teams_data)} equipos\n")
    
    player_ids = []
    position_mapping = {}
    team_mapping = {}
    
    # Contador de position_ids para ver la distribución
    position_id_counter = Counter()
    
    for team in teams_data:
        team_name = team.get('name')
        for player_data in team.get('players', []):
            player_id = player_data.get('player_id')
            position_id = player_data.get('position_id')
            
            if player_id:
                player_ids.append(player_id)
                position_mapping[player_id] = position_id
                team_mapping[player_id] = team_name
                position_id_counter[position_id] += 1
    
    print(f"📊 Position_IDs encontrados:")
    for pos_id, count in sorted(position_id_counter.items()):
        pos_name = POSITION_MAP_CORRECTO.get(pos_id, f'UNKNOWN_{pos_id}')
        print(f"   {pos_id}: {count} jugadores → {pos_name}")
    
    print(f"\n⚠️  Si ves 'UNKNOWN' necesitamos ajustar el mapeo\n")
    
    # 2. Obtener datos completos
    print(f"📡 Obteniendo datos de {len(player_ids)} jugadores...")
    print(f"⏱️  Esto tomará ~{len(player_ids) * 0.3 / 60:.1f} minutos\n")
    
    jugadores = []
    errores = 0
    
    for i, player_id in enumerate(player_ids, 1):
        try:
            url_player = f"https://api.sportmonks.com/v3/football/players/{player_id}"
            response = requests.get(url_player, params={"api_token": API_TOKEN}, timeout=10)
            
            if response.status_code == 200:
                player_data = response.json().get('data', {})
                
                nombre = player_data.get('display_name') or player_data.get('common_name') or player_data.get('name', 'Unknown')
                position_id = position_mapping.get(player_id)
                position_name = POSITION_MAP_CORRECTO.get(position_id, 'MID')
                team_name = team_mapping.get(player_id, 'Unknown')
                
                # Edad
                dob = player_data.get('date_of_birth')
                edad = ''
                if dob:
                    try:
                        from datetime import datetime
                        birth_year = int(dob.split('-')[0])
                        edad = datetime.now().year - birth_year
                    except:
                        pass
                
                # Nacionalidad
                nationality_data = player_data.get('nationality', {})
                nacionalidad = nationality_data.get('name', '') if isinstance(nationality_data, dict) else ''
                
                jugadores.append({
                    'sportmonks_id': player_id,
                    'name': nombre,
                    'position': position_name,
                    'position_id': position_id,
                    'team': team_name,
                    'age': edad,
                    'nationality': nacionalidad
                })
                
                if i % 50 == 0:
                    print(f"   Procesados: {i}/{len(player_ids)}")
                
            else:
                errores += 1
            
            time.sleep(0.3)
            
        except Exception as e:
            errores += 1
    
    print(f"\n✅ Procesados: {len(jugadores)} jugadores")
    print(f"❌ Errores: {errores}\n")
    
    # 3. Guardar CSV
    csv_filename = 'sportmonks_players_CORRECTED.csv'
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['sportmonks_id', 'name', 'position', 'position_id', 'team', 'age', 'nationality']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for jugador in jugadores:
            writer.writerow(jugador)
    
    print(f"✅ CSV guardado: {csv_filename}\n")
    
    # 4. Estadísticas
    pos_counter = Counter([j['position'] for j in jugadores])
    team_counter = Counter([j['team'] for j in jugadores])
    
    print("="*60)
    print("📊 RESUMEN")
    print("="*60)
    print(f"Total: {len(jugadores)} jugadores")
    print(f"Archivo: {csv_filename}\n")
    
    print("📋 Por posición:")
    for pos, count in pos_counter.most_common():
        porcentaje = (count / len(jugadores)) * 100
        print(f"   {pos}: {count} ({porcentaje:.1f}%)")
    
    print(f"\n🏆 Por equipo:")
    for team, count in team_counter.most_common():
        print(f"   {team}: {count}")
    
    print("\n" + "="*60)
    print("✅ EXPORTACIÓN COMPLETADA")
    print("="*60)


if __name__ == "__main__":
    crear_csv_con_mapeo_correcto()
