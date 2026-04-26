import requests
import json

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
SEASON_ID = 21787

url_teams = f"https://api.sportmonks.com/v3/football/teams/seasons/{SEASON_ID}"
params = {"api_token": API_TOKEN}

try:
    resp = requests.get(url_teams, params=params, timeout=15)
    resp.raise_for_status()
    teams = resp.json().get('data', [])
    print(f"Teams: {len(teams)}\n")
    
    # Probar con varios equipos
    for i, team in enumerate(teams[:2]):  # Solo los primeros 2
        team_id = team['id']
        team_name = team['name']
        
        print(f"\n--- {team_name} (ID: {team_id}) ---")
        
        url_squad = f"https://api.sportmonks.com/v3/football/squads/seasons/{SEASON_ID}/teams/{team_id}"
        resp2 = requests.get(url_squad, params=params, timeout=15)
        resp2.raise_for_status()
        squad_raw = resp2.json()
        
        print(json.dumps(squad_raw, indent=2)[:1000])  # Primeros 1000 caracteres
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
