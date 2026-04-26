import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.core.database import SessionLocal
from app.models.models import Player

def check_missing():
    db = SessionLocal()
    try:
        legends = db.query(Player).filter(Player.is_legend == True).all()
        missing = []
        for p in legends:
            if not p.image_url or "placeholder" in p.image_url or "wikimedia" not in p.image_url:
                missing.append(p)
                
        print(f"Missing images for {len(missing)} players:")
        for m in missing:
            print(f"- {m.id}: {m.name}")
    finally:
        db.close()

if __name__ == "__main__":
    check_missing()
