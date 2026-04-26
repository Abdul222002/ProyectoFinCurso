import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.core.database import SessionLocal
from app.models.models import Player

def check_count():
    db = SessionLocal()
    try:
        missing_count = db.query(Player).filter(
            (Player.image_url == None) | 
            (Player.image_url == "") | 
            (Player.image_url.like("%placeholder%"))
        ).count()
        total_count = db.query(Player).count()
        
        print(f"Total players: {total_count}")
        print(f"Players missing images: {missing_count}")
    finally:
        db.close()

if __name__ == "__main__":
    check_count()
