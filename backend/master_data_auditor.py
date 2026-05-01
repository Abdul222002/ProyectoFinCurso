import requests
import sys
import os
sys.path.append(os.path.abspath("backend"))

from app.core.database import SessionLocal
from app.models.models import Match, Player, PlayerMatchStats

API_TOKEN = '8Jolb4HwJbTxrxBwYJWjndgAHXstanHw5rrrtqCB4f17SeV6uvHiJ8uYKGb1'

def get_match_real_teams(sm_match_id):
    url = f"https://api.sportmonks.com/v3/football/fixtures/{sm_match_id}?include=participants"
    headers = {'Authorization': API_TOKEN}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if 'data' in data:
            participants = data['data'].get('participants', [])
            teams = {}
            for p in participants:
                # meta -> location: 'home' o 'away'
                location = p.get('meta', {}).get('location')
                teams[location] = p.get('name')
            return teams
    except Exception as e:
        print(f"Error checking API for {sm_match_id}: {e}")
    return None

db = SessionLocal()

# 1. Auditar los partidos que tienen "Dundee" en el nombre (ID Sportmonks)
matches_to_audit = db.query(Match).filter(
    (Match.home_team.ilike("%Dundee%")) | (Match.away_team.ilike("%Dundee%"))
).all()

print(f"Auditing {len(matches_to_audit)} matches using Sportmonks API...")

changes_made = 0
for m in matches_to_audit:
    real_teams = get_match_real_teams(m.sportmonks_id)
    if real_teams:
        real_home = real_teams.get('home')
        real_away = real_teams.get('away')
        
        # Mapeo manual preciso para evitar normalización errónea
        def fix_name(name):
            if name == 'Dundee FC' or name == 'Dundee': return 'Dundee'
            if name == 'Dundee United': return 'Dundee United'
            return name

        fixed_home = fix_name(real_home)
        fixed_away = fix_name(real_away)
        
        if m.home_team != fixed_home or m.away_team != fixed_away:
            print(f"Match {m.id} (SM:{m.sportmonks_id}): {m.home_team} vs {m.away_team} -> {fixed_home} vs {fixed_away}")
            m.home_team = fixed_home
            m.away_team = fixed_away
            changes_made += 1

if changes_made > 0:
    db.commit()
    print(f"✅ SUCCESS: Fixed {changes_made} match names in database.")
else:
    print("ℹ️ No match name changes needed.")

# 2. Auditar Jugadores (Dave Richards y Ryan Astley como ejemplos, pero extendido)
# Buscamos jugadores asignados a Dundee o Dundee United
players_to_fix = db.query(Player).filter(
    (Player.current_team == 'Dundee') | (Player.current_team == 'Dundee United')
).all()

player_fixes = 0
for p in players_to_fix:
    # Miramos sus estadísticas reales para ver en qué equipo juega de verdad
    # Tomamos el partido más reciente donde haya jugado minutos
    last_stat = db.query(PlayerMatchStats).join(Match).filter(
        PlayerMatchStats.player_id == p.id,
        PlayerMatchStats.minutes_played > 0
    ).order_by(Match.kickoff_time.desc()).first()
    
    if last_stat:
        # El equipo real del jugador es el que aparece en el partido que jugó
        m = last_stat.match
        match_team = ""
        # Lógica de prioridad: si el partido tiene un nombre exacto, lo usamos
        if 'Dundee United' in m.home_team or 'Dundee United' in m.away_team: match_team = 'Dundee United'
        elif 'Dundee' in m.home_team or 'Dundee' in m.away_team: match_team = 'Dundee'
        
        if match_team and p.current_team != match_team:
            print(f"Player {p.name} (ID:{p.id}): {p.current_team} -> {match_team}")
            p.current_team = match_team
            player_fixes += 1

if player_fixes > 0:
    db.commit()
    print(f"✅ SUCCESS: Fixed {player_fixes} player team assignments.")
else:
    print("ℹ️ No player team changes needed.")

db.close()
