import sys
import os
from datetime import datetime, timedelta

# Añadir el directorio raíz al path para importar app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.models import Gameweek

def seed():
    db = SessionLocal()
    try:
        count = db.query(Gameweek).count()
        if count > 0:
            print(f"Ya hay {count} jornadas en la base de datos.")
            return

        now = datetime.utcnow()
        gameweeks = []
        for i in range(1, 39):
            start = now + timedelta(weeks=i-1)
            end = start + timedelta(days=3)
            gw = Gameweek(
                number=i,
                start_date=start,
                end_date=end,
                is_active=(i == 1),
                is_finished=False
            )
            gameweeks.append(gw)
        
        db.add_all(gameweeks)
        db.commit()
        print("✅ Se han creado 38 jornadas (la 1 está activa).")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
