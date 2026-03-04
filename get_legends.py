import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')

# Add the backend directory to sys.path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.core.database import SessionLocal
from app.models.models import Player

def get_legends():
    db = SessionLocal()
    try:
        legends = db.query(Player).filter(Player.is_legend == True).all()
        print(f"Total legends found: {len(legends)}")
        
        data = []
        for l in legends:
            data.append({"id": l.id, "name": l.name})
            
        with open("legends.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print("Data written to legends.json")
    finally:
        db.close()

if __name__ == "__main__":
    get_legends()
