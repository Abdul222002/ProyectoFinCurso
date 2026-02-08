"""
MIGRACIÓN A BASE DE DATOS - Jornada 1
Guarda las estadísticas de la jornada 1 en la base de datos
Usa el sistema de puntuación balanceado
"""

import sys
import os
from datetime import datetime

# Añadir paths necesarios
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from sqlalchemy.orm import Session
from app.core.database import engine, get_db, Base
from app.models.models import (
    Gameweek,
    Match,
    Player,
    PlayerMatchStats,
    MatchStatus
)

# Importar sistema de puntos
from scripts.sistema_puntos_oficial import (
    FantasyScoringEngine,
    ScoringConfig,
    SportmonksAPIClient,
    StatsExtractor,
    API_TOKEN,
    logger
)
from dataclasses import dataclass


# ============================================
# CONFIGURACIÓN BALANCEADA
# ============================================

@dataclass
class BalancedScoringConfig(ScoringConfig):
    """Configuración balanceada que prioriza goles y asistencias"""
    
    # GOLES - AUMENTADOS
    goals_gk_def: int = 10
    goals_mid: int = 7
    goals_fwd: int = 6
    
    # ASISTENCIAS - AUMENTADAS
    assist_goal: int = 5
    assist_chance: int = 2
    
    # CLEAN SHEET
    clean_sheet_gk: int = 5
    clean_sheet_def: int = 4
    
    # ACUMULADORES - REDUCIDOS
    shots_on_target_per_point: int = 4
    dribbles_per_point: int = 5
    crosses_per_point: int = 4
    ball_recoveries_per_point: int = 10
    clearances_per_point: int = 6
    tackles_per_point: int = 8
    interceptions_per_point: int = 8
    duels_won_per_point: int = 10
    accurate_passes_per_point: int = 50
    
    # PENALIZACIONES - MÁS ESTRICTAS
    yellow_card_penalty: int = -2
    red_card_penalty: int = -5
    goals_conceded_penalty_gk_def: int = -3
    fouls_per_penalty: int = 2
    losses_gk_def_threshold: int = 6
    losses_mid_threshold: int = 8
    losses_fwd_threshold: int = 10
    
    # PENALTIS
    penalty_save_bonus: int = 5
    penalty_miss_penalty: int = -3
    penalty_won_bonus: int = 2
    penalty_committed_penalty: int = -2


# ============================================
# FIXTURES JORNADA 1
# ============================================

FIXTURES_JORNADA_1 = [
    {
        'sportmonks_id': 19428039,
        'home_team': 'Kilmarnock',
        'away_team': 'Livingston',
        'kickoff': '2024-08-04 12:00:00'
    },
    {
        'sportmonks_id': 19428040,
        'home_team': 'Motherwell',
        'away_team': 'Rangers',
        'kickoff': '2024-08-04 14:00:00'
    },
    {
        'sportmonks_id': 19428041,
        'home_team': 'Falkirk',
        'away_team': 'Dundee United',
        'kickoff': '2024-08-04 16:00:00'
    },
    {
        'sportmonks_id': 19428042,
        'home_team': 'Dundee',
        'away_team': 'Hibernian',
        'kickoff': '2024-08-04 18:00:00'
    },
    {
        'sportmonks_id': 19428043,
        'home_team': 'Celtic',
        'away_team': 'St. Mirren',
        'kickoff': '2024-08-04 20:00:00'
    },
]


# ============================================
# FUNCIONES PRINCIPALES
# ============================================

def create_gameweek_1(db: Session):
    """Crea o recupera la jornada 1"""
    
    # Buscar si ya existe
    gameweek = db.query(Gameweek).filter(Gameweek.number == 1).first()
    
    if gameweek:
        logger.info("Jornada 1 ya existe en la BD")
        return gameweek
    
    # Crear nueva jornada
    gameweek = Gameweek(
        number=1,
        start_date=datetime(2024, 8, 4, 12, 0, 0),
        end_date=datetime(2024, 8, 4, 23, 59, 59),
        is_active=False,
        is_finished=True
    )
    
    db.add(gameweek)
    db.commit()
    db.refresh(gameweek)
    
    logger.info(f"✅ Jornada 1 creada: {gameweek}")
    return gameweek


