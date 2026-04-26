import sys
import os

# Ajustar el PYTHONPATH para importar desde backend
sys.path.append("/backend")

from app.core.database import SessionLocal
from app.models.models import UserCard, Team

db = SessionLocal()

try:
    cards = db.query(UserCard).filter(UserCard.team_id == None, UserCard.league_id != None).all()
    fixed = 0
    for card in cards:
        team = db.query(Team).filter(Team.user_id == card.user_id, Team.league_id == card.league_id).first()
        if team:
            card.team_id = team.id
            fixed += 1

    db.commit()
    print(f"[{fixed}] Cartas huérfanas restauradas correctamente a sus respectivos equipos.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
