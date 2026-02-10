import requests

API_TOKEN = 'uE2hA7iHbThgr4DjSOXCZEMYK7mIja06CEM4RooUWltOIUjXad9hqU4DqcYp'
BASE_URL = "https://api.sportmonks.com/v3/football/fixtures/between"

def check_rounds():
    url = f"{BASE_URL}/2025-10-04/2025-10-06" # Weekend in Oct
    params = {
        'api_token': API_TOKEN,
        'include': 'round' 
    }
    
    response = requests.get(url, params=params)
    data = response.json().get('data', [])
    
    print(f"Fixtures found: {len(data)}")
    for f in data[:3]:
        print(f"ID: {f['id']}")
        print(f"Round: {f.get('round')}")
        
check_rounds()
