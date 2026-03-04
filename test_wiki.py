import requests

def test_wiki(name):
    # Try searching Wikipedia
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
    
    response = requests.get(url, params=params, headers=headers)
    try:
        data = response.json()
    except Exception as e:
        print(f"Error parsing JSON. Status {response.status_code}. Response: {response.text[:200]}")
        return None
        
    pages = data.get("query", {}).get("pages", {})
    if not pages:
        return None
        
    page = list(pages.values())[0]
    if "original" in page:
        return page["original"]["source"]
    return None

if __name__ == "__main__":
    names = ["Pelé", "Diego Maradona", "Zinedine Zidane", "Marco van Basten"]
    for n in names:
        print(f"{n}: {test_wiki(n)}")
