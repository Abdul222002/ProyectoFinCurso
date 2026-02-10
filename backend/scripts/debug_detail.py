import requests

API_TOKEN = 'uE2hA7iHbThgr4DjSOXCZEMYK7mIja06CEM4RooUWltOIUjXad9hqU4DqcYp'
BASE_URL = "https://api.sportmonks.com/v3/football/fixtures"

def test_detail(fixture_id, params):
    print(f"\n--- Testing Detail {fixture_id} with params {params['include']} ---")
    url = f"{BASE_URL}/{fixture_id}"
    try:
        response = requests.get(url, params=params)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
        else:
            data = response.json().get('data', {})
            print(f"Success. Name: {data.get('name')}")
            # Check keys
            print(f"Keys: {list(data.keys())}")
            if 'lineups' in data: print(f"Lineups: {len(data['lineups'])}")
            if 'round' in data: print(f"Round: {data['round']}")
    except Exception as e:
        print(f"Exception: {e}")

id_match = 19428128 # One that failed in logs
# id_match = 19428056 # Match 33 (should work)

# 1. Full params (Attempt 1)
params_1 = {'api_token': API_TOKEN, 'include': 'participants,scores,round,lineups'}
test_detail(id_match, params_1)

# 2. Basic params (Attempt 2)
params_2 = {'api_token': API_TOKEN, 'include': 'participants,scores,round'}
test_detail(id_match, params_2)

# 3. Minimal params
params_3 = {'api_token': API_TOKEN, 'include': 'participants,round'}
test_detail(id_match, params_3)

# 4. Only participants
params_4 = {'api_token': API_TOKEN, 'include': 'participants'}
test_detail(id_match, params_4)
