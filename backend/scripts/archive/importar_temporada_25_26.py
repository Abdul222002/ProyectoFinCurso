"""
Script masivo para importar partidos, gameweeks y estadísticas
de la temporada 2025/2026 hasta la fecha actual (10/02/2026)
"""

import sys
import os
import requests
from datetime import datetime, timedelta
# from dateutil.relativedelta import relativedelta

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

# Equipos escoceses para filtrar (por si acaso)
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

def get_fixtures_in_range(start_str, end_str):
    """Obtiene fixtures en un rango de fechas"""
    url = f"https://api.sportmonks.com/v3/football/fixtures/between/{start_str}/{end_str}"
    params = {
        'api_token': API_TOKEN,
        'include': 'participants,scores,round,lineups',
        # 'leagues': 501  # Eliminamos esto por si causa problemas
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 404:
            print(f"⚠️  404 Not Found for {start_str} to {end_str} (No fixtures?)")
            return []
            
        response.raise_for_status()
        return response.json().get('data', [])
    except Exception as e:
        logger.error(f"Error fetching fixtures {start_str} to {end_str}: {e}")
        return []

def process_stats_for_match(db, match, fixture, scoring_engine):
    """Procesa estadísticas para un partido"""
    
    # Borramos stats existentes para evitar duplicados/errores
    # synchronize_session=False is critical here
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
            # Crear jugador si no existe
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
            red_cards=final_stats.red_cards
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
    print("🚀 INICIANDO IMPORTACIÓN MASIVA TEMPORADA 25/26")
    db = next(get_db())
    scor_config = ScoringConfig()
    engine = FantasyScoringEngine(scor_config)
    
    # 1. Iterar por INTERVALOS CORTOS (7 días) para evitar limites de API
    current_date = datetime.strptime(START_DATE, "%Y-%m-%d")
    final_date = datetime.strptime(END_DATE, "%Y-%m-%d")
    
    all_fixtures = []
    
    while current_date < final_date:
        next_date = current_date + timedelta(days=7)
        if next_date > final_date:
            next_date = final_date
            
        start_str = current_date.strftime("%Y-%m-%d")
        end_str = next_date.strftime("%Y-%m-%d")
        
        print(f"📅 Fetching {start_str} to {end_str}...")
        fixtures = get_fixtures_in_range(start_str, end_str)
        if fixtures:
            print(f"   ✅ Found {len(fixtures)} fixtures")
            all_fixtures.extend(fixtures)
            
        current_date = next_date + timedelta(days=1) # Siguiente dia para no solapar? O mismo dia?
        # "between" dates are inclusive. If we do 1-7, then 8-14. 
        # So next loop should start at next_date + 1 day?
        # Actually API logic usually handles overlapping start/end fine or we might get duplicates.
        # Let's do current_date = next_date (start next batch where previous left off).
        # But if inclusive, we get duplicates.
        # Let's do next_date + 1 day for start.
        # start: 2025-08-01, end: 2025-08-08
        # next start: 2025-08-09
            
    print(f"✅ Total fixtures encontrados: {len(all_fixtures)}")
    
    # 2. Agrupar por Gameweek (Round)
    fixtures_by_round = {}
    for fix in all_fixtures:
        round_data = fix.get('round', {})
        round_name = round_data.get('name')
        
        try:
            gw_num = int(round_name)
        except:
            continue
            
        if gw_num not in fixtures_by_round:
            fixtures_by_round[gw_num] = []
        fixtures_by_round[gw_num].append(fix)
        
    # 3. Procesar Gameweeks
    for gw_num in sorted(fixtures_by_round.keys()):
        fixtures = fixtures_by_round[gw_num]
        
        dates = [datetime.strptime(f['starting_at'], "%Y-%m-%d %H:%M:%S") for f in fixtures if f.get('starting_at')]
        if not dates: continue
        
        start_gw = min(dates)
        end_gw = max(dates)
        
        gw = db.query(Gameweek).filter(Gameweek.number == gw_num).first()
        if not gw:
            gw = Gameweek(
                number=gw_num,
                start_date=start_gw,
                end_date=end_gw,
                is_active=False,
                is_finished=(end_gw < datetime.now())
            )
            db.add(gw)
            print(f"✨ Created Gameweek {gw_num}")
        else:
            # Actualizar fechas si estaban mal (2024)
            if gw.start_date.year == 2024:
                gw.start_date = start_gw
                gw.end_date = end_gw
                gw.is_finished = (end_gw < datetime.now())
                print(f"🔄 Updated Gameweek {gw_num} dates to 2025/26")
        
        db.flush()
        
        # 4. Procesar Partidos
        print(f"  ⚽ Processing {len(fixtures)} matches for GW {gw_num}...")
        for fix in fixtures:
            fix_id = fix.get('id')
            
            participants = fix.get('participants', [])
            home = next((p for p in participants if p['meta']['location'] == 'home'), {})
            away = next((p for p in participants if p['meta']['location'] == 'away'), {})
            
            home_name = home.get('name')
            away_name = away.get('name')
            
            if not es_equipo_escoces(home_name): continue
            
            scores = fix.get('scores', [])
            home_score = next((s['score']['goals'] for s in scores if s['description'] == 'CURRENT' and s['participant_id'] == home['id']), 0)
            away_score = next((s['score']['goals'] for s in scores if s['description'] == 'CURRENT' and s['participant_id'] == away['id']), 0)
            
            kickoff = datetime.strptime(fix['starting_at'], "%Y-%m-%d %H:%M:%S")
            
            match = db.query(Match).filter(Match.sportmonks_id == fix_id).first()
            
            if not match:
                # Check for existing match to update (fix 2024 date issue)
                match = db.query(Match).filter(
                    Match.gameweek_id == gw.id,
                    Match.home_team == home_name,
                    Match.away_team == away_name
                ).first()
                if match:
                    match.sportmonks_id = fix_id

            # Enum handling
            status = MatchStatus.SCHEDULED
            if fix.get('finished') or kickoff < datetime.now():
                status = MatchStatus.FINISHED

            if not match:
                match = Match(
                    sportmonks_id=fix_id,
                    gameweek_id=gw.id,
                    home_team=home_name,
                    away_team=away_name,
                    home_score=home_score,
                    away_score=away_score,
                    status=status,
                    kickoff_time=kickoff
                )
                db.add(match)
                db.flush()
            else:
                match.kickoff_time = kickoff
                match.home_score = home_score
                match.away_score = away_score
                match.status = status
                if match.sportmonks_id != fix_id:
                     match.sportmonks_id = fix_id
            
            # 5. Stats
            if status == MatchStatus.FINISHED and (home_score is not None):
                 process_stats_for_match(db, match, fix, engine)
        
        db.commit()
    
    # Sincronizar backup
    print("🔄 Syncing matches_backup...")
    db.execute(text("TRUNCATE TABLE matches_backup"))
    db.execute(text("INSERT INTO matches_backup SELECT * FROM matches"))
    db.commit()
    
    print("✅ IMPORTACIÓN COMPLETADA")

if __name__ == "__main__":
    main()
