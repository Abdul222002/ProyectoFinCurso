import json
from fuzzywuzzy import fuzz # Librería para comparar nombres parecidos

def importar_jugadores_fusionados():
    # 1. CARGAMOS LOS DATOS (Simulado)
    # Lista real de Sportmonks (La Verdad)
    sportmonks_players = [
        {"id": 1, "name": "Kyogo Furuhashi", "team": "Celtic", "position": "FWD"},
        {"id": 2, "name": "James Tavernier", "team": "Rangers", "position": "DEF"},
        {"id": 3, "name": "John Canterano", "team": "Aberdeen", "position": "MID"}, # Este NO está en FIFA
    ]

    # Lista de FIFA (La Decoración)
    # Supongamos que esto viene de tu CSV
    fifa_database = [
        {"name": "Kyogo Furuhashi", "rating": 77, "photo": "url_kyogo.png"},
        {"name": "J. Tavernier", "rating": 78, "photo": "url_tav.png"},
    ]

    players_to_insert = []

    print("🔄 Iniciando Fusión de Datos...")

    for real_player in sportmonks_players:
        
        # 2. BUSCAR MATCH EN FIFA
        match_found = None
        
        for fifa_player in fifa_database:
            # Usamos coincidencia difusa (Fuzzy) por si el nombre varía un poco
            # Ej: "James Tavernier" vs "J. Tavernier"
            ratio = fuzz.token_sort_ratio(real_player["name"], fifa_player["name"])
            
            if ratio > 85: # Si se parecen más del 85%
                match_found = fifa_player
                break
        
        # 3. DECIDIR QUÉ DATOS GUARDAR
        nuevo_jugador = {
            "external_id": real_player["id"],
            "name": real_player["name"],
            "position": real_player["position"],
            "real_team": real_player["team"]
        }

        if match_found:
            # ✅ ESTÁ EN FIFA: Usamos sus datos bonitos
            print(f"✅ MATCH: {real_player['name']} (OVR {match_found['rating']})")
            nuevo_jugador["photo_url"] = match_found["photo"]
            nuevo_jugador["base_rating_fifa"] = match_found["rating"]
            nuevo_jugador["current_rating_fifa"] = match_found["rating"]
            # Precio según la tabla que hicimos antes
            nuevo_jugador["current_price"] = calcular_precio_base(match_found["rating"])
            
        else:
            # ❌ NO ESTÁ EN FIFA: Creamos Carta Genérica (Canterano)
            print(f"👻 GHOST: {real_player['name']} - Creando genérico...")
            nuevo_jugador["photo_url"] = "https://tu-web.com/assets/default_silhouette.png"
            nuevo_jugador["base_rating_fifa"] = 58  # Media de bronce baja
            nuevo_jugador["current_rating_fifa"] = 58
            nuevo_jugador["current_price"] = 150000 # Precio mínimo
            
            # NOTA: Le ponemos un 'flag' interno por si luego queremos actualizarlo a mano
            nuevo_jugador["is_generic"] = True

        players_to_insert.append(nuevo_jugador)

    # 4. AQUÍ HARÍAS EL DB.ADD_ALL(players_to_insert)
    return players_to_insert

# Helper rápido para el precio (copiado de nuestra lógica anterior)
def calcular_precio_base(ovr):
    if ovr >= 80: return 10000000
    if ovr >= 75: return 4000000
    if ovr >= 70: return 1000000
    return 500000

# --- EJECUCIÓN ---
importar_jugadores_fusionados()