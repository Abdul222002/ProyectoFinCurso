"""
Script para importar jugadores desde la API de Sportmonks
Recorre todos los equipos de la Scottish Premiership y obtiene sus jugadores
"""

import requests
import json
from typing import List, Dict, Optional

# ==========================================
# CONFIGURACIÓN
# ==========================================

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
SEASON_ID = 21787  # Scottish Premiership 2023/24
BASE_URL = "https://api.sportmonks.com/v3/football"

# Mapeo de posiciones de Sportmonks a nuestro sistema
POSITION_MAP = {
    "Goalkeeper": "GK",
    "Defender": "DEF",
    "Midfielder": "MID",
    "Attacker": "FWD",
    "Forward": "FWD",
}


# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def get_position_enum(sportmonks_position: str) -> str:
    """
    Convierte la posición de Sportmonks a nuestro enum (GK, DEF, MID, FWD)
    """
    for key, value in POSITION_MAP.items():
        if key.lower() in sportmonks_position.lower():
            return value
    
    # Default: si no sabemos, lo ponemos como MID
    return "MID"


def calcular_precio_base(overall: int) -> float:
    """
    Calcula el precio base según el overall del jugador
    """
    if overall >= 80:
        return 10000000.0
    elif overall >= 75:
        return 4000000.0
    elif overall >= 70:
        return 1000000.0
    elif overall >= 65:
        return 500000.0
    else:
        return 300000.0


def estimar_overall(edad: int, posicion: str) -> int:
    """
    Estima un overall base para jugadores sin datos de FIFA
    Basado en edad y posición
    """
    # Jugadores jóvenes (sub-23): 60-68
    if edad < 23:
        return 62
    # Jugadores en su prime (23-29): 65-72
    elif edad < 30:
        return 68
    # Jugadores veteranos (30+): 63-70
    else:
        return 65


# ==========================================
# FUNCIONES DE API
# ==========================================

def obtener_equipos_temporada(season_id: int) -> List[Dict]:
    """
    Obtiene todos los equipos de una temporada
    """
    url = f"{BASE_URL}/teams/seasons/{season_id}"
    params = {
        "api_token": API_TOKEN,
        "include": "players"  # Incluimos los jugadores de cada equipo
    }
    
    print(f"🔄 Obteniendo equipos de la temporada {season_id}...")
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"❌ Error {response.status_code}: {response.text}")
        return []
    
    data = response.json().get('data', [])
    print(f"✅ Encontrados {len(data)} equipos")
    return data


