import requests

headers = {"Authorization": "Bearer fake_token"} # We might need a real token or just test gameweek
try:
    gw_res = requests.get("http://localhost:8000/teams/active-gameweek")
    print("Gameweek Response:", gw_res.status_code, gw_res.text)
except Exception as e:
    print("Error:", e)
