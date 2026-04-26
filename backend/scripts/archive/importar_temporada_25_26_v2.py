"""
Script masivo para importar partidos, gameweeks y estadísticas
de la temporada 2025/2026 hasta la fecha actual (10/02/2026).
Versión 2.1: Sin 'events' en include para evitar 404.
"""

import sys
import os
import requests
import time
from datetime import datetime, timedelta

# Añadir paths necesarios
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.core.database import get_db
from app.models.models import (
    Match, Gameweek, Player, PlayerMatchStats, 
    Position as DBPosition, MatchStatus
)
from scripts.sistema_puntos_oficial import (
    FantasyScoringEngine, ScoringConfig, 
    StatsExtractor, API_TOKEN, logger
)

# Constantes
SEASON_ID = 25598
START_DATE = "2025-08-01"
END_DATE = "2026-02-10"

# Equipos escoceses para filtrar
EQUIPOS_ESCOCESES = [
    "Celtic", "Rangers", "Aberdeen", "Hearts", "Hibernian", 
    "Dundee", "Motherwell", "St. Mirren", "Kilmarnock", 
    "Ross County", "St. Johnstone", "Livingston", "Falkirk",
    "Dundee United"
]

def es_equipo_escoces(nombre):
    for clave in EQUIPOS_ESCOCESES:
        if clave in nombre:
            return True
    return False

