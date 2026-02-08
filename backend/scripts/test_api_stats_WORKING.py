"""
Script ACTUALIZADO con el include correcto: lineups.player.statistics
Basado en el script funcional del usuario
"""

import os
import requests
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')

# Partido de ejemplo (Celtic vs Rangers o similar)
MATCH_ID = 18535655

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

def mapear_posicion(type_id):
    """Mapea type_id de Sportmonks a nuestra posición"""
    # Basado en observaciones anteriores
    if type_id == 24:
        return Position.GK
    elif type_id in [25, 26, 27]:
        return Position.DEF
    elif type_id in [28, 29, 30]:
        return Position.MID
    else:
        return Position.FWD

def calcular_puntos_fantasy(stats_dict, position, clean_sheet=False):
    """Calcula puntos fantasy con la fórmula diferenciada"""
    
    puntos = 0
    
    # Goles
    goals = stats_dict.get('goals', 0) or 0
    puntos += goals * GOAL_POINTS[position]
    
    # Asistencias
    assists = stats_dict.get('assists', 0) or 0
    puntos += assists * ASSIST_POINTS[position]
    
    # Minutos jugados (necesitamos calcularlo de otra forma si no está)
    minutes = stats_dict.get('minutes_played', 90)  # Asumir 90 por defecto
    if minutes >= 60:
        puntos += 2
    elif minutes > 0:
        puntos += 1
    
    # Rating
    rating = stats_dict.get('rating')
    if rating:
        try:
            rating_float = float(rating)
            if rating_float >= 9.0:
                puntos += 5
            elif rating_float >= 8.0:
                puntos += 3
            elif rating_float >= 7.0:
                puntos += 1
        except:
            pass
    
    # Clean sheet
    if clean_sheet:
        puntos += CLEAN_SHEET_POINTS[position]
    
    # Tarjetas
    yellowcards = stats_dict.get('yellowcards', 0) or 0
    redcards = stats_dict.get('redcards', 0) or 0
    
    puntos -= yellowcards * 1
    puntos -= redcards * 3
    
    return puntos

def obtener_estadisticas_partido():
    """Obtiene stats y calcula puntos fantasy"""
    
    base_url = f"https://api.sportmonks.com/v3/football/fixtures/{MATCH_ID}"
    
    # ✅ INCLUDE CORRECTO
    params = {
        "api_token": API_TOKEN,
        "include": "lineups.player.statistics;participants;scores"
    }

    print(f"\n" + "="*80)
    print(f"📡 OBTENIENDO ESTADÍSTICAS DEL PARTIDO {MATCH_ID}")
    print("="*80 + "\n")
    
    response = requests.get(base_url, params=params, timeout=30)

    if response.status_code == 200:
        data = response.json().get('data', {})
        
        # Info del partido
        nombre_partido = data.get('name', 'N/A')
        print(f"⚽ PARTIDO: {nombre_partido}\n")
        
        # Obtener resultado para clean sheets
        participants = data.get('participants', [])
        scores = data.get('scores', [])
        
        home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
        away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
        
        home_score = next((s['score']['goals'] for s in scores 
                          if s['description'] == 'CURRENT' and s['participant_id'] == home_team.get('id')), 0)
        away_score = next((s['score']['goals'] for s in scores 
                          if s['description'] == 'CURRENT' and s['participant_id'] == away_team.get('id')), 0)
        
        print(f"🏟️  {home_team.get('name', 'Home')} {home_score} - {away_score} {away_team.get('name', 'Away')}")
        print("="*80)
        
        # Lineups
        lineups = data.get('lineups', [])
        
        if not lineups:
            print("\n❌ No hay lineups disponibles")
            return
        
        print(f"\n👥 {len(lineups)} jugadores en el partido\n")
        
        # Contador de puntos por equipo
        puntos_home = 0
        puntos_away = 0
        
        # Procesar primeros 10 jugadores como ejemplo
        for idx, player_entry in enumerate(lineups[:10], 1):
            
            player_name = player_entry.get('player_name', 'N/A')
            type_id = player_entry.get('type_id')
            participant_id = player_entry.get('participant_id')
            
            # Mapear posición
            position = mapear_posicion(type_id)
            
            # Determinar clean sheet
            is_home = participant_id == home_team.get('id')
            clean_sheet = False
            if position in [Position.GK, Position.DEF]:
                clean_sheet = (away_score == 0) if is_home else (home_score == 0)
            
            # Convertir stats
            stats_raw = player_entry.get('statistics', [])
            stats_dict = {}
            for stat in stats_raw:
                tipo = stat.get('type', {}).get('name')
                valor = stat.get('value')
                if tipo:
                    stats_dict[tipo.lower()] = valor
            
            # CALCULAR PUNTOS FANTASY
            puntos = calcular_puntos_fantasy(stats_dict, position, clean_sheet)
            
            if is_home:
                puntos_home += puntos
            else:
                puntos_away += puntos
            
            # Imprimir
            print(f"\n{idx}. {player_name} ({position.value})")
            print(f"   {'='*70}")
            
            # Stats relevantes
            if stats_dict:
                print(f"   📊 Rating: {stats_dict.get('rating', 'N/A')}")
                
                detalles = []
                if stats_dict.get('goals', 0) > 0:
                    detalles.append(f"⚽ Goles: {stats_dict['goals']}")
                if stats_dict.get('assists', 0) > 0:
                    detalles.append(f"🎯 Asistencias: {stats_dict['assists']}")
                if stats_dict.get('yellowcards', 0) > 0:
                    detalles.append(f"🟨 Amarillas: {stats_dict['yellowcards']}")
                if stats_dict.get('redcards', 0) > 0:
                    detalles.append(f"🟥 Rojas: {stats_dict['redcards']}")
                if clean_sheet:
                    detalles.append(f"🧤 Clean Sheet")
                
                if detalles:
                    print(f"   {' | '.join(detalles)}")
            
            print(f"\n   ⚡ PUNTOS FANTASY: {puntos} puntos")
        
        print(f"\n" + "="*80)
        print(f"📊 RESUMEN (Primeros 10 jugadores):")
        print(f"   {home_team.get('name', 'Home')}: {puntos_home} puntos")
        print(f"   {away_team.get('name', 'Away')}: {puntos_away} puntos")
        print("="*80)
        
    else:
        print(f"\n❌ Error {response.status_code}: {response.text[:500]}")

if __name__ == "__main__":
    obtener_estadisticas_partido()
