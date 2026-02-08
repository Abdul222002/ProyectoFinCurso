"""
Script de prueba para verificar estadísticas de la API Sportmonks
y calcular puntos fantasy
"""

import os
import requests
from dotenv import load_dotenv
from enum import Enum

# Cargar variables de entorno
load_dotenv()

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')
SEASON_ID = 21787  # Scottish Premiership 2025/26

class Position(Enum):
    GK = "GK"
    DEF = "DEF"
    MID = "MID"
    FWD = "FWD"

# Tablas de puntos por posición
GOAL_POINTS = {
    Position.GK: 10,
    Position.DEF: 7,
    Position.MID: 5,
    Position.FWD: 4
}

ASSIST_POINTS = {
    Position.GK: 5,
    Position.DEF: 4,
    Position.MID: 3,
    Position.FWD: 2
}

CLEAN_SHEET_POINTS = {
    Position.GK: 4,
    Position.DEF: 3,
    Position.MID: 1,
    Position.FWD: 0
}


def calcular_puntos_fantasy(stats, position_str, clean_sheet=False):
    """
    Calcula puntos fantasy basándose en estadísticas reales
    
    Args:
        stats: diccionario con estadísticas del jugador
        position_str: posición del jugador (GK, DEF, MID, FWD)
        clean_sheet: si mantuvo portería imbatida
    """
    
    puntos = 0
    position = Position[position_str]
    
    # Goles
    goals = stats.get('goals', 0)
    puntos += goals * GOAL_POINTS[position]
    
    # Asistencias
    assists = stats.get('assists', 0)
    puntos += assists * ASSIST_POINTS[position]
    
    # Minutos jugados
    minutes = stats.get('minutes_played', 0)
    if minutes >= 60:
        puntos += 2
    elif minutes > 0:
        puntos += 1
    
    # Nota del partido
    rating = stats.get('rating')
    if rating:
        rating_value = float(rating) if isinstance(rating, (int, float, str)) else 0
        if rating_value >= 9.0:
            puntos += 5
        elif rating_value >= 8.0:
            puntos += 3
        elif rating_value >= 7.0:
            puntos += 1
    
    # Portería imbatida
    if clean_sheet:
        puntos += CLEAN_SHEET_POINTS[position]
    
    # Penalizaciones
    yellow_cards = stats.get('yellowcards', 0)
    red_cards = stats.get('redcards', 0)
    
    puntos -= yellow_cards * 1
    puntos -= red_cards * 3
    
    return puntos


