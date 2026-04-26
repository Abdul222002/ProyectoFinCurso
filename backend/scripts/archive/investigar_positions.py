"""
Script para investigar los position_ids reales de Sportmonks
y corregir el CSV con las posiciones correctas
"""

import requests
import csv
import time

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
SEASON_ID = 21787

def investigar_positions():
    """Investiga los position_ids y nombres reales"""
    
    print("="*60)
    print("🔍 INVESTIGANDO POSITION_IDs REALES")
    print("="*60 + "\n")
    
    # 1. Obtener player_ids
    url = f"https://api.sportmonks.com/v3/football/teams/seasons/{SEASON_ID}"
    params = {"api_token": API_TOKEN, "include": "players"}
    
    response = requests.get(url, params=params, timeout=30)
    teams_data = response.json().get('data', [])
    
    player_ids = []
    position_ids_from_squad = {}
    
    for team in teams_data:
        for player_data in team.get('players', []):
            player_id = player_data.get('player_id')
            position_id = player_data.get('position_id')
            
            if player_id:
                player_ids.append(player_id)
                position_ids_from_squad[player_id] = position_id
    
    print(f"Total player_ids: {len(player_ids)}")
    
    # 2. Investigar los primeros 20 jugadores
    print("\n📊 Investigando position_ids en jugadores individuales...\n")
    
    position_mapping = {}
    
    for i, player_id in enumerate(player_ids[:20], 1):
        try:
            url_player = f"https://api.sportmonks.com/v3/football/players/{player_id}"
            response = requests.get(url_player, params={"api_token": API_TOKEN}, timeout=10)
            
            if response.status_code == 200:
                player_data = response.json().get('data', {})
                nombre = player_data.get('display_name', 'Unknown')
                
                # Posición desde squad
                pos_id_squad = position_ids_from_squad.get(player_id)
                
                # Posición desde datos del jugador
                position_data = player_data.get('position', {})
                if isinstance(position_data, dict):
                    pos_id_player = position_data.get('id')
                    pos_name_player = position_data.get('name')
                else:
                    pos_id_player = None
                    pos_name_player = None
                
                print(f"{i}. {nombre}")
                print(f"   Squad position_id: {pos_id_squad}")
                print(f"   Player position_id: {pos_id_player}")
                print(f"   Player position_name: {pos_name_player}")
                print()
                
                # Guardar mapeo
                if pos_name_player and pos_id_player:
                    position_mapping[pos_id_player] = pos_name_player
                
            time.sleep(0.3)
            
        except Exception as e:
            print(f"Error: {e}")
    
    # 3. Mostrar mapeo encontrado
    print("\n" + "="*60)
    print("🗺️  MAPEO DE POSITION_IDs ENCONTRADO:")
    print("="*60)
    for pos_id, pos_name in sorted(position_mapping.items()):
        print(f"   {pos_id}: {pos_name}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    investigar_positions()
