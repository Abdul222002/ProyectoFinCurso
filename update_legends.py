import sys
import os
import requests
import time

sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.core.database import SessionLocal
from app.models.models import Player

def get_wiki_image(name):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{name} footballer",
        "gsrlimit": 1,
        "prop": "pageimages",
        "piprop": "original",
        "format": "json"
    }
    headers = {
        "User-Agent": "MyFootballApp/1.0 (contact@example.com)"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        if pages:
            page = list(pages.values())[0]
            if "original" in page:
                return page["original"]["source"]
    except Exception as e:
        print(f"Error fetching {name}: {e}")
    return None

def update_legends():
    db = SessionLocal()
    try:
        legends = db.query(Player).filter(Player.is_legend == True).all()
        print(f"Updating images for {len(legends)} legend players...")
        
        updated_count = 0
        for p in legends:
            # Skip if they already have an image and it's not a placeholder
            if p.image_url and "placeholder" not in p.image_url and "wikimedia" in p.image_url:
                continue
                
            img_url = get_wiki_image(p.name)
            if img_url:
                p.image_url = img_url
                print(f"[{p.id}] {p.name} -> {img_url}")
                updated_count += 1
            else:
                print(f"[{p.id}] {p.name} -> NOT FOUND")
            
            # small delay to not hammer Wikipedia API
            time.sleep(0.1)
            
        if updated_count > 0:
            db.commit()
            print(f"Successfully updated and saved {updated_count} players.")
        else:
            print("No players were updated.")
            
    finally:
        db.close()

if __name__ == "__main__":
    update_legends()