def get_fixtures_list(start_str, end_str):
    """Obtiene lista de fixtures básica (sin includes pesados)"""
    url = f"https://api.sportmonks.com/v3/football/fixtures/between/{start_str}/{end_str}"
    params = {
        'api_token': API_TOKEN,
        'include': 'participants', # Mínimo necesario
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json().get('data', [])
    except Exception as e:
        logger.error(f"Error fetching fixtures list {start_str} to {end_str}: {e}")
        return []

def get_fixture_details(fixture_id):
    """Obtiene detalles completos de un partido"""
    url = f"https://api.sportmonks.com/v3/football/fixtures/{fixture_id}"
    
    # Intento 1: Con lineups
    params = {
        'api_token': API_TOKEN,
        'include': 'participants,scores,round,lineups' 
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('data', {})
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
             # Intento 2: Sin lineups (para salvar al menos el partido)
             # print(f" ⚠️ 404 with lineups, retrying without...")
             params['include'] = 'participants,scores,round'
             try:
                 response = requests.get(url, params=params)
                 response.raise_for_status()
                 data = response.json().get('data', {})
                 # Marcar que no tiene lineups para logica posterior
                 data['lineups'] = [] 
                 return data
             except Exception as e2:
                 logger.error(f"Error fetching basic details {fixture_id}: {e2}")
                 return None
                 
        logger.error(f"Error fetching fixture details {fixture_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching fixture details {fixture_id}: {e}")
        return None

def process_stats_for_match(db, match, fixture, scoring_engine):
    """Procesa estadísticas para un partido"""
    
    # IMPORTANTE: synchronize_session=False para evitar errores con sesiones expiradas
    db.query(PlayerMatchStats).filter(PlayerMatchStats.match_id == match.id).delete(synchronize_session=False)
    
    lineups = fixture.get('lineups', [])
    participants = fixture.get('participants', [])
    
    if not lineups:
        return 0

    scores = fixture.get('scores', [])
    
    # Identificar equipos home/away
    home_participant = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
    away_participant = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
    
    home_id = home_participant.get('id')
    away_id = away_participant.get('id')
    
    # Obtener score actual
    home_score = next((s['score']['goals'] for s in scores if s['description'] == 'CURRENT' and s['participant_id'] == home_id), 0)
    away_score = next((s['score']['goals'] for s in scores if s['description'] == 'CURRENT' and s['participant_id'] == away_id), 0)

    stats_processed = 0
    played_player_ids = set()

    # Procesar jugadores que jugaron
    for player_entry in lineups:
        position_id = player_entry.get('type_id')
        player_pos = StatsExtractor.map_position(position_id)
        
        clean_sheet = StatsExtractor.determine_clean_sheet(
            player_pos, player_entry.get('participant_id'),
            home_id, away_id, home_score, away_score
        )
        
        raw_stats = StatsExtractor.extract_player_stats(player_entry, clean_sheet)
        final_stats = scoring_engine.calculate_points(raw_stats)
        
        if final_stats.minutes_played == 0:
            continue

        # Buscar/Crear jugador
        sm_player_id = player_entry.get('player_id')
        player = db.query(Player).filter(Player.sportmonks_id == sm_player_id).first()
        
        if not player:
            team_name = match.home_team if player_entry.get('participant_id') == home_id else match.away_team
            
            db_pos = DBPosition.MID
            if final_stats.position.name == 'GK': db_pos = DBPosition.GK
            elif final_stats.position.name == 'DEF': db_pos = DBPosition.DEF
            elif final_stats.position.name == 'FWD': db_pos = DBPosition.FWD
            
            player = Player(
                name=final_stats.player_name,
                sportmonks_id=sm_player_id,
                position=db_pos,
                current_team=team_name,
                nationality="Unknown", age=25, overall_rating=70, potential=75
            )
            db.add(player)
            db.flush()
            
        played_player_ids.add(player.id)
        
        # Crear Stats
        pms = PlayerMatchStats(
            player_id=player.id,
            match_id=match.id,
            minutes_played=final_stats.minutes_played,
            rating=final_stats.rating,
            goals=final_stats.goals,
            assists=final_stats.assists,
            clean_sheet=final_stats.clean_sheet,
            fantasy_points=final_stats.fantasy_points,
            saves=final_stats.saves,
            goals_conceded=final_stats.goals_conceded,
            yellow_cards=final_stats.yellow_cards,
            red_cards=final_stats.red_cards,
        )
        db.add(pms)
        stats_processed += 1

    # Procesar jugadores que NO jugaron (Rellenar con 0s)
    all_team_players = db.query(Player).filter(
        Player.current_team.in_([match.home_team, match.away_team]),
        Player.is_legend == 0
    ).all()
    
    zeros_processed = 0
    for p in all_team_players:
        if p.id not in played_player_ids:
            pms = PlayerMatchStats(
                player_id=p.id,
                match_id=match.id,
                minutes_played=0,
                rating=0.0,
                goals=0, assists=0, fantasy_points=0,
                clean_sheet=False, saves=0, goals_conceded=0,
                yellow_cards=0, red_cards=0
            )
            db.add(pms)
            zeros_processed += 1
            
    return stats_processed + zeros_processed

def main():
    print("🚀 INICIANDO IMPORTACIÓN MASIVA TEMPORADA 25/26 (V2.1)")
    db = next(get_db())
    scor_config = ScoringConfig()
    engine = FantasyScoringEngine(scor_config)
    
    # 1. Obtener lista de partidos (ligera, sin detalles)
    current_date = datetime.strptime(START_DATE, "%Y-%m-%d")
    final_date = datetime.strptime(END_DATE, "%Y-%m-%d")
    
    all_fixtures_list = []
    
    print("📋 Recopilando lista de partidos...")
    while current_date < final_date:
        next_date = current_date + timedelta(days=7)
        if next_date > final_date: next_date = final_date
            
        start_str = current_date.strftime("%Y-%m-%d")
        end_str = next_date.strftime("%Y-%m-%d")
        
        print(f"  - {start_str} to {end_str}...", end="")
        fixtures = get_fixtures_list(start_str, end_str)
        if fixtures:
            # Filtrar escoceses AQUI
            escoceses = []
            for f in fixtures:
                p = f.get('participants', [])
                if not p: continue
                h = next((x for x in p if x['meta']['location'] == 'home'), {})
                a = next((x for x in p if x['meta']['location'] == 'away'), {})
                if es_equipo_escoces(h.get('name', '')) and es_equipo_escoces(a.get('name', '')):
                    escoceses.append(f)
            print(f" ✅ {len(escoceses)} fixtures (filtered)")
            all_fixtures_list.extend(escoceses)
        else:
            print(" ⚠️ 0 found")
            
        current_date = next_date + timedelta(days=1)
        
    print(f"\n📊 Total partidos escoceses encontrados: {len(all_fixtures_list)}")
    print("⏳ Iniciando procesamiento detallado (esto tomará unos minutos)...")
    
    gw_cache = {} 
    
    # Pre-cargar gameweeks existentes
    gws = db.query(Gameweek).all()
    gw_cache = {gw.number: gw for gw in gws}
    
    for i, fixture_basic in enumerate(all_fixtures_list):
        fix_id = fixture_basic.get('id')
        print(f"\n[{i+1}/{len(all_fixtures_list)}] Procesando Fixture {fix_id}...", end="")
        
        # 2. Detalles completos
        fixture = get_fixture_details(fix_id)
        if not fixture:
            print(" ❌ Error details")
            continue
            
        # Extraer Round (Gameweek)
        round_data = fixture.get('round', {})
        round_name = round_data.get('name')
        if not round_name:
            # Fallback: intentar stage name si round name falla? O si es None
            print(f" ⚠️ No round name found (skipping)")
            continue
            
        try:
            gw_num = int(round_name)
        except:
            print(f" ⚠️ Invalid round name: '{round_name}' (skipping)")
            continue
            
        # Gestionar Gameweek
        gw = gw_cache.get(gw_num)
        kickoff = datetime.strptime(fixture['starting_at'], "%Y-%m-%d %H:%M:%S")
        
        if not gw:
            gw = Gameweek(
                number=gw_num,
                start_date=kickoff, # Inicial, se expandirá
                end_date=kickoff,
                is_active=False,
                is_finished=False
            )
            db.add(gw)
            db.flush() # Para tener ID
            gw_cache[gw_num] = gw
            print(f" (New GW {gw_num})", end="")
        else:
            # Expandir rango fechas
            if kickoff < gw.start_date or gw.start_date.year == 2024:
                gw.start_date = kickoff
            if kickoff > gw.end_date or gw.end_date.year == 2024:
                gw.end_date = kickoff
            # Actualizar estado finished si es necesario
            gw.is_finished = (gw.end_date < datetime.now())

        # Gestionar Match
        participants = fixture.get('participants', [])
        home = next((p for p in participants if p['meta']['location'] == 'home'), {})
        away = next((p for p in participants if p['meta']['location'] == 'away'), {})
        
        home_name = home.get('name')
        away_name = away.get('name')
        
        scores = fixture.get('scores', [])
        home_score = next((s['score']['goals'] for s in scores if s['description'] == 'CURRENT' and s['participant_id'] == home['id']), 0)
        away_score = next((s['score']['goals'] for s in scores if s['description'] == 'CURRENT' and s['participant_id'] == away['id']), 0)
        
        status = MatchStatus.SCHEDULED
        if fixture.get('finished') or kickoff < datetime.now():
            status = MatchStatus.FINISHED
        
        # Upsert Match
        match = db.query(Match).filter(Match.sportmonks_id == fix_id).first()
        if not match:
             # Try finding by team/gw to fix old records (if dates were messed up)
             # But careful not to duplicate if we trust sportmonks_id
             match = db.query(Match).filter(
                 Match.gameweek_id == gw.id,
                 Match.home_team == home_name,
                 Match.away_team == away_name
             ).first()
             
        if not match:
            match = Match(
                sportmonks_id=fix_id, 
                gameweek_id=gw.id,
                home_team=home_name, away_team=away_name,
                home_score=home_score, away_score=away_score,
                status=status, kickoff_time=kickoff
            )
            db.add(match)
            db.flush() # Para ID
        else:
            match.kickoff_time = kickoff
            match.home_score = home_score
            match.away_score = away_score
            match.status = status
            match.sportmonks_id = fix_id # Update ID if matched by teams
        
        # 3. Stats
        stats_count = 0
        if status == MatchStatus.FINISHED and home_score is not None:
             stats_count = process_stats_for_match(db, match, fixture, engine)
             
        print(f" ✅ {home_name} vs {away_name} ({home_score}-{away_score}) [Stats: {stats_count}]")
        
        # Commit periódico
        if (i+1) % 10 == 0:
            db.commit()
            
    db.commit()
    
    # Sincronizar backup
    print("\n🔄 Syncing matches_backup...")
    db.execute(text("TRUNCATE TABLE matches_backup"))
    db.execute(text("INSERT INTO matches_backup SELECT * FROM matches"))
    db.commit()
    
    print("✅ IMPORTACIÓN COMPLETADA")

if __name__ == "__main__":
    main()
