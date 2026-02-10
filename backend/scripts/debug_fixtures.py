import requests

API_TOKEN = 'uE2hA7iHbThgr4DjSOXCZEMYK7mIja06CEM4RooUWltOIUjXad9hqU4DqcYp'
BASE_URL = "https://api.sportmonks.com/v3/football/fixtures/between"

def test_fetch(name, params):
    print(f"\n--- Testing {name} ---")
    url = f"{BASE_URL}/2025-08-22/2025-08-25"
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json().get('data', [])
            print(f"Fixtures found: {len(data)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

# 1. User Params
params_user = {
    'api_token': API_TOKEN,
    'include': 'participants'
}
test_fetch("User Params", params_user)

# 2. My Params (Full)
params_full = {
    'api_token': API_TOKEN,
    'include': 'participants,scores,round,lineups',
    # 'leagues': 501
}
test_fetch("My Params (Full)", params_full)

# 3. My Params (No Lineups)
params_no_lineups = {
    'api_token': API_TOKEN,
    'include': 'participants,scores,round',
}
test_fetch("My Params (No Lineups)", params_no_lineups)
