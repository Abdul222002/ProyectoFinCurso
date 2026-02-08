import requests

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"

# Listar todas las ligas
r = requests.get(
    'https://api.sportmonks.com/v3/football/leagues',
    params={'api_token': API_TOKEN},
    timeout=15
)

data = r.json()
print(f"Total ligas: {len(data.get('data', []))}")

# Buscar ligas escocesas
scottish = [l for l in data.get('data', []) if 'scot' in l.get('name', '').lower()]
print(f"\nLigas escocesas encontradas: {len(scottish)}")
for l in scottish:
    print(f"  - {l['name']} (ID: {l['id']})")
