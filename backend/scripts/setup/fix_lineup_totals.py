import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.database import SessionLocal
from app.models.models import GameweekLineup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix_totals")

def fix_totals():
    db = SessionLocal()
    try:
        lineups = db.query(GameweekLineup).all()
        logger.info(f"Revisando totales de {len(lineups)} alineaciones...")

        updated_count = 0

        for lineup in lineups:
            real_total = sum((lp.points_earned or 0.0) for lp in lineup.players)
            
            # Formatear a 1 decimal
            real_total = round(real_total, 1)
            
            if abs((lineup.points_earned or 0.0) - real_total) > 0.01:
                logger.info(f"Corrigiendo J{lineup.gameweek.number} Equipo {lineup.team_id}: {lineup.points_earned} -> {real_total}")
                lineup.points_earned = real_total
                updated_count += 1

        db.commit()
        logger.info(f"✅ Se han corregido los totales de {updated_count} alineaciones.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_totals()