def obtener_detalles_jugador(player_id: int) -> Optional[Dict]:
    """
    Obtiene información detallada de un jugador específico
    """
    url = f"{BASE_URL}/players/{player_id}"
    params = {
        "api_token": API_TOKEN,
        "include": "position,nationality,detailedPosition"
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        return None
    
    return response.json().get('data')


# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================

def importar_jugadores_sportmonks() -> List[Dict]:
    """
    Importa todos los jugadores de la Scottish Premiership desde Sportmonks
    
    Returns:
        Lista de diccionarios con los datos de los jugadores listos para insertar en BD
    """
    equipos = obtener_equipos_temporada(SEASON_ID)
    
    if not equipos:
        print("❌ No se pudieron obtener los equipos")
        return []
    
    jugadores_procesados = []
    total_jugadores = 0
    
    print("\n" + "="*60)
    print("PROCESANDO JUGADORES POR EQUIPO")
    print("="*60 + "\n")
    
    for equipo in equipos:
        team_name = equipo.get('name', 'Unknown')
        squad = equipo.get('players', [])
        
        print(f"\n📋 {team_name}: {len(squad)} jugadores")
        print("-" * 40)
        
        for player_data in squad:
            player_id = player_data.get('id')
            player_name = player_data.get('display_name') or player_data.get('common_name') or player_data.get('name', 'Unknown')
            
            # Datos básicos que vienen en el listado
            position_info = player_data.get('position', {})
            position_name = position_info.get('name', 'Midfielder') if isinstance(position_info, dict) else 'Midfielder'
            
            nationality_info = player_data.get('nationality', {})
            nationality = nationality_info.get('name', 'Scotland') if isinstance(nationality_info, dict) else 'Scotland'
            
            # Edad (calculada desde fecha de nacimiento si existe)
            date_of_birth = player_data.get('date_of_birth')
            age = 25  # Default
            if date_of_birth:
                from datetime import datetime
                birth_year = int(date_of_birth.split('-')[0])
                age = datetime.now().year - birth_year
            
            # Posición en nuestro sistema
            position_enum = get_position_enum(position_name)
            
            # Overall estimado (ya que Sportmonks no tiene ratings FIFA)
            overall = estimar_overall(age, position_enum)
            
            # Crear objeto jugador
            jugador = {
                "sportmonks_id": player_id,
                "name": player_name,
                "age": age,
                "position": position_enum,
                "nationality": nationality,
                "overall_rating": overall,
                "potential": overall + 5,  # Potencial ligeramente superior
                "current_team": team_name,
                "is_legend": False,
                "current_price": calcular_precio_base(overall),
                "target_price": calcular_precio_base(overall),
                "image_url": player_data.get('image_path'),
                
                # Stats por defecto (se pueden ajustar después)
                "pace": overall - 5,
                "shooting": overall - 3 if position_enum in ["FWD", "MID"] else overall - 10,
                "passing": overall - 2,
                "dribbling": overall - 4,
                "defending": overall - 3 if position_enum in ["DEF", "GK"] else overall - 15,
                "physical": overall - 2,
            }
            
            jugadores_procesados.append(jugador)
            total_jugadores += 1
            
            print(f"  ✓ {player_name} ({position_enum}) - OVR {overall}")
    
    print("\n" + "="*60)
    print(f"✅ TOTAL PROCESADO: {total_jugadores} jugadores")
    print("="*60 + "\n")
    
    return jugadores_procesados


def guardar_json(jugadores: List[Dict], filename: str = "jugadores_sportmonks.json"):
    """
    Guarda los jugadores en un archivo JSON
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(jugadores, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Datos guardados en: {filename}")


def mostrar_estadisticas(jugadores: List[Dict]):
    """
    Muestra estadísticas de los jugadores importados
    """
    from collections import Counter
    
    print("\n" + "="*60)
    print("ESTADÍSTICAS DE IMPORTACIÓN")
    print("="*60)
    
    # Por posición
    posiciones = Counter([j['position'] for j in jugadores])
    print("\n📊 Jugadores por posición:")
    for pos, count in posiciones.most_common():
        print(f"   {pos}: {count}")
    
    # Por equipo
    equipos = Counter([j['current_team'] for j in jugadores])
    print("\n🏆 Jugadores por equipo:")
    for team, count in equipos.most_common():
        print(f"   {team}: {count}")
    
    # Por overall
    print("\n⭐ Distribución de Overall:")
    overalls = [j['overall_rating'] for j in jugadores]
    print(f"   Promedio: {sum(overalls) / len(overalls):.1f}")
    print(f"   Máximo: {max(overalls)}")
    print(f"   Mínimo: {min(overalls)}")
    
    # Capacidad de liga
    print("\n🎮 Capacidad de Liga:")
    total = len(jugadores)
    max_usuarios = total // 15
    max_real = int(total * 0.6) // 15
    print(f"   Total jugadores: {total}")
    print(f"   Capacidad teórica: {max_usuarios} usuarios/liga")
    print(f"   Capacidad realista: {max_real} usuarios/liga")


# ==========================================
# EJECUCIÓN
# ==========================================

if __name__ == "__main__":
    print("🚀 IMPORTADOR DE JUGADORES - SPORTMONKS API")
    print("="*60 + "\n")
    
    # Importar jugadores
    jugadores = importar_jugadores_sportmonks()
    
    if jugadores:
        # Guardar en JSON
        guardar_json(jugadores)
        
        # Mostrar estadísticas
        mostrar_estadisticas(jugadores)
        
        print("\n✅ Proceso completado exitosamente!")
        print("\n💡 Siguiente paso: Ejecutar el script de fusión con datos FIFA")
        print("   para mejorar las estadísticas y fotos de los jugadores.")
    else:
        print("\n❌ No se pudieron importar jugadores")
#Tiene que haber 338 jugadores gracias al script que hemos hecho