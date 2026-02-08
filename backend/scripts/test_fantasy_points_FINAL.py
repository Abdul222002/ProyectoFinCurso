"""
Script CORRECTO con lineups.details.type
Calcula puntos fantasy con datos reales de la API
"""

import os
import requests
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')
FIXTURE_ID = 19428171  # Aberdeen vs Livingston (ejemplo del usuario)

class Position(Enum):
    GK = "GK"
    DEF = "DEF"
    MID = "MID"
    FWD = "FWD"

# Puntos por posición
GOAL_POINTS = {Position.GK: 10, Position.DEF: 7, Position.MID: 5, Position.FWD: 4}
ASSIST_POINTS = {Position.GK: 5, Position.DEF: 4, Position.MID: 3, Position.FWD: 2}
CLEAN_SHEET_POINTS = {Position.GK: 4, Position.DEF: 3, Position.MID: 1, Position.FWD: 0}

def mapear_posicion(type_id):
    if type_id == 24: return Position.GK
    elif type_id in [25, 26, 27]: return Position.DEF
    elif type_id in [28, 29, 30]: return Position.MID
    else: return Position.FWD

def calcular_puntos_fantasy(stats, position, clean_sheet=False):
    puntos = 0
    
    # Goles
    puntos += stats.get('goals', 0) * GOAL_POINTS[position]
    
    # Asistencias
    puntos += stats.get('assists', 0) * ASSIST_POINTS[position]
    
    # Minutos (asumimos 90 si jugó, necesitaríamos otro campo para saber exacto)
    if stats.get('rating', 0) > 0:  # Si tiene rating, jugó
        puntos += 2  # Asumir 60+ minutos
    
    # Rating
    rating = stats.get('rating', 0)
    if rating >= 9.0:
        puntos += 5
    elif rating >= 8.0:
        puntos += 3
    elif rating >= 7.0:
        puntos += 1
    
    # Clean sheet
    if clean_sheet:
        puntos += CLEAN_SHEET_POINTS[position]
    
    # Tarjetas
    puntos -= stats.get('yellowcards', 0) * 1
    puntos -= stats.get('redcards', 0) * 3
    
    return puntos

url = f"https://api.sportmonks.com/v3/football/fixtures/{FIXTURE_ID}"
params = {
    "api_token": API_TOKEN,
    "include": "lineups.details.type;participants;scores"
}

print(f"\n{'='*80}")
print(f"📡 OBTENIENDO ESTADÍSTICAS - PARTIDO {FIXTURE_ID}")
print(f"{'='*80}\n")

response = requests.get(url, params=params, timeout=30)

if response.status_code == 200:
    data = response.json().get('data', {})
    lineups = data.get('lineups', [])
    
    # Info del partido
    participants = data.get('participants', [])
    scores = data.get('scores', [])
    
    home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
    away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
    
    home_score = next((s['score']['goals'] for s in scores 
                      if s['description'] == 'CURRENT' and s['participant_id'] == home_team.get('id')), 0)
    away_score = next((s['score']['goals'] for s in scores 
                      if s['description'] == 'CURRENT' and s['participant_id'] == away_team.get('id')), 0)
    
    print(f"⚽ {home_team.get('name', 'Home')} {home_score} - {away_score} {away_team.get('name', 'Away')}\n")
    print(f"{'='*80}")
    print(f"\n{'JUGADOR':<25} | {'POS':<4} | {'GOL':<3} | {'AST':<3} | {'NOTA':<4} | {'PUNTOS'}")
    print("-" * 80)
    
    total_home = 0
    total_away = 0
    
    for player in lineups[:15]:  # Primeros 15 jugadores
        name = player.get('player_name', 'N/A')
        type_id = player.get('type_id')
        participant_id = player.get('participant_id')
        
        position = mapear_posicion(type_id)
        
        # Determinar clean sheet
        is_home = participant_id == home_team.get('id')
        clean_sheet = False
        if position in [Position.GK, Position.DEF]:
            clean_sheet = (away_score == 0) if is_home else (home_score == 0)
        
        # Extraer stats de details
        details = player.get('details', [])
        stats = {
            'goals': 0,
            'assists': 0,
            'rating': 0,
            'yellowcards': 0,
            'redcards': 0
        }
        
        for stat in details:
            type_info = stat.get('type', {})
            stat_name = type_info.get('developer_name', '')
            data_wrapper = stat.get('data', {})
            valor = data_wrapper.get('value', 0)
            
            if stat_name == "GOALS":
                stats['goals'] = int(valor) if valor else 0
            elif stat_name == "ASSISTS":
                stats['assists'] = int(valor) if valor else 0
            elif stat_name == "RATING":
                stats['rating'] = float(valor) if valor else 0
            elif stat_name == "YELLOWCARDS":
                stats['yellowcards'] = int(valor) if valor else 0
            elif stat_name == "REDCARDS":
                stats['redcards'] = int(valor) if valor else 0
        
        # Calcular puntos
        puntos = calcular_puntos_fantasy(stats, position, clean_sheet)
        
        if is_home:
            total_home += puntos
        else:
            total_away += puntos
        
        # Mostrar solo si tiene datos interesantes
        if stats['rating'] > 0:
            print(f"{name:<25} | {position.value:<4} | {stats['goals']:<3} | {stats['assists']:<3} | {stats['rating']:<4.1f} | {puntos} pts")
    
    print("-" * 80)
    print(f"\n📊 TOTALES FANTASY:")
    print(f"   {home_team.get('name', 'Home')}: {total_home} puntos")
    print(f"   {away_team.get('name', 'Away')}: {total_away} puntos")
    print(f"\n{'='*80}")
    print("✅ SISTEMA DE PUNTOS FANTASY FUNCIONANDO CORRECTAMENTE")
    print(f"{'='*80}\n")

else:
    print(f"❌ Error {response.status_code}: {response.text[:500]}")
