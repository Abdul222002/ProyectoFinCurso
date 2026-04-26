"""
DEBUG: Ver desglose exacto de puntos de jugadores específicos
"""

import os
import sys
import requests
from dotenv import load_dotenv
import math

# Redirigir output a archivo
output_file = open("debug_puntos.txt", "w", encoding="utf-8")
sys.stdout = output_file

load_dotenv()
sys.path.append(os.path.dirname(__file__))

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')

from sistema_puntos_oficial import extract_stats, mapear_posicion, Position

# Fixture de Hibernian (Kieron Bowie)
FIXTURE_HIBERNIAN = 19428042

# Fixture de Dundee United (Panutche Camara)
FIXTURE_DUNDEE_UNITED = 19428041

# Fixture de Livingston (George Stanger)
FIXTURE_LIVINGSTON = 19428039

def debug_jugador(fixture_id, nombre_buscar):
    """Debug detallado de un jugador específico"""
    
    url = f"https://api.sportmonks.com/v3/football/fixtures/{fixture_id}"
    params = {
        "api_token": API_TOKEN,
        "include": "lineups.details.type;scores;participants"
    }
    
    response = requests.get(url, params=params, timeout=30)
    data = response.json().get('data', {})
    lineups = data.get('lineups', [])
    participants = data.get('participants', [])
    scores = data.get('scores', [])
    
    # Buscar jugador
    for player_entry in lineups:
        if nombre_buscar.lower() in player_entry.get('player_name', '').lower():
            
            player_name = player_entry.get('player_name')
            type_id = player_entry.get('type_id')
            participant_id = player_entry.get('participant_id')
            
            position = mapear_posicion(type_id)
            
            # Determinar clean sheet
            home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
            away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
            
            home_score = next((s['score']['goals'] for s in scores 
                              if s['description'] == 'CURRENT' and s['participant_id'] == home_team.get('id')), 0)
            away_score = next((s['score']['goals'] for s in scores 
                              if s['description'] == 'CURRENT' and s['participant_id'] == away_team.get('id')), 0)
            
            is_home = participant_id == home_team.get('id')
            clean_sheet = False
            if position in [Position.GK, Position.DEF]:
                clean_sheet = (away_score == 0) if is_home else (home_score == 0)
            
            # Extraer stats
            stats = extract_stats(player_entry)
            
            print(f"\n{'='*100}")
            print(f"🔍 DEBUG: {player_name}")
            print(f"{'='*100}\n")
            
            print(f"Posición: {position.value}")
            print(f"Clean sheet: {clean_sheet}\n")
            
            print("📊 TODAS LAS STATS:")
            print("-" * 100)
            for key, value in stats.items():
                if value and value != 0:
                    print(f"  {key:<25} = {value}")
            
            # CALCULAR PUNTOS PASO A PASO
            print(f"\n{'='*100}")
            print("🧮 CÁLCULO DE PUNTOS DETALLADO")
            print(f"{'='*100}\n")
            
            puntos = 0
            
            # 1. Minutos
            if stats['minutes_played'] >= 60:
                pts = 2
                print(f"✅ Minutos (>= 60): {stats['minutes_played']} → +{pts} pts")
                puntos += pts
            elif stats['minutes_played'] > 0:
                pts = 1
                print(f"✅ Minutos (< 60): {stats['minutes_played']} → +{pts} pt")
                puntos += pts
            
            # 2. Goles
            if stats['goals'] > 0:
                pts = stats['goals'] * 4  # FWD
                print(f"⚽ Goles: {stats['goals']} × 4 (delantero) → +{pts} pts")
                puntos += pts
            
            # 3. Asistencias
            if stats['assists'] > 0:
                pts = stats['assists'] * 3
                print(f"🎯 Asistencias de gol: {stats['assists']} × 3 → +{pts} pts")
                puntos += pts
            
            if stats.get('chances_created', 0) > 0:
                pts = stats['chances_created'] * 1
                print(f"🎯 Ocasiones creadas: {stats['chances_created']} × 1 → +{pts} pts")
                puntos += pts
            
            # 4. Nota
            if stats['rating']:
                rating = stats['rating']
                if rating >= 8.5:
                    pts = 4
                elif rating >= 5.0:
                    pts = round((rating - 5.0) * (4.0 / 3.5))
                else:
                    pts = 0
                print(f"📝 Nota del partido: {rating} → +{pts} pts")
                puntos += pts
            
            # 5. Tarjetas
            if stats['yellow_cards'] > 0:
                pts = stats['yellow_cards'] * -1
                print(f"🟨 Tarjetas amarillas: {stats['yellow_cards']} → {pts} pts")
                puntos += pts
            
            if stats['red_cards'] > 0:
                pts = stats['red_cards'] * -3
                print(f"🟥 TARJETAS ROJAS: {stats['red_cards']} → {pts} pts")
                puntos += pts
            
            # 6. Goles recibidos
            goles_recibidos = stats.get('goals_conceded_team', 0)
            if goles_recibidos > 0:
                pts = -math.floor(goles_recibidos / 2) * 1  # FWD
                if pts != 0:
                    print(f"⚠️  Goles recibidos (equipo): {goles_recibidos} ÷ 2 → {pts} pts")
                    puntos += pts
            
            # 7-11. Acumuladores
            print(f"\n📈 BONOS ACUMULADORES:")
            
            # Tiros
            if stats.get('shots_on_target', 0) > 0:
                pts = math.floor(stats['shots_on_target'] / 2)
                if pts > 0:
                    print(f"  Tiros a puerta: {stats['shots_on_target']} ÷ 2 → +{pts} pts")
                    puntos += pts
            
            # Regates
            if stats.get('dribbles', 0) > 0:
                pts = math.floor(stats['dribbles'] / 2)
                if pts > 0:
                    print(f"  Regates: {stats['dribbles']} ÷ 2 → +{pts} pts")
                    puntos += pts
            
            # Cruces
            if stats.get('crosses', 0) > 0:
                pts = math.floor(stats['crosses'] / 2)
                if pts > 0:
                    print(f"  Cruces: {stats['crosses']} ÷ 2 → +{pts} pts")
                    puntos += pts
            
            # Recuperaciones
            if stats.get('ball_recoveries', 0) > 0:
                pts = math.floor(stats['ball_recoveries'] / 5)
                if pts > 0:
                    print(f"  Recuperaciones: {stats['ball_recoveries']} ÷ 5 → +{pts} pts")
                    puntos += pts
            
            # Despejes
            if stats.get('clearances', 0) > 0:
                pts = math.floor(stats['clearances'] / 3)
                if pts > 0:
                    print(f"  Despejes: {stats['clearances']} ÷ 3 → +{pts} pts")
                    puntos += pts
            
            # Tackles
            if stats.get('tackles', 0) > 0:
                pts = math.floor(stats['tackles'] / 3)
                if pts > 0:
                    print(f"  Tackles: {stats['tackles']} ÷ 3 → +{pts} pts")
                    puntos += pts
            
            # Intercepciones
            if stats.get('interceptions', 0) > 0:
                pts = math.floor(stats['interceptions'] / 3)
                if pts > 0:
                    print(f"  Intercepciones: {stats['interceptions']} ÷ 3 → +{pts} pts")
                    puntos += pts
            
            # Duelos ganados
            if stats.get('duels_won', 0) > 0:
                pts = math.floor(stats['duels_won'] / 4)
                if pts > 0:
                    print(f"  Duelos ganados: {stats['duels_won']} ÷ 4 → +{pts} pts")
                    puntos += pts
            
            # Pases precisos
            if stats.get('accurate_passes', 0) > 0:
                pts = math.floor(stats['accurate_passes'] / 15)
                if pts > 0:
                    print(f"  Pases precisos: {stats['accurate_passes']} ÷ 15 → +{pts} pts")
                    puntos += pts
            
            # Faltas
            if stats.get('fouls', 0) > 0:
                pts = -math.floor(stats['fouls'] / 3)
                if pts != 0:
                    print(f"  Faltas: {stats['fouls']} ÷ 3 → {pts} pts")
                    puntos += pts
            
            # Pérdidas
            total_losses = stats.get('total_losses', 0)
            if total_losses > 0:
                pts = -math.floor(total_losses / 12)  # FWD
                if pts != 0:
                    print(f"  Pérdidas: {total_losses} ÷ 12 → {pts} pts")
                    puntos += pts
            
            print(f"\n{'='*100}")
            print(f"🎯 TOTAL: {puntos} PUNTOS")
            print(f"{'='*100}\n")
            
            return

print("\n" + "="*100)
print("🔍 ANÁLISIS DE CASOS PROBLEMÁTICOS")
print("="*100)

print("\n1️⃣  PANUTCHE CAMARA (19 pts con 1 asistencia):")
debug_jugador(FIXTURE_DUNDEE_UNITED, "Panutche Camara")

print("\n2️⃣  KIERON BOWIE (14 pts con 2 goles):")
debug_jugador(FIXTURE_HIBERNIAN, "Kieron Bowie")

print("\n3️⃣  GEORGE STANGER (4 pts con expulsión):")
debug_jugador(FIXTURE_LIVINGSTON, "George Stanger")

output_file.close()
sys.stdout = sys.__stdout__
print("\n✅ Debug guardado en: debug_puntos.txt")