def obtener_ultimo_partido():
    """Obtiene el fixture más reciente de la temporada"""
    
    print("\n" + "="*80)
    print("📡 OBTENIENDO ÚLTIMOS PARTIDOS DE LA TEMPORADA")
    print("="*80 + "\n")
    
    url = f"https://api.sportmonks.com/v3/football/fixtures/seasons/{SEASON_ID}"
    params = {
        "api_token": API_TOKEN,
        "include": "participants;scores;state"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        fixtures = data.get('data', [])
        
        # Buscar partidos finalizados
        finished = [f for f in fixtures if f.get('state', {}).get('state') == 'FT']
        
        if not finished:
            print("❌ No se encontraron partidos finalizados")
            return None
        
        # Tomar el último partido finalizado
        ultimo = finished[-1]
        
        participants = ultimo.get('participants', [])
        home = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
        away = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
        
        print(f"✅ Partido encontrado:")
        print(f"   {home.get('name')} vs {away.get('name')}")
        print(f"   ID: {ultimo['id']}")
        print(f"   Fecha: {ultimo.get('starting_at')}")
        
        return ultimo['id']
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def obtener_estadisticas_partido(fixture_id):
    """Obtiene estadísticas detalladas de un partido"""
    
    print("\n" + "="*80)
    print(f"📊 OBTENIENDO ESTADÍSTICAS DEL PARTIDO {fixture_id}")
    print("="*80 + "\n")
    
    url = f"https://api.sportmonks.com/v3/football/fixtures/{fixture_id}"
    params = {
        "api_token": API_TOKEN,
        "include": "lineups.player;lineups.details;scores;participants"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        fixture = data.get('data', {})
        
        # Obtener información del partido
        participants = fixture.get('participants', [])
        home = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
        away = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
        
        scores = fixture.get('scores', [])
        home_score = next((s['score']['goals'] for s in scores 
                          if s['description'] == 'CURRENT' and s['participant_id'] == home.get('id')), 0)
        away_score = next((s['score']['goals'] for s in scores 
                          if s['description'] == 'CURRENT' and s['participant_id'] == away.get('id')), 0)
        
        print(f"🏟️  {home.get('name')} {home_score} - {away_score} {away.get('name')}\n")
        
        # Obtener lineups
        lineups = fixture.get('lineups', [])
        
        if not lineups:
            print("❌ No se encontraron lineups")
            return
        
        print(f"✅ {len(lineups)} jugadores encontrados\n")
        print("="*80)
        
        # Analizar primer jugador con estadísticas
        for idx, lineup in enumerate(lineups[:5], 1):  # Primeros 5 jugadores
            
            player_data = lineup.get('player', {})
            details = lineup.get('details', [])
            
            print(f"\n{idx}. {player_data.get('display_name', 'N/A')}")
            print(f"   Posición: {lineup.get('position_id')}")
            print(f"   Titular: {'Sí' if lineup.get('formation_position') else 'No'}")
            
            # Extraer estadísticas de details
            stats = {}
            for detail in details:
                type_name = detail.get('type', {}).get('name', '')
                value = detail.get('value', {}).get('total', 0)
                stats[type_name] = value
            
            print(f"\n   📊 ESTADÍSTICAS DISPONIBLES:")
            print(f"   {'-'*70}")
            for key, value in stats.items():
                print(f"   {key:30} {value}")
            
            # Datos comunes que esperamos
            expected_stats = {
                'minutes_played': stats.get('Minutes Played', 0),
                'goals': stats.get('Goals', 0),
                'assists': stats.get('Assists', 0),
                'yellowcards': stats.get('Yellow Cards', 0),
                'redcards': stats.get('Red Cards', 0),
                'rating': stats.get('Rating')
            }
            
            print(f"\n   🎯 DATOS PARA PUNTOS FANTASY:")
            print(f"   {'-'*70}")
            for key, value in expected_stats.items():
                print(f"   {key:20} {value}")
            
            # Calcular puntos (asumiendo FWD por ahora)
            position_id = lineup.get('position_id', 24)
            
            # Mapeo aproximado position_id -> Position
            if position_id == 24:
                position = "GK"
            elif position_id in [25, 26, 27]:
                position = "DEF"
            elif position_id in [28, 29, 30]:
                position = "MID"
            else:
                position = "FWD"
            
            # Determinar clean sheet
            participant_id = lineup.get('participant_id')
            clean_sheet = False
            if participant_id == home.get('id'):
                clean_sheet = away_score == 0
            else:
                clean_sheet = home_score == 0
            
            puntos = calcular_puntos_fantasy(expected_stats, position, clean_sheet)
            
            print(f"\n   ⚡ PUNTOS FANTASY CALCULADOS: {puntos} puntos")
            print(f"   {'-'*70}")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Función principal"""
    
    print("\n🔍 PRUEBA DE API - ESTADÍSTICAS DE JUGADORES")
    
    if not API_TOKEN:
        print("❌ Error: SPORTMONKS_API_KEY no configurada")
        return
    
    # 1. Obtener último partido
    fixture_id = obtener_ultimo_partido()
    
    if not fixture_id:
        return
    
    # 2. Obtener estadísticas detalladas
    obtener_estadisticas_partido(fixture_id)
    
    print("\n✅ PRUEBA COMPLETADA\n")


if __name__ == "__main__":
    main()
