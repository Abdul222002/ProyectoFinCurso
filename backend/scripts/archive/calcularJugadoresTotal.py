import requests

# TU CONFIGURACIÓN
api_token = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
season_id = 21787  # ID de la temporada 23/24 (o la actual) de Escocia

url = f"https://api.sportmonks.com/v3/football/teams/seasons/{season_id}"
params = {
    "api_token": api_token,
    "include": "players" # Pedimos los jugadores de cada equipo
}

print("⏳ Conectando con Sportmonks para hacer el censo...")
response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json().get('data', [])
    
    total_players = 0
    breakdown = []
    
    print(f"\n--- CENSO DE LA LIGA ESCOCESA ({len(data)} Equipos) ---")
    
    for team in data:
        team_name = team.get('name')
        squad = team.get('players', [])
        squad_size = len(squad)
        
        total_players += squad_size
        breakdown.append(f"{team_name}: {squad_size} jugadores")
        
    print("\n".join(breakdown))
    print("-" * 30)
    print(f"✅ TOTAL JUGADORES EN BASE DE DATOS: {total_players}")
    
    # CÁLCULO DE CAPACIDAD DE LIGA
    # Asumimos que un usuario necesita 15 jugadores (11 titulares + 4 banca)
    max_usuarios = total_players // 15
    print(f"📊 Capacidad Teórica: {max_usuarios} usuarios por liga (si se compran todos)")
    
    # Cálculo realista (solo jugadores que juegan)
    realistas = int(total_players * 0.6) # El 60% son relevantes
    max_real = realistas // 15
    print(f"📉 Capacidad Realista (Competitiva): ~{max_real} usuarios por liga")

else:
    print(f"Error: {response.status_code}")