import requests

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
SEASON_ID = 21787

url = f"https://api.sportmonks.com/v3/football/teams/seasons/{SEASON_ID}"
params = {"api_token": API_TOKEN}

try:
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    teams = resp.json().get('data', [])
    print(f"Status: {resp.status_code}")
    print(f"Teams found: {len(teams)}")
    
    if teams:
        print(f"\n First team: {teams[0]['name']}")
        
        # Probar obtener jugadores del primer equipo
        team_id = teams[0]['id']
        url_players = f"https://api.sportmonks.com/v3/football/squads/seasons/{SEASON_ID}/teams/{team_id}"
        resp2 = requests.get(url_players, params=params, timeout=15)
        resp2.raise_for_status()
        data = resp2.json().get('data', [])
        
        if data:
            squad_data = data[0] if isinstance(data, list) else data
            players = squad_data.get('players', [])
            print(f"Players in first team: {len(players)}")
            if players:
                print(f"First player: {players[0].get('player', {}).get('display_name')}")
        
except Exception as e:
    print(f"Error: {e}")
