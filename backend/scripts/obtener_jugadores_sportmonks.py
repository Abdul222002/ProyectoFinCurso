"""
Script mejorado para obtener jugadores de Sportmonks
Usa múltiples estrategias para trabajar con el plan gratuito
"""

import requests
import json
import time

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
SEASON_ID = 21787

def get_teams():
    """Obtiene los equipos de la temporada"""
    url = f"https://api.sportmonks.com/v3/football/teams/seasons/{SEASON_ID}"
    params = {"api_token": API_TOKEN}
    
    response = requests.get(url, params=params, timeout=15)
    if response.status_code == 200:
        return response.json().get('data', [])
    return []


def get_team_players_method1(team_id):
    """Método 1: Endpoint directo de jugadores por equipo"""
    url = f"https://api.sportmonks.com/v3/football/players/teams/{team_id}"
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                return data['data']
    except:
        pass
    return None


def get_team_players_method2(team_id, season_id):
    """Método 2: Squad por temporada y equipo"""
    url = f"https://api.sportmonks.com/v3/football/squads/seasons/{season_id}/teams/{team_id}"
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                squad_data = data['data'][0] if isinstance(data['data'], list) else data['data']
                return squad_data.get('players', [])
    except:
        pass
    return None


def get_matches_with_lineups():
    """Método 3: Obtener jugadores desde las alineaciones de partidos"""
    url = f"https://api.sportmonks.com/v3/football/fixtures/seasons/{SEASON_ID}"
    params = {
        "api_token": API_TOKEN,
        "include": "lineups"
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
    except:
        pass
    return []


def main():
    print("="*60)
    print("🔍 OBTENIENDO JUGADORES DE SPORTMONKS")
    print("="*60 + "\n")
    
    # 1. Obtener equipos
    print("📋 Obteniendo equipos...")
    teams = get_teams()
    print(f"✅ Encontrados {len(teams)} equipos\n")
    
    all_players = {}
    total_players = 0
    
    # 2. Intentar obtener jugadores por cada equipo
    for team in teams:
        team_id = team['id']
        team_name = team['name']
        
        print(f"🔍 {team_name} (ID: {team_id})...")
        
        # Probar método 1
        players = get_team_players_method1(team_id)
        if players:
            print(f"   ✅ Método 1: {len(players)} jugadores")
            all_players[team_name] = players
            total_players += len(players)
            time.sleep(0.5)  # Respetar rate limit
            continue
        
        # Probar método 2
        players = get_team_players_method2(team_id, SEASON_ID)
        if players:
            print(f"   ✅ Método 2: {len(players)} jugadores")
            all_players[team_name] = players
            total_players += len(players)
            time.sleep(0.5)
            continue
        
        print(f"   ❌ No se pudieron obtener jugadores")
        time.sleep(0.5)
    
    # 3. Si no funcionó, intentar desde partidos
    if total_players == 0:
        print("\n⚠️  Los métodos directos no funcionaron")
        print("🔄 Intentando obtener jugadores desde alineaciones de partidos...\n")
        
        matches = get_matches_with_lineups()
        print(f"📊 Partidos encontrados: {len(matches)}")
        
        # Guardar para análisis
        with open('matches_data.json', 'w', encoding='utf-8') as f:
            json.dump(matches[:5], f, indent=2, ensure_ascii=False)
        print("💾 Primeros 5 partidos guardados en matches_data.json")
    
    # 4. Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    print(f"Total de jugadores obtenidos: {total_players}")
    print(f"Equipos con datos: {len(all_players)}")
    
    if all_players:
        # Guardar todos los jugadores
        with open('all_players_sportmonks.json', 'w', encoding='utf-8') as f:
            json.dump(all_players, f, indent=2, ensure_ascii=False)
        print("\n💾 Datos guardados en: all_players_sportmonks.json")
        
        # Mostrar ejemplo de un jugador
        first_team = list(all_players.keys())[0]
        first_player = all_players[first_team][0]
        print(f"\n📋 Ejemplo de jugador ({first_team}):")
        print(f"   Claves disponibles: {list(first_player.keys())}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
