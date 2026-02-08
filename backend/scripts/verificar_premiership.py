import requests
import json

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
LEAGUE_ID = 501  # Premiership

print("="*60)
print(f"🔍 INVESTIGANDO LIGA ID {LEAGUE_ID}")
print("="*60 + "\n")

# 1. Obtener info de la liga
print("📋 Información de la liga...")
r = requests.get(
    f'https://api.sportmonks.com/v3/football/leagues/{LEAGUE_ID}',
    params={'api_token': API_TOKEN},
    timeout=15
)

if r.status_code == 200:
    liga = r.json().get('data', {})
    print(f"✅ Nombre: {liga.get('name')}")
    print(f"   País: {liga.get('country', {}).get('name', 'N/A')}")
    print(f"   Tipo: {liga.get('type')}")
    print()
else:
    print(f"❌ Error: {r.status_code}\n")

# 2. Obtener temporadas de esta liga
print("📅 Obteniendo temporadas...")
r = requests.get(
    f'https://api.sportmonks.com/v3/football/seasons/leagues/{LEAGUE_ID}',
    params={'api_token': API_TOKEN},
    timeout=15
)

if r.status_code == 200:
    temporadas = r.json().get('data', [])
    print(f"✅ Temporadas encontradas: {len(temporadas)}\n")
    
    # Mostrar las últimas 3
    for temp in temporadas[-3:]:
        print(f"   📅 {temp.get('name')} (ID: {temp.get('id')})")
        print(f"      {temp.get('starting_at')} → {temp.get('ending_at')}")
    
    if temporadas:
        # Usar la más reciente
        season_id = temporadas[-1]['id']
        season_name = temporadas[-1]['name']
        
        print(f"\n✅ Usando temporada: {season_name} (ID: {season_id})")
        
        # 3. Obtener equipos de esta temporada
        print(f"\n🏆 Obteniendo equipos de la temporada {season_id}...")
        r = requests.get(
            f'https://api.sportmonks.com/v3/football/teams/seasons/{season_id}',
            params={'api_token': API_TOKEN},
            timeout=15
        )
        
        if r.status_code == 200:
            teams = r.json().get('data', [])
            print(f"✅ Equipos encontrados: {len(teams)}\n")
            
            for team in teams:
                print(f"   - {team.get('name')} (ID: {team.get('id')})")
            
            # Guardar
            with open('premiership_teams.json', 'w', encoding='utf-8') as f:
                json.dump(teams, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Equipos guardados en: premiership_teams.json")
            
        else:
            print(f"❌ Error obteniendo equipos: {r.status_code}")
            print(r.text[:300])
else:
    print(f"❌ Error obteniendo temporadas: {r.status_code}")

print("\n" + "="*60)
