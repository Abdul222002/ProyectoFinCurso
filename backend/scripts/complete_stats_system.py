"""
SISTEMA COMPLETO DE EXTRACCIÓN DE STATS Y CÁLCULO DE PUNTOS FANTASY
Basado en descubrimiento de 58 developer_names disponibles
"""

import os
import requests
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')

class Position(Enum):
    GK = "GK"
    DEF = "DEF"
    MID = "MID"
    FWD = "FWD"

# ============================================
# MAPEO COMPLETO API → BASE DE DATOS
# ============================================
STAT_MAPPING = {
    # Básicos
    'MINUTES_PLAYED': 'minutes_played',
    'RATING': 'rating',
    
    # Ataque
    'GOALS': 'goals',
    'ASSISTS': 'assists',
    'SHOTS_ON_TARGET': 'shots_on_target',
    'SHOTS_TOTAL': 'shots_total',  # Extra
    'SHOTS_OFF_TARGET': 'shots_off_target',  # Extra
    
    # Defensa
    'GOALS_CONCEDED': 'goals_conceded',
    'GOALKEEPER_GOALS_CONCEDED': 'goalkeeper_goals_conceded',  # Para GK
    'SAVES': 'saves',
    'SAVES_INSIDE_BOX': 'saves_inside_box',  # Extra
    'CLEARANCES': 'clearances',
    'BLOCKED_SHOTS': 'blocked_shots',  # Extra
    'INTERCEPTIONS': 'interceptions',  # Extra
    
    # Tarjetas
    'YELLOWCARDS': 'yellow_cards',
    'REDCARDS': 'red_cards',
    
    # Stats avanzadas
    'SUCCESSFUL_DRIBBLES': 'successful_dribbles',
    'DRIBBLED_ATTEMPTS': 'dribble_attempts',  # Extra
    'BALL_RECOVERY': 'ball_recoveries',
    'ACCURATE_CROSSES': 'accurate_crosses',
    'TOTAL_CROSSES': 'total_crosses',  # Extra
    'DISPOSSESSED': 'dispossessed',
    'TACKLES': 'tackles',  # Extra
    'TACKLES_WON': 'tackles_won',  # Extra
    'DUELS_WON': 'duels_won',  # Extra
    'DUELS_LOST': 'duels_lost',  # Extra
    'FOULS': 'fouls',  # Extra
    'FOULS_DRAWN': 'fouls_drawn',  # Extra
    'KEY_PASSES': 'key_passes',  # Extra
    'ACCURATE_PASSES': 'accurate_passes',  # Extra
    'PASSES': 'total_passes',  # Extra
}

# ============================================
# SISTEMA DE PUNTOS SIMPLIFICADO
# ============================================

# Puntos por posición
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

def mapear_posicion(type_id):
    """Mapea type_id de API a Position"""
    if type_id == 24:
        return Position.GK
    elif type_id in [25, 26, 27]:
        return Position.DEF
    elif type_id in [28, 29, 30]:
        return Position.MID
    else:
        return Position.FWD

def extract_all_stats(player_entry):
    """
    Extrae TODAS las estadísticas disponibles de un jugador
    Devuelve diccionario con TODOS los campos de PlayerMatchStats
    """
    
    stats = {
        # Básicos
        'minutes_played': 0,
        'rating': None,
        
        # Ataque
        'goals': 0,
        'assists': 0,
        'shots_on_target': 0,
        'shots_total': 0,
        'shots_off_target': 0,
        
        # Defensa
        'clean_sheet': False,  # Se calcula después
        'goals_conceded': 0,
        'goalkeeper_goals_conceded': 0,
        'saves': 0,
        'saves_inside_box': 0,
        'clearances': 0,
        'blocked_shots': 0,
        'interceptions': 0,
        
        # Tarjetas
        'yellow_cards': 0,
        'red_cards': 0,
        'own_goals': 0,  # No disponible en API
        
        # Penaltis (no disponibles)
        'penalties_missed': 0,
        'penalties_won': 0,
        'penalties_saved': 0,
        
        # Stats avanzadas
        'successful_dribbles': 0,
        'dribble_attempts': 0,
        'ball_recoveries': 0,
        'accurate_crosses': 0,
        'total_crosses': 0,
        'dispossessed': 0,
        'tackles': 0,
        'tackles_won': 0,
        'duels_won': 0,
        'duels_lost': 0,
        'fouls': 0,
        'fouls_drawn': 0,
        'key_passes': 0,
        'accurate_passes': 0,
        'total_passes': 0,
    }
    
    # Extraer de details
    details = player_entry.get('details', [])
    
    for stat in details:
        type_info = stat.get('type', {})
        developer_name = type_info.get('developer_name', '')
        data_wrapper = stat.get('data', {})
        valor = data_wrapper.get('value')
        
        # Mapear según STAT_MAPPING
        if developer_name in STAT_MAPPING:
            field_name = STAT_MAPPING[developer_name]
            
            # Convertir tipo según campo
            if field_name == 'rating':
                stats[field_name] = float(valor) if valor else None
            elif field_name in stats:
                try:
                    stats[field_name] = int(valor) if valor else 0
                except:
                    stats[field_name] = 0
    
    return stats

