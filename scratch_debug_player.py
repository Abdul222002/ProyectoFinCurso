import sys
import os
# Añadir el path del backend para poder importar los modelos
sys.path.append(os.path.abspath("backend"))

from app.core.database import SessionLocal
from app.models.models import Player, Match, Gameweek, PlayerMatchStats
from sqlalchemy import or_

db = SessionLocal()

player_id = 518 # Dave Richards
player = db.query(Player).filter(Player.id == player_id).first()
print(f"DEBUG: Player {player.name}, Team: '{player.current_team}'")

player_team = player.current_team or "Unknown"
search_term = "Dundee" if "Dundee" in player_team else player_team
print(f"DEBUG: Search term: '{search_term}'")

all_gameweeks = db.query(Gameweek).all()
gw_id_to_num = {gw.id: gw.number for gw in all_gameweeks}
print(f"DEBUG: Found {len(all_gameweeks)} gameweeks. Map sample: {list(gw_id_to_num.items())[:5]}")

team_matches = db.query(Match).filter(
    or_(
        Match.home_team.ilike(f"%{search_term}%"),
        Match.away_team.ilike(f"%{search_term}%")
    )
).all()
print(f"DEBUG: Found {len(team_matches)} matches for team.")

matches_by_gw_num = {}
for m in team_matches:
    num = gw_id_to_num.get(m.gameweek_id, 0)
    if num > 0:
        if num not in matches_by_gw_num:
            matches_by_gw_num[num] = []
        matches_by_gw_num[num].append(m)

print(f"DEBUG: matches_by_gw_num keys: {sorted(matches_by_gw_num.keys())}")

# Check J31 specifically
print(f"DEBUG: J31 (num 31) in matches_by_gw_num? {31 in matches_by_gw_num}")
if 31 in matches_by_gw_num:
    for m in matches_by_gw_num[31]:
        print(f"  Match: {m.home_team} vs {m.away_team} (ID: {m.id}, GW_ID: {m.gameweek_id})")

db.close()
