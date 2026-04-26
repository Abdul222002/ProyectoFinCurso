"""
Script para recargar SOLO las estadísticas del Match 33 (St. Mirren vs Rangers)
"""

import sys
import os
from datetime import datetime

# Añadir paths necesarios
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import (
    Match,
    Player,
    PlayerMatchStats,
    Position as DBPosition
)

from scripts.sistema_puntos_oficial import (
    FantasyScoringEngine,
    ScoringConfig,
    SportmonksAPIClient,
    StatsExtractor,
    API_TOKEN,
    logger
)
from dataclasses import dataclass


@dataclass
class BalancedScoringConfig(ScoringConfig):
    """Configuración balanceada que prioriza goles y asistencias"""
    
    goals_gk_def: int = 10
    goals_mid: int = 7
    goals_fwd: int = 6
    assist_goal: int = 5
    assist_chance: int = 2
    clean_sheet_gk: int = 5
    clean_sheet_def: int = 4
    shots_on_target_per_point: int = 4
    dribbles_per_point: int = 5
    crosses_per_point: int = 4
    ball_recoveries_per_point: int = 10
    clearances_per_point: int = 6
    tackles_per_point: int = 8
    interceptions_per_point: int = 8
    duels_won_per_point: int = 10
    accurate_passes_per_point: int = 50
    yellow_card_penalty: int = -2
    red_card_penalty: int = -5
    goals_conceded_penalty_gk_def: int = -3
    fouls_per_penalty: int = 2
    losses_gk_def_threshold: int = 6
    losses_mid_threshold: int = 8
    losses_fwd_threshold: int = 10
    penalty_save_bonus: int = 5
    penalty_miss_penalty: int = -3
    penalty_won_bonus: int = 2
    penalty_committed_penalty: int = -2


def recargar_match_33():
    """Recarga las estadísticas del Match 33"""
    
    print("\n" + "="*130)
    print("🔄 RECARGA DE MATCH 33: St. Mirren vs Rangers")
    print("="*130 + "\n")
    
    if not API_TOKEN:
        logger.error("SPORTMONKS_API_KEY no está configurada")
        return
    
    db = next(get_db())
    
    try:
        # Obtener el Match 33
        match = db.query(Match).filter(Match.id == 33).first()
        
        if not match:
            print("❌ Match 33 no encontrado")
            return
        
        print(f"📋 Match 33 encontrado:")
        print(f"   ID BD: {match.id}")
        print(f"   Equipos: {match.home_team} vs {match.away_team}")
        print(f"   Sportmonks ID: {match.sportmonks_id}")
        print(f"   Resultado: {match.home_score}-{match.away_score}\n")
        
        # Borrar estadísticas existentes del Match 33
        deleted = db.query(PlayerMatchStats).filter(
            PlayerMatchStats.match_id == 33
        ).delete(synchronize_session=False)
        
        db.commit()
        print(f"🗑️  Borrados {deleted} registros antiguos\n")
        
        # Configurar sistema de puntos
        api_client = SportmonksAPIClient(API_TOKEN)
        config = BalancedScoringConfig()
        scoring_engine = FantasyScoringEngine(config)
        
        # Obtener datos del partido
        print(f"📡 Obteniendo datos de la API...\n")
        fixture_data = api_client.get_fixture(match.sportmonks_id)
        
        if not fixture_data:
            print(f"❌ No se pudieron obtener datos del fixture {match.sportmonks_id}")
            return
        
        lineups = fixture_data.get('lineups', [])
        participants = fixture_data.get('participants', [])
        
        # Info equipos
        home_team = next((p for p in participants 
                         if p.get('meta', {}).get('location') == 'home'), {})
        away_team = next((p for p in participants 
                         if p.get('meta', {}).get('location') == 'away'), {})
        
        home_score = match.home_score
        away_score = match.away_score
        
        # Procesar jugadores que JUGARON
        players_with_stats = 0
        played_player_ids = set()
        
        for player_entry in lineups:
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
            stats = scoring_engine.calculate_points(stats)
            
            if stats.minutes_played == 0:
                continue
            
            player_name = stats.player_name
            sportmonks_player_id = player_entry.get('player_id')
            
            player = db.query(Player).filter(
                Player.sportmonks_id == sportmonks_player_id
            ).first()
            
            if not player:
                player_team = match.home_team if player_entry.get('participant_id') == home_team.get('id') else match.away_team
                
                if stats.position.name == 'GK':
                    db_position = DBPosition.GK
                elif stats.position.name == 'DEF':
                    db_position = DBPosition.DEF
                elif stats.position.name == 'MID':
                    db_position = DBPosition.MID
                else:
                    db_position = DBPosition.FWD
                
                player = Player(
                    name=player_name,
                    sportmonks_id=sportmonks_player_id,
                    age=25,
                    position=db_position,
                    nationality="Scotland",
                    overall_rating=70,
                    potential=75,
                    current_team=player_team
                )
                db.add(player)
                db.flush()
            
            played_player_ids.add(player.id)
            
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
            players_with_stats += 1
        
        # Añadir jugadores que NO jugaron
        players_without_stats = 0
        
        all_home_players = db.query(Player).filter(
            Player.current_team == match.home_team,
            Player.is_legend == 0
        ).all()
        
        all_away_players = db.query(Player).filter(
            Player.current_team == match.away_team,
            Player.is_legend == 0
        ).all()
        
        for player in all_home_players + all_away_players:
            if player.id not in played_player_ids:
                player_stat = PlayerMatchStats(
                    player_id=player.id,
                    match_id=match.id,
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
                    shots_total=0,
                    accurate_passes=0,
                    total_passes=0,
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
                db.add(player_stat)
                players_without_stats += 1
        
        db.commit()
        
        print(f"✅ Jugadores con stats (API): {players_with_stats}")
        print(f"✅ Jugadores sin minutos (0s): {players_without_stats}")
        print(f"✅ Total guardados: {players_with_stats + players_without_stats}\n")
        
        print(f"{'='*130}")
        print("✅ MATCH 33 RECARGADO EXITOSAMENTE")
        print(f"{'='*130}\n")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    recargar_match_33()
