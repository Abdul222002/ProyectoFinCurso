import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.core.database import SessionLocal
from app.models.models import Player

# Manual URLs for the 5 missing legends
manual_urls = {
    338: "https://upload.wikimedia.org/wikipedia/commons/4/4e/Johan_Cruyff_1974c.jpg", # Johan Cruyff
    345: "https://upload.wikimedia.org/wikipedia/commons/8/87/Paolo_Maldini_AC_Milan.jpg", # Paolo Maldini
    373: "https://upload.wikimedia.org/wikipedia/commons/8/89/Romario_en_2011.jpg", # Romário
    379: "https://upload.wikimedia.org/wikipedia/commons/e/ec/Zlatan_Ibrahimovi%C4%87_2018.jpg", # Zlatan Ibrahimović
    381: "https://upload.wikimedia.org/wikipedia/commons/b/b5/Sergio_Ag%C3%BCero_2018.jpg" # Sergio Agüero
}

def update_manual():
    db = SessionLocal()
    try:
        updated = 0
        for p_id, url in manual_urls.items():
            player = db.query(Player).filter(Player.id == p_id).first()
            if player:
                player.image_url = url
                print(f"Updated {player.name} -> {url}")
                updated += 1
                
        if updated > 0:
            db.commit()
            print(f"Commit successful for {updated} players.")
    finally:
        db.close()

if __name__ == "__main__":
    update_manual()
