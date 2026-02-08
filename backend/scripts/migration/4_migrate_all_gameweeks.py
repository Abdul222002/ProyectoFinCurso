"""
PASO 4: Migrar Todas las Jornadas
Migra todas las jornadas disponibles jornada por jornada
"""

import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.database import get_db
from app.models.models import (
    Gameweek,
    Match,
    Player,
    PlayerMatchStats,
    MatchStatus
)
from scripts.sistema_puntos_oficial import (
    FantasyScoringEngine,
    SportmonksAPIClient,
    StatsExtractor,
    API_TOKEN,
    logger
)
from dataclasses import dataclass


@dataclass
class BalancedScoringConfig:
    """Configuración balanceada"""
    #  Minutos y participación
    minutes_full_game: int = 90
    minutes_clean_sheet_threshold: int = 60
    points_full_game: int = 2
    points_partial_game: int = 1
    
    # Goles
    goals_gk_def: int = 10
    goals_mid: int = 7
    goals_fwd: int = 6
    
    # Asistencias
    assist_goal: int = 5
    assist_chance: int = 2
    
    # Clean sheet
    clean_sheet_gk: int = 5
    clean_sheet_def: int = 4
    clean_sheet_mid: int = 2
    clean_sheet_fwd: int = 1
    
    # Acumuladores
    shots_on_target_per_point: int = 4
    dribbles_per_point: int = 5
    crosses_per_point: int = 4
    ball_recoveries_per_point: int = 10
    clearances_per_point: int = 6
    tackles_per_point: int = 8
    interceptions_per_point: int = 8
    duels_won_per_point: int = 10
    accurate_passes_per_point: int = 50
    
    # Penalizaciones
    yellow_card_penalty: int = -2
    red_card_penalty: int = -5
    goals_conceded_penalty_gk_def: int = -3
    goals_conceded_penalty_mid_fwd: int = -1
    goals_conceded_per_penalty: int = 2
    fouls_per_penalty: int = 2
    losses_gk_def_threshold: int = 6
    losses_mid_threshold: int = 8
    losses_fwd_threshold: int = 10
    
    # Rating
    rating_max_points: int = 4
    rating_min_threshold: float = 5.0
    rating_max_threshold: float = 8.0
    
    # Portero
    saves_per_point: int = 3
    
    # Penaltis
    penalty_save_bonus: int = 5
    penalty_miss_penalty: int = -3
    penalty_won_bonus: int = 2
    penalty_committed_penalty: int = -2


# Fixtures por jornada (6 partidos por jornada - Scottish Premiership tiene 12 equipos)
FIXTURES_BY_GAMEWEEK = {
    1: [19428038, 19428039, 19428040, 19428041, 19428042, 19428043],  # 6 partidos
    2: [19428044, 19428045, 19428046, 19428047, 19428048, 19428054],  # 6 partidos
    3: [19428049, 19428050, 19428051, 19428052, 19428053, 19428055],  # 6 partidos
}


