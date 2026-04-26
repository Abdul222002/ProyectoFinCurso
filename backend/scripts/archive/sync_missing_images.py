import sys
import os
import requests
import time

sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.core.database import SessionLocal
from app.models.models import Player

def get_wiki_image(name, lang="en"):
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{name} footballer" if lang == "en" else f"{name} futbolista",
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
        print(f"Error fetching {name} ({lang}): {e}")
    return None

def update_missing():
    db = SessionLocal()
    try:
        # Maradona manual override for better resolution / different image
        maradona = db.query(Player).filter(Player.id == 331).first() # 331 is Maradona
        if maradona:
            # Let's try to get his image from the Spanish Wikipedia, it usually has a better/iconic picture
            img_url = get_wiki_image("Diego Maradona", lang="es")
            if img_url:
                maradona.image_url = img_url
                print(f"Updated Maradona: {img_url}")
            else:
                # Fallback manual high-res image
                maradona.image_url = "https://upload.wikimedia.org/wikipedia/commons/b/be/Diego_Maradona_-_Mundial_86.jpg"
                print("Updated Maradona with fallback")

        # Now find all players missing images
        missing_players = db.query(Player).filter(
            (Player.image_url == None) | 
            (Player.image_url == "") | 
            (Player.image_url.like("%placeholder%"))
        ).all()
        
        print(f"Found {len(missing_players)} players missing images.")
        
        updated_count = 0
        for p in missing_players:
            img_url = get_wiki_image(p.name, lang="en")
            if not img_url:
                img_url = get_wiki_image(p.name, lang="es")
                
            if img_url:
                p.image_url = img_url
                print(f"[{p.id}] {p.name} -> {img_url}", flush=True)
                updated_count += 1
            else:
                print(f"[{p.id}] {p.name} -> NOT FOUND", flush=True)
            
            time.sleep(0.1) # Be nice to Wikipedia API
            
        if updated_count > 0 or maradona:
            db.commit()
            print(f"Successfully updated and saved {updated_count} missing players. (Plus Maradona)")
        else:
            print("No new players were updated.")
            
    finally:
        db.close()

if __name__ == "__main__":
    update_missing()
