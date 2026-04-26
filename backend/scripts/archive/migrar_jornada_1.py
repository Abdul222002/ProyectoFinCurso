"""
MIGRACIÓN JORNADA 1 COMPLETA - Scottish Premiership 2024/25
Procesa los 5 partidos de la jornada 1 usando IDs conocidos
"""

import os
import sys
import requests
from dotenv import load_dotenv
from enum import Enum
import math

load_dotenv()

# Añadir path para importar
sys.path.append(os.path.dirname(__file__))

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')

# IDs DE LOS 5 PARTIDOS DE LA JORNADA 1
FIXTURES_JORNADA_1 = [
    19428039,  # Kilmarnock vs Livingston
    19428040,  # Motherwell vs Rangers
    19428041,  # Falkirk vs Dundee United
    19428042,  # Dundee vs Hibernian
    19428043,  # Celtic vs St. Mirren
]

class Position(Enum):
    GK = "Portero"
    DEF = "Defensa"
    MID = "Mediocentro"
    FWD = "Delantero"

# Importar funciones del sistema oficial
from sistema_puntos_oficial import (
    extract_stats,
    calcular_puntos_fantasy_oficial,
    mapear_posicion
)

def procesar_partido(fixture_id):
    """Procesa un partido completo y devuelve estadísticas de jugadores"""
    
    url = f"https://api.sportmonks.com/v3/football/fixtures/{fixture_id}"
    params = {
        "api_token": API_TOKEN,
        "include": "lineups.details.type;participants;scores"
    }
    
    print(f"\n🔄 Procesando fixture {fixture_id}...", end=" ")
    
    response = requests.get(url, params=params, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Error {response.status_code}")
        return []
    
    data = response.json().get('data', {})
    lineups = data.get('lineups', [])
    participants = data.get('participants', [])
    scores = data.get('scores', [])
    state = data.get('state', {}).get('state', 'N/A')
    
    # Info del partido
    home_team = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
    away_team = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
    
    home_score = next((s['score']['goals'] for s in scores 
                      if s['description'] == 'CURRENT' and s['participant_id'] == home_team.get('id')), 0)
    away_score = next((s['score']['goals'] for s in scores 
                      if s['description'] == 'CURRENT' and s['participant_id'] == away_team.get('id')), 0)
    
    nombre_partido = f"{home_team.get('name', 'Home')} {home_score}-{away_score} {away_team.get('name', 'Away')}"
    
    if not lineups:
        print(f"⚠️  Sin lineups - {nombre_partido} ({state})")
        return []
    
    print(f"✅ {nombre_partido} ({state})")
    
    jugadores_procesados = []
    
    for player_entry in lineups:
        player_name = player_entry.get('player_name', 'N/A')
        player_id = player_entry.get('player_id')
        type_id = player_entry.get('type_id')
        participant_id = player_entry.get('participant_id')
        
        if not player_id:
            continue
        
        position = mapear_posicion(type_id)
        
        # Determinar clean sheet
        is_home = participant_id == home_team.get('id')
        clean_sheet = False
        if position in [Position.GK, Position.DEF]:
            clean_sheet = (away_score == 0) if is_home else (home_score == 0)
        
        # Extraer stats
        stats = extract_stats(player_entry)
        
        # Solo procesar jugadores que jugaron
        if stats['minutes_played'] > 0:
            # Calcular puntos
            fantasy_points = calcular_puntos_fantasy_oficial(stats, position, clean_sheet)
            
            jugadores_procesados.append({
                'fixture_id': fixture_id,
                'player_id': player_id,
                'player_name': player_name,
                'team': home_team.get('name') if is_home else away_team.get('name'),
                'position': position.value,
                'stats': stats,
                'fantasy_points': fantasy_points,
                'clean_sheet': clean_sheet
            })
    
    print(f"   → {len(jugadores_procesados)} jugadores procesados")
    
    return jugadores_procesados

def migrar_jornada_1_completa():
    """Proceso completo de migración de la jornada 1"""
    
    print("\n" + "="*100)
    print("📅 MIGRACIÓN JORNADA 1 COMPLETA - Scottish Premiership 2024/25")
    print("="*100)
    
    print(f"\n🎯 Partidos a procesar: {len(FIXTURES_JORNADA_1)}")
    print("   - Kilmarnock vs Livingston")
    print("   - Motherwell vs Rangers")
    print("   - Falkirk vs Dundee United")
    print("   - Dundee vs Hibernian")
    print("   - Celtic vs St. Mirren")
    
    # Procesar todos los fixtures
    todos_jugadores = []
    
    for fixture_id in FIXTURES_JORNADA_1:
        jugadores = procesar_partido(fixture_id)
        todos_jugadores.extend(jugadores)
    
    # Resumen final
    print("\n" + "="*100)
    print("📊 RESUMEN JORNADA 1")
    print("="*100 + "\n")
    
    print(f"✅ Total jugadores procesados: {len(todos_jugadores)}")
    
    # Top 20 puntuadores
    if todos_jugadores:
        todos_jugadores.sort(key=lambda x: x['fantasy_points'], reverse=True)
        
        print(f"\n🏆 TOP 20 JUGADORES DE LA JORNADA:\n")
        print(f"{'#':<3} | {'JUGADOR':<25} | {'EQUIPO':<20} | {'POS':<10} | {'MIN':<3} | {'GOL':<3} | {'AST':<3} | {'PUNTOS'}")
        print("-" * 120)
        
        for idx, jugador in enumerate(todos_jugadores[:20], 1):
            stats = jugador['stats']
            print(f"{idx:<3} | {jugador['player_name']:<25} | {jugador['team']:<20} | "
                  f"{jugador['position']:<10} | {stats['minutes_played']:<3} | "
                  f"{stats['goals']:<3} | {stats['assists']:<3} | {jugador['fantasy_points']}")
        
        # Estadísticas
        total_puntos = sum(j['fantasy_points'] for j in todos_jugadores)
        promedio = total_puntos / len(todos_jugadores) if todos_jugadores else 0
        
        print(f"\n📈 ESTADÍSTICAS GENERALES:")
        print(f"   - Puntos totales: {total_puntos}")
        print(f"   - Promedio por jugador: {promedio:.2f}")
        print(f"   - Puntos máximos: {todos_jugadores[0]['fantasy_points']} ({todos_jugadores[0]['player_name']})")
        print(f"   - Puntos mínimos: {todos_jugadores[-1]['fantasy_points']} ({todos_jugadores[-1]['player_name']})")
    
    print("\n" + "="*100)
    print("✅ MIGRACIÓN COMPLETADA")
    print("="*100 + "\n")
    
    # Guardar resultados en archivo
    output_file = "jornada_1_resultados.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*120 + "\n")
        f.write("📊 JORNADA 1 - RESULTADOS COMPLETOS\n")
        f.write("="*120 + "\n\n")
        
        f.write(f"Total jugadores procesados: {len(todos_jugadores)}\n\n")
        
        f.write("🏆 CLASIFICACIÓN COMPLETA:\n\n")
        f.write(f"{'#':<4} | {'JUGADOR':<30} | {'EQUIPO':<20} | {'POS':<10} | {'MIN':<3} | {'GOL':<3} | {'AST':<3} | {'NOTA':<5} | {'PTS'}\n")
        f.write("-" * 120 + "\n")
        
        for idx, jugador in enumerate(todos_jugadores, 1):
            stats = jugador['stats']
            rating = stats.get('rating', 0)
            f.write(f"{idx:<4} | {jugador['player_name']:<30} | {jugador['team']:<20} | "
                   f"{jugador['position']:<10} | {stats['minutes_played']:<3} | "
                   f"{stats['goals']:<3} | {stats['assists']:<3} | {rating:<5.1f} | {jugador['fantasy_points']}\n")
        
        if todos_jugadores:
            total_puntos = sum(j['fantasy_points'] for j in todos_jugadores)
            promedio = total_puntos / len(todos_jugadores)
            
            f.write(f"\n{'='*120}\n")
            f.write(f"📈 ESTADÍSTICAS:\n")
            f.write(f"   - Puntos totales: {total_puntos}\n")
            f.write(f"   - Promedio: {promedio:.2f}\n")
            f.write(f"   - Máximo: {todos_jugadores[0]['fantasy_points']} ({todos_jugadores[0]['player_name']})\n")
            f.write(f"   - Mínimo: {todos_jugadores[-1]['fantasy_points']} ({todos_jugadores[-1]['player_name']})\n")
    
    print(f"📄 Resultados completos guardados en: {output_file}\n")
    
    return todos_jugadores

if __name__ == "__main__":
    jugadores = migrar_jornada_1_completa()