def calcular_puntos_fantasy_simplificado(stats, position, clean_sheet=False):
    """
    Sistema SIMPLIFICADO de puntos fantasy
    
    REGLAS:
    - 90 minutos: +2 puntos
    - Menos de 90: +1 punto
    - Goles y asistencias según posición
    - Tarjetas restan
    - Goles en contra restan
    """
    
    puntos = 0
    
    # ========================================
    # MINUTOS (SIMPLIFICADO)
    # ========================================
    if stats['minutes_played'] >= 90:
        puntos += 2
    elif stats['minutes_played'] > 0:
        puntos += 1
    
    # ========================================
    # GOLES (diferenciado por posición)
    # ========================================
    puntos += stats['goals'] * GOAL_POINTS[position]
    
    # ========================================
    # ASISTENCIAS (diferenciado por posición)
    # ========================================
    puntos += stats['assists'] * ASSIST_POINTS[position]
    
    # ========================================
    # CLEAN SHEET (diferenciado por posición)
    # ========================================
    if clean_sheet:
        puntos += CLEAN_SHEET_POINTS[position]
    
    # ========================================
    # RATING (opcional, solo bonus)
    # ========================================
    if stats['rating']:
        if stats['rating'] >= 9.0:
            puntos += 5
        elif stats['rating'] >= 8.0:
            puntos += 3
        elif stats['rating'] >= 7.0:
            puntos += 1
    
    # ========================================
    # PENALIZACIONES
    # ========================================
    puntos -= stats['yellow_cards'] * 1
    puntos -= stats['red_cards'] * 3
    puntos -= stats['own_goals'] * 2
    
    # Goles encajados (solo para GK)
    if position == Position.GK and stats['goalkeeper_goals_conceded'] > 0:
        puntos -= stats['goalkeeper_goals_conceded'] * 1  # -1 por gol encajado
    
    return puntos

def obtener_partido_completo(fixture_id):
    """Obtiene un partido con TODAS las estadísticas"""
    
    url = f"https://api.sportmonks.com/v3/football/fixtures/{fixture_id}"
    params = {
        "api_token": API_TOKEN,
        "include": "lineups.details.type;participants;scores"
    }
    
    print(f"\n{'='*80}")
    print(f"📊 EXTRAYENDO ESTADÍSTICAS COMPLETAS - FIXTURE {fixture_id}")
    print(f"{'='*80}\n")
    
    response = requests.get(url, params=params, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Error {response.status_code}")
        return None
    
    data = response.json().get('data', {})
    lineups = data.get('lineups', [])
    participants = data.get('participants', [])
    scores = data.get('scores', [])
    
    # Info del partido
    home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
    away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
    
    home_score = next((s['score']['goals'] for s in scores 
                      if s['description'] == 'CURRENT' and s['participant_id'] == home_team.get('id')), 0)
    away_score = next((s['score']['goals'] for s in scores 
                      if s['description'] == 'CURRENT' and s['participant_id'] == away_team.get('id')), 0)
    
    print(f"⚽ {home_team.get('name', 'Home')} {home_score} - {away_score} {away_team.get('name', 'Away')}\n")
    
    # Procesar jugadores
    jugadores_procesados = []
    
    for player_entry in lineups:
        player_name = player_entry.get('player_name', 'N/A')
        type_id = player_entry.get('type_id')
        participant_id = player_entry.get('participant_id')
        
        position = mapear_posicion(type_id)
        
        # Determinar clean sheet
        is_home = participant_id == home_team.get('id')
        clean_sheet = False
        if position in [Position.GK, Position.DEF]:
            clean_sheet = (away_score == 0) if is_home else (home_score == 0)
        
        # Extraer TODAS las stats
        stats = extract_all_stats(player_entry)
        stats['clean_sheet'] = clean_sheet
        
        # Calcular puntos
        fantasy_points = calcular_puntos_fantasy_simplificado(stats, position, clean_sheet)
        stats['fantasy_points'] = fantasy_points
        
        jugadores_procesados.append({
            'name': player_name,
            'position': position.value,
            'team': home_team.get('name') if is_home else away_team.get('name'),
            'stats': stats
        })
    
    return {
        'home_team': home_team.get('name'),
        'away_team': away_team.get('name'),
        'home_score': home_score,
        'away_score': away_score,
        'players': jugadores_procesados
    }

# ============================================
# TEST
# ============================================
if __name__ == "__main__":
    
    partido = obtener_partido_completo(19428171)
    
    if partido:
        print(f"{'JUGADOR':<25} | {'POS':<4} | {'MIN':<3} | {'GOL':<3} | {'AST':<3} | {'NOTA':<4} | {'PTS'}")
        print("-" * 90)
        
        for player in partido['players'][:15]:  # Primeros 15
            s = player['stats']
            if s['minutes_played'] > 0:  # Solo los que jugaron
                print(f"{player['name']:<25} | {player['position']:<4} | {s['minutes_played']:<3} | "
                      f"{s['goals']:<3} | {s['assists']:<3} | {s['rating'] or 0:<4.1f} | {s['fantasy_points']}")
        
        print("\n✅ TODAS LAS ESTADÍSTICAS EXTRAÍDAS CORRECTAMENTE")