def migrate_gameweek(gameweek_number):
    """Migra una jornada específica"""
    
    if gameweek_number not in FIXTURES_BY_GAMEWEEK:
        print(f"❌ Jornada {gameweek_number} no tiene fixtures definidos")
        return False
    
    if not API_TOKEN:
        print("❌ API_TOKEN no configurada")
        return False
    
    api_client = SportmonksAPIClient(API_TOKEN)
    scoring_engine = FantasyScoringEngine(BalancedScoringConfig())
    db = next(get_db())
    
    try:
        # Obtener jornada de BD
        gameweek = db.query(Gameweek).filter(
            Gameweek.number == gameweek_number
        ).first()
        
        if not gameweek:
            print(f"❌ Jornada {gameweek_number} no existe en la BD")
            return False
        
        print(f"\n⚽ Migrando Jornada {gameweek_number}...\n")
        
        fixtures = FIXTURES_BY_GAMEWEEK[gameweek_number]
        players_saved = 0
        matches_saved = 0
        
        for fixture_id in fixtures:
            # Obtener datos
            fixture_data = api_client.get_fixture(fixture_id)
            if not fixture_data:
                print(f"  ❌ No se pudo obtener fixture {fixture_id}")
                continue
            
            lineups = fixture_data.get('lineups', [])
            participants = fixture_data.get('participants', [])
            scores = fixture_data.get('scores', [])
            
            home_team = next((p for p in participants 
                             if p.get('meta', {}).get('location') == 'home'), {})
            away_team = next((p for p in participants 
                             if p.get('meta', {}).get('location') == 'away'), {})
            
            home_score = next((s['score']['goals'] for s in scores 
                              if s['description'] == 'CURRENT' 
                              and s['participant_id'] == home_team.get('id')), 0)
            away_score = next((s['score']['goals'] for s in scores 
                              if s['description'] == 'CURRENT' 
                              and s['participant_id'] == away_team.get('id')), 0)
            
            # Crear Match
            match = Match(
                sportmonks_id=fixture_id,
                gameweek_id=gameweek.id,
                home_team=home_team.get('name', 'Home'),
                away_team=away_team.get('name', 'Away'),
                home_score=home_score,
                away_score=away_score,
                status=MatchStatus.FINISHED,
                kickoff_time=gameweek.start_date
            )
            db.add(match)
            db.flush()
            matches_saved += 1
            
            print(f"  {match.home_team} {home_score}-{away_score} {match.away_team} → ", end='')
            
            match_players = 0
            
            # Procesar jugadores
            for player_entry in lineups:
                sportmonks_id = player_entry.get('player_id')
                if not sportmonks_id:
                    continue
                
                # Determinar clean sheet
                clean_sheet = StatsExtractor.determine_clean_sheet(
                    StatsExtractor.map_position(player_entry.get('type_id')),
                    player_entry.get('participant_id'),
                    home_team.get('id'),
                    away_team.get('id'),
                    home_score,
                    away_score
                )
                
                # Extraer stats
                stats = StatsExtractor.extract_player_stats(player_entry, clean_sheet)
                
                if stats.minutes_played == 0:
                    continue
                
                # Calcular puntos
                stats = scoring_engine.calculate_points(stats)
                
                # Buscar jugador en BD
                player = db.query(Player).filter(
                    Player.sportmonks_id == sportmonks_id
                ).first()
                
                if not player:
                    print(f"\n  ⚠️  Jugador {stats.player_name} no encontrado en BD, omitiendo")
                    continue
                
                # Crear PlayerMatchStats
                player_stat = PlayerMatchStats(
                    player_id=player.id,
                    match_id=match.id,
                    minutes_played=stats.minutes_played,
                    rating=stats.rating,
                    goals=stats.goals,
                    assists=stats.assists,
                    chances_created=stats.chances_created,
                    clean_sheet=stats.clean_sheet,
                    goals_conceded=stats.goals_conceded,
                    goals_conceded_team=stats.goals_conceded_team,
                    saves=stats.saves,
                    clearances=stats.clearances,
                    yellow_cards=stats.yellow_cards,
                    red_cards=stats.red_cards,
                    shots_on_target=stats.shots_on_target,
                    dribbles=stats.dribbles,
                    crosses=stats.crosses,
                    ball_recoveries=stats.ball_recoveries,
                    dispossessed=stats.dispossessed,
                    possession_lost=stats.possession_lost,
                    turnovers=stats.turnovers,
                    total_losses=stats.total_losses,
                    accurate_passes=stats.accurate_passes,
                    tackles=stats.tackles,
                    interceptions=stats.interceptions,
                    duels_won=stats.duels_won,
                    fouls=stats.fouls,
                    penalty_miss=stats.penalty_miss,
                    penalty_save=stats.penalty_save,
                    penalty_won=stats.penalty_won,
                    penalty_committed=stats.penalty_committed,
                    fantasy_points=stats.fantasy_points
                )
                db.add(player_stat)
                
                # Actualizar acumuladores del jugador
                player.total_matches_played += 1
                player.sum_match_ratings += stats.rating
                player.sum_fantasy_points += stats.fantasy_points
                
                match_players += 1
                players_saved += 1
            
            print(f"{match_players} jugadores")
        
        # NUEVO: Agregar registros con 0 puntos para jugadores que NO jugaron
        print(f"\n📊 Agregando registros de 0 puntos para jugadores que no jugaron...")
        
        # Obtener todos los jugadores regulares (no leyendas)
        all_regular_players = db.query(Player).filter(Player.is_legend == False).all()
        
        # Obtener IDs de jugadores que ya tienen stats en esta jornada
        players_with_stats_query = db.query(PlayerMatchStats.player_id).join(
            Match, PlayerMatchStats.match_id == Match.id
        ).filter(Match.gameweek_id == gameweek.id).distinct()
        
        players_with_stats_ids = set([row[0] for row in players_with_stats_query.all()])
        
        # Crear registros de 0 puntos para los que no jugaron
        zero_points_added = 0
        
        for player in all_regular_players:
            if player.id not in players_with_stats_ids:
                # Crear registro con 0 puntos (no jugó)
                # Usar el primer partido de la jornada como referencia
                if matches_saved > 0:
                    first_match = db.query(Match).filter(
                        Match.gameweek_id == gameweek.id
                    ).first()
                    
                    if first_match:
                        zero_stat = PlayerMatchStats(
                            player_id=player.id,
                            match_id=first_match.id,
                            minutes_played=0,
                            rating=0.0,
                            goals=0,
                            assists=0,
                            chances_created=0,
                            clean_sheet=False,
                            goals_conceded=0,
                            goals_conceded_team=0,
                            saves=0,
                            clearances=0,
                            yellow_cards=0,
                            red_cards=0,
                            shots_on_target=0,
                            dribbles=0,
                            crosses=0,
                            ball_recoveries=0,
                            dispossessed=0,
                            possession_lost=0,
                            turnovers=0,
                            total_losses=0,
                            accurate_passes=0,
                            tackles=0,
                            interceptions=0,
                            duels_won=0,
                            fouls=0,
                            penalty_miss=0,
                            penalty_save=0,
                            penalty_won=0,
                            penalty_committed=0,
                            fantasy_points=0
                        )
                        db.add(zero_stat)
                        zero_points_added += 1
        
        db.commit()
        
        total_stats = players_saved + zero_points_added
        
        print(f"✅ Jornada {gameweek_number}: {matches_saved} partidos")
        print(f"   - {players_saved} jugadores con stats reales")
        print(f"   - {zero_points_added} jugadores sin jugar (0 pts)")
        print(f"   - {total_stats} stats totales guardadas")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error en jornada {gameweek_number}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def migrate_all_gameweeks():
    """Migra todas las jornadas disponibles"""
    
    print("\n" + "="*100)
    print("⚽ PASO 4: MIGRAR TODAS LAS JORNADAS")
    print("="*100 + "\n")
    
    total_gameweeks = len(FIXTURES_BY_GAMEWEEK)
    success_count = 0
    
    for gw_num in sorted(FIXTURES_BY_GAMEWEEK.keys()):
        if migrate_gameweek(gw_num):
            success_count += 1
        else:
            print(f"⚠️  Jornada {gw_num} falló, pero continuando...")
    
    print("\n" + "="*100)
    print(f"✅ MIGRACIÓN COMPLETADA: {success_count}/{total_gameweeks} jornadas")
    print("="*100 + "\n")
    
    return success_count == total_gameweeks


if __name__ == "__main__":
    migrate_all_gameweeks()
