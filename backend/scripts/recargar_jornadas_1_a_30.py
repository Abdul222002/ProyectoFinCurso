"""
RECARGA COMPLETA DE LAS JORNADAS 1 A 30
Este script borra todas las estadísticas de player_match_stats de las primeras 30 jornadas
y las vuelve a cargar desde la API de Sportmonks usando el sistema de puntos balanceado.
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load env before doing anything else
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Añadir paths necesarios
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import engine, get_db, Base
from app.models.models import (
    Gameweek,
    Match,
    Player,
    PlayerMatchStats,
    MatchStatus,
    Position as DBPosition
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
# CONFIGURACIÓN BALANCEADA (LA MISMA QUE 3 JORNADAS)
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


def recargar_jornadas_1_a_30():
    """Recarga las 30 primeras jornadas desde Sportmonks API"""
    
    print("\n" + "="*130)
    print("🔄 RECARGA COMPLETA DE LAS JORNADAS 1 A 30")
    print("="*130)
    print("\n⚖️  Usando: BalancedScoringConfig")
    print("="*130 + "\n")
    
    # Validación
    if not API_TOKEN:
        logger.error("SPORTMONKS_API_KEY no está configurada")
        return
    
    # Obtener sesión
    db = next(get_db())
    
    try:
        # PASO 1: Obtener los partidos de las jornadas 1 a 30
        print("\n📋 Obteniendo partidos de las jornadas...\n")
        TARGET_GAMEWEEKS = list(range(1, 31))
        matches = db.query(Match).join(Gameweek).filter(
            Gameweek.number.in_(TARGET_GAMEWEEKS)
        ).order_by(Gameweek.number, Match.id).all()
        
        print(f"✅ Encontrados {len(matches)} partidos:")
        
        # PASO 2: Borrar TODAS las estadísticas de estos partidos
        print(f"\n🗑️  Borrando estadísticas existentes de las jornadas objetivas...\n")
        
        match_ids = [m.id for m in matches]
        if match_ids:
            deleted_count = db.query(PlayerMatchStats).filter(
                PlayerMatchStats.match_id.in_(match_ids)
            ).delete(synchronize_session=False)
            db.commit()
            print(f"✅ Borrados {deleted_count} registros antiguos\n")
        else:
            print("⚠️ No se han encontrado partidos en la base de datos para borrar las estadísticas. ¿Están sincronizadas las jornadas?")
            return
            
        # PASO 3: Configurar sistema de puntos
        api_client = SportmonksAPIClient(API_TOKEN)
        config = BalancedScoringConfig()
        scoring_engine = FantasyScoringEngine(config)
        
        total_players_saved = 0
        
        # Hacemos caché de los jugadores del equipo para reducir selects
        print("\n📦 Cargando jugadores en caché...")
        all_players_db = db.query(Player).filter(Player.is_legend == 0).all()
        players_by_team = {}
        players_by_sportmonks_id = {}
        for p in all_players_db:
            if p.current_team not in players_by_team:
                players_by_team[p.current_team] = []
            players_by_team[p.current_team].append(p)
            if p.sportmonks_id:
                players_by_sportmonks_id[p.sportmonks_id] = p
                
        # PASO 4: Procesar cada partido
        for idx, match in enumerate(matches, 1):
            gameweek_num = db.query(Gameweek).filter(Gameweek.id == match.gameweek_id).first().number
            
            print(f"\n{'='*130}")
            print(f"⚽ PARTIDO {idx}/{len(matches)} - Jornada {gameweek_num}")
            print(f"{'='*130}")
            print(f"🏟️  {match.home_team} {match.home_score} - {match.away_score} {match.away_team}")
            print(f"📡 Sportmonks ID: {match.sportmonks_id}\n")
            
            # Obtener datos del partido desde la API
            fixture_data = api_client.get_fixture(match.sportmonks_id)
            if not fixture_data:
                print(f"❌ No se pudo obtener datos del fixture {match.sportmonks_id}")
                continue
            
            # Extraer información
            lineups = fixture_data.get('lineups', [])
            participants = fixture_data.get('participants', [])
            
            # Info equipos
            home_team = next((p for p in participants 
                             if p.get('meta', {}).get('location') == 'home'), {})
            away_team = next((p for p in participants 
                             if p.get('meta', {}).get('location') == 'away'), {})
            
            home_score = match.home_score
            away_score = match.away_score
            
            # Procesar jugadores que JUGARON (tienen stats en la API)
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
                
                # Calcular puntos
                stats = scoring_engine.calculate_points(stats)
                
                if stats.minutes_played == 0:
                    continue  # Saltamos, pero los añadiremos después
                
                sportmonks_player_id = player_entry.get('player_id')
                player = players_by_sportmonks_id.get(sportmonks_player_id)

                # Buscar en db si no está en la cache
                if not player:
                    player = db.query(Player).filter(
                        Player.sportmonks_id == sportmonks_player_id
                    ).first()
                    
                if not player:
                    # Crear nuevo jugador placeholder si no existe (no deberia pasar normalmente)
                    player_name = stats.player_name
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
                    players_by_sportmonks_id[sportmonks_player_id] = player
                    if player_team not in players_by_team:
                        players_by_team[player_team] = []
                    players_by_team[player_team].append(player)
                
                # Recordar que este jugador ya tiene stats
                played_player_ids.add(player.id)
                
                # Crear nueva estadística
                player_stat = PlayerMatchStats(
                    player_id=player.id,
                    match_id=match.id
                )
                db.add(player_stat)
                
                # Asignar atributos
                try:
                    for attr in dir(stats):
                        if not attr.startswith('__') and hasattr(player_stat, attr) and attr != 'metadata':
                            setattr(player_stat, attr, getattr(stats, attr))
                            
                    players_with_stats += 1
                    total_players_saved += 1
                except Exception as e:
                    logger.error(f"Error al asignar stats para {player.name}: {e}")
                    db.rollback()
                    raise
            
            # AHORA: Añadir registros con 0s para jugadores que NO jugaron
            players_without_stats = 0
            
            all_home_players = players_by_team.get(match.home_team, [])
            all_away_players = players_by_team.get(match.away_team, [])
            all_team_players = all_home_players + all_away_players
            
            # Crear registros con 0s para los que no jugaron
            for player in all_team_players:
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
                    total_players_saved += 1
            
            print(f"✅ Jugadores con stats (API): {players_with_stats}")
            print(f"✅ Jugadores sin minutos (0s): {players_without_stats}")
            print(f"✅ Total guardados: {players_with_stats + players_without_stats}")
            
            # Commit después de cada partido
            db.commit()
        
        # Resumen final
        print("\n" + "="*130)
        print("📊 RESUMEN DE RECARGA")
        print("="*130)
        print(f"\n✅ 30 Jornadas recargadas correctamente")
        print(f"  - Partidos procesados: {len(matches)}")
        print(f"  - Jugadores stats: {total_players_saved} registros")
        print("\n" + "="*130 + "\n")
        
        print("\n✅ RECARGA COMPLETADA CON ÉXITO\n")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error durante la recarga: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    recargar_jornadas_1_a_30()