def migrar_jornada_1_db():
    """Migra la jornada 1 completa a la base de datos"""
    
    print("\n" + "="*130)
    print("💾 MIGRACIÓN A BASE DE DATOS - JORNADA 1")
    print("="*130)
    print("\n⚖️  Usando: BalancedScoringConfig")
    print("="*130 + "\n")
    
    # Validación
    if not API_TOKEN:
        logger.error("SPORTMONKS_API_KEY no está configurada")
        return
    
    # Crear tablas si no existen
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tablas de base de datos verificadas")
    
    # Obtener sesión
    db = next(get_db())
    
    try:
        # 1. Crear/obtener jornada 1
        gameweek = create_gameweek_1(db)
        
        # 2. Configurar sistema de puntos
        api_client = SportmonksAPIClient(API_TOKEN)
        config = BalancedScoringConfig()
        scoring_engine = FantasyScoringEngine(config)
        
        total_players_saved = 0
        total_matches_saved = 0
        
        # 3. Procesar cada partido
        for idx, fixture_info in enumerate(FIXTURES_JORNADA_1, 1):
            fixture_id = fixture_info['sportmonks_id']
            
            print(f"\n{'='*130}")
            print(f"⚽ PARTIDO {idx}/{len(FIXTURES_JORNADA_1)}")
            print(f"{'='*130}")
            
            # Buscar si el partido ya existe
            existing_match = db.query(Match).filter(
                Match.sportmonks_id == fixture_id
            ).first()
            
            if existing_match:
                print(f"⚠️  Partido {fixture_info['home_team']} vs {fixture_info['away_team']} ya existe. Actualizando...")
                match = existing_match
            else:
                match = None
            
            # Obtener datos del partido
            fixture_data = api_client.get_fixture(fixture_id)
            if not fixture_data:
                print(f"❌ No se pudo obtener datos del fixture {fixture_id}")
                continue
            
            # Extraer información
            lineups = fixture_data.get('lineups', [])
            participants = fixture_data.get('participants', [])
            scores = fixture_data.get('scores', [])
            
            # Info equipos
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
            
            # Crear o actualizar partido
            if not match:
                match = Match(
                    sportmonks_id=fixture_id,
                    gameweek_id=gameweek.id,
                    home_team=home_team.get('name', fixture_info['home_team']),
                    away_team=away_team.get('name', fixture_info['away_team']),
                    home_score=home_score,
                    away_score=away_score,
                    status=MatchStatus.FINISHED,
                    kickoff_time=datetime.strptime(fixture_info['kickoff'], '%Y-%m-%d %H:%M:%S')
                )
                db.add(match)
                db.flush()  # Get ID sin hacer commit
                total_matches_saved += 1
            else:
                match.home_score = home_score
                match.away_score = away_score
                match.status = MatchStatus.FINISHED
            
            print(f"🏟️  {match.home_team} {home_score} - {away_score} {match.away_team}\n")
            
            # Procesar jugadores
            players_in_match = 0
            
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
                
                # Calcular puntos
                stats = scoring_engine.calculate_points(stats)
                
                if stats.minutes_played == 0:
                    continue  # No guardar jugadores que no jugaron
                
                # Buscar o crear jugador en BD
                player_name = stats.player_name
                sportmonks_player_id = player_entry.get('player_id')
                
                player = db.query(Player).filter(
                    Player.sportmonks_id == sportmonks_player_id
                ).first()
                
                if not player:
                    # Determinar equipo del jugador
                    player_team = match.home_team if player_entry.get('participant_id') == home_team.get('id') else match.away_team
                    
                    # Convertir posición a enum correcto
                    from app.models.models import Position as DBPosition
                    if stats.position.name == 'GK':
                        db_position = DBPosition.GK
                    elif stats.position.name == 'DEF':
                        db_position = DBPosition.DEF
                    elif stats.position.name == 'MID':
                        db_position = DBPosition.MID
                    else:
                        db_position = DBPosition.FWD
                    
                    # Crear nuevo jugador (simplificado)
                    player = Player(
                        name=player_name,
                        sportmonks_id=sportmonks_player_id,
                        age=25,  # Placeholder
                        position=db_position,
                        nationality="Scotland",  # Placeholder
                        overall_rating=70,  # Placeholder
                        potential=75,
                        current_team=player_team
                    )
                    db.add(player)
                    db.flush()
                
                # Buscar si ya existe la stat del partido
                try:
                    existing_stat = db.query(PlayerMatchStats).filter(
                        PlayerMatchStats.player_id == player.id,
                        PlayerMatchStats.match_id == match.id
                    ).first()
                except Exception as e:
                    logger.error(f"Error al buscar stat existente: {e}")
                    existing_stat = None
                
                if existing_stat:
                    # Actualizar
                    player_stat = existing_stat
                else:
                    # Crear nueva
                    player_stat = PlayerMatchStats(
                        player_id=player.id,
                        match_id=match.id
                    )
                    db.add(player_stat)
                
                # Actualizar todos los campos
                try:
                    player_stat.minutes_played = stats.minutes_played
                    player_stat.rating = stats.rating
                    player_stat.goals = stats.goals
                    player_stat.assists = stats.assists
                    player_stat.chances_created = stats.chances_created
                    player_stat.clean_sheet = stats.clean_sheet
                    player_stat.goals_conceded = stats.goals_conceded
                    player_stat.goals_conceded_team = stats.goals_conceded_team
                    player_stat.saves = stats.saves
                    player_stat.clearances = stats.clearances
                    player_stat.yellow_cards = stats.yellow_cards
                    player_stat.red_cards = stats.red_cards
                    player_stat.shots_on_target = stats.shots_on_target
                    player_stat.dribbles = stats.dribbles
                    player_stat.crosses = stats.crosses
                    player_stat.ball_recoveries = stats.ball_recoveries
                    player_stat.dispossessed = stats.dispossessed
                    player_stat.possession_lost = stats.possession_lost
                    player_stat.turnovers = stats.turnovers
                    player_stat.total_losses = stats.total_losses
                    player_stat.accurate_passes = stats.accurate_passes
                    player_stat.tackles = stats.tackles
                    player_stat.interceptions = stats.interceptions
                    player_stat.duels_won = stats.duels_won
                    player_stat.fouls = stats.fouls
                    player_stat.penalty_miss = stats.penalty_miss
                    player_stat.penalty_save = stats.penalty_save
                    player_stat.penalty_won = stats.penalty_won
                    player_stat.penalty_committed = stats.penalty_committed
                    player_stat.fantasy_points = stats.fantasy_points
                    
                    players_in_match += 1
                    total_players_saved += 1
                except Exception as e:
                    logger.error(f"Error al asignar stats para {player_name}: {e}")
                    db.rollback()
                    raise
            
            print(f"✅ Guardados: {players_in_match} jugadores")
            
            # Commit después de cada partido
            db.commit()
        
        # Resumen final
        print("\n" + "="*130)
        print("📊 RESUMEN DE MIGRACIÓN")
        print("="*130)
        print(f"\n✅ Jornada 1 guardada correctamente")
        print(f"  - Partidos: {total_matches_saved} nuevos")
        print(f"  - Jugadores stats: {total_players_saved} registros")
        print("\n" + "="*130 + "\n")
        
        # Verificar
        print("🔍 VERIFICACIÓN:")
        total_stats = db.query(PlayerMatchStats).join(Match).filter(
            Match.gameweek_id == gameweek.id
        ).count()
        print(f"  - Total stats en jornada 1: {total_stats}")
        
        # Top 5 jugadores
        top_players = db.query(PlayerMatchStats, Player).join(
            Player
        ).join(Match).filter(
            Match.gameweek_id == gameweek.id
        ).order_by(PlayerMatchStats.fantasy_points.desc()).limit(5).all()
        
        print(f"\n🏆 TOP 5 JUGADORES EN BD:")
        print("-" * 130)
        for idx, (stat, player) in enumerate(top_players, 1):
            print(f"  {idx}. {player.name:<30} - {stat.fantasy_points} pts "
                  f"({stat.goals}G, {stat.assists}A)")
        
        print("\n✅ MIGRACIÓN COMPLETADA CON ÉXITO\n")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        db.close()


# ============================================
# EJECUTAR
# ============================================

if __name__ == "__main__":
    migrar_jornada_1_db()
