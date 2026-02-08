"""
MIGRACIÓN JORNADA 1 - Sistema Balanceado
Usa la configuración balanceada que prioriza goles y asistencias
"""

import sys
import os

# Importar desde backend/scripts
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'scripts'))

from sistema_puntos_oficial import (
    FantasyScoringEngine,
    ScoringConfig,
    SportmonksAPIClient,
    StatsExtractor,
    ResultsPresenter,
    logger,
    API_TOKEN
)
from dataclasses import dataclass

# ============================================
# CONFIGURACIÓN BALANCEADA
# ============================================

@dataclass
class BalancedScoringConfig(ScoringConfig):
    """
    Configuración balanceada que prioriza:
    1. Goles y asistencias (DECISIVAS)
    2. Rating (rendimiento)
    3. Bonus acumulativos (más difíciles)
    """
    
    # GOLES - AUMENTADOS +40-67%
    goals_gk_def: int = 10      # Era 6 → +67%
    goals_mid: int = 7          # Era 5 → +40%
    goals_fwd: int = 6          # Era 4 → +50%
    
    # ASISTENCIAS - AUMENTADAS +67-100%
    assist_goal: int = 5        # Era 3 → +67%
    assist_chance: int = 2      # Era 1 → +100%
    
    # CLEAN SHEET - LIGERAMENTE AUMENTADO
    clean_sheet_gk: int = 5     # Era 4 → +25%
    clean_sheet_def: int = 4    # Era 3 → +33%
    
    # ACUMULADORES - REDUCIDOS -38% a -50%
    shots_on_target_per_point: int = 4    # Era 2 → -50%
    dribbles_per_point: int = 5           # Era 3 → -40%
    crosses_per_point: int = 4            # Era 2 → -50%
    ball_recoveries_per_point: int = 10   # Era 5 → -50%
    clearances_per_point: int = 6         # Era 3 → -50%
    tackles_per_point: int = 8            # Era 5 → -38%
    interceptions_per_point: int = 8      # Era 5 → -38%
    duels_won_per_point: int = 10         # Era 6 → -40%
    accurate_passes_per_point: int = 50   # Era 30 → -40%
    
    # PENALIZACIONES - MÁS ESTRICTAS
    yellow_card_penalty: int = -2         # Era -1
    red_card_penalty: int = -5            # Era -3
    goals_conceded_penalty_gk_def: int = -3  # Era -2
    fouls_per_penalty: int = 2            # Era 3
    
    # PÉRDIDAS - MÁS ESTRICTAS
    losses_gk_def_threshold: int = 6      # Era 8
    losses_mid_threshold: int = 8         # Era 10
    losses_fwd_threshold: int = 10        # Era 12
    
    # PENALTIS - AÑADIDOS ✅
    penalty_save_bonus: int = 5
    penalty_miss_penalty: int = -3
    penalty_won_bonus: int = 2
    penalty_committed_penalty: int = -2


# ============================================
# FIXTURES JORNADA 1
# ============================================

FIXTURES_JORNADA_1 = [
    19428039,  # Kilmarnock vs Livingston
    19428040,  # Motherwell vs Rangers
    19428041,  # Falkirk vs Dundee United
    19428042,  # Dundee vs Hibernian
    19428043,  # Celtic vs St. Mirren
]


# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def migrar_jornada_1_balanceada():
    """Migra jornada 1 con configuración balanceada"""
    
    print("\n" + "="*130)
    print("⚖️  MIGRACIÓN JORNADA 1 - SISTEMA BALANCEADO")
    print("="*130)
    print("\n📊 CONFIGURACIÓN USADA:")
    print("  ⬆️  Goles FWD: 6 pts (+50%)")
    print("  ⬆️  Goles MID: 7 pts (+40%)")
    print("  ⬆️  Goles DEF/GK: 10 pts (+67%)")
    print("  ⬆️  Asistencias: 5 pts (+67%)")
    print("  ⬇️  Acumuladores: -38% a -50%")
    print("  ✅ Penaltis: Parar +5, Fallar -3")
    print("="*130 + "\n")
    
    # Validación
    if not API_TOKEN:
        logger.error("SPORTMONKS_API_KEY no está configurada")
        return
    
    # Inicializar componentes CON CONFIGURACIÓN BALANCEADA
    api_client = SportmonksAPIClient(API_TOKEN)
    config = BalancedScoringConfig()
    scoring_engine = FantasyScoringEngine(config)
    presenter = ResultsPresenter()
    
    all_players = []
    
    # Procesar cada partido
    for idx, fixture_id in enumerate(FIXTURES_JORNADA_1, 1):
        print(f"\n{'='*130}")
        print(f"⚽ PARTIDO {idx}/{len(FIXTURES_JORNADA_1)} - Fixture ID: {fixture_id}")
        print(f"{'='*130}")
        
        # Obtener datos del partido
        fixture_data = api_client.get_fixture(fixture_id)
        if not fixture_data:
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
        
        print(f"\n🏟️  {home_team.get('name', 'Home')} {home_score} - {away_score} {away_team.get('name', 'Away')}\n")
        
        # Procesar jugadores
        match_players = []
        presenter.print_table_header()
        
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
            
            # Calcular puntos CON CONFIG BALANCEADA
            stats = scoring_engine.calculate_points(stats)
            
            if stats.minutes_played > 0:
                match_players.append(stats)
                all_players.append(stats)
                presenter.print_player_row(stats)
        
        # Top del partido
        print(f"\n{'='*130}")
        presenter.print_top_scorers(match_players, top_n=3)
    
    # ========================================
    # RESUMEN GLOBAL
    # ========================================
    
    print("\n" + "="*130)
    print("📊 RESUMEN JORNADA 1 COMPLETA - SISTEMA BALANCEADO ⚖️")
    print("="*130 + "\n")
    
    all_players.sort(key=lambda x: x.fantasy_points, reverse=True)
    
    print(f"✅ Total jugadores procesados: {len(all_players)}\n")
    
    print("🏆 TOP 20 JUGADORES:\n")
    print(f"{'#':<3} | {'JUGADOR':<25} | {'EQUIPO':<20} | {'POS':<10} | {'MIN':<3} | {'G':<2} | {'A':<2} | {'NOTA':<5} | {'PTS'}")
    print("-" * 130)
    
    # Obtener equipo de cada jugador (simplificado)
    for idx, player in enumerate(all_players[:20], 1):
        # Nota: Equipo no está en PlayerStats, lo ponemos como "N/A"
        print(f"{idx:<3} | {player.player_name:<25} | {'N/A':<20} | "
              f"{str(player.position):<10} | {player.minutes_played:<3} | "
              f"{player.goals:<2} | {player.assists:<2} | "
              f"{player.rating:<5.1f} | {player.fantasy_points}")
    
    # ========================================
    # ESTADÍSTICAS
    # ========================================
    
    total_puntos = sum(p.fantasy_points for p in all_players)
    promedio = total_puntos / len(all_players) if all_players else 0
    
    print(f"\n📈 ESTADÍSTICAS:")
    print(f"   - Puntos totales: {total_puntos}")
    print(f"   - Promedio: {promedio:.2f} pts/jugador")
    print(f"   - Máximo: {all_players[0].fantasy_points} pts ({all_players[0].player_name})")
    print(f"   - Mínimo: {all_players[-1].fantasy_points} pts ({all_players[-1].player_name})")
    
    # ========================================
    # ANÁLISIS DE GOLEADORES vs TRABAJADORES
    # ========================================
    
    print(f"\n🎯 ANÁLISIS CLAVE:")
    print("-" * 130)
    
    # Buscar jugadores clave
    kieron_bowie = next((p for p in all_players if 'bowie' in p.player_name.lower()), None)
    panutche_camara = next((p for p in all_players if 'camara' in p.player_name.lower()), None)
    
    if kieron_bowie and panutche_camara:
        print(f"\nCOMPARACIÓN CRÍTICA:")
        print(f"  🥇 Kieron Bowie (2 goles):     {kieron_bowie.fantasy_points} pts")
        print(f"  🥈 Panutche Camara (1 asist):  {panutche_camara.fantasy_points} pts")
        
        diff = kieron_bowie.fantasy_points - panutche_camara.fantasy_points
        if diff > 0:
            print(f"  ✅ DIFERENCIA: +{diff} pts a favor del goleador")
            print(f"  ✅ SISTEMA BALANCEADO FUNCIONANDO CORRECTAMENTE")
        else:
            print(f"  ⚠️  DIFERENCIA: {diff} pts - El mediocentro aún supera al goleador")
    
    print("\n" + "="*130)
    print("✅ MIGRACIÓN COMPLETADA")
    print("="*130 + "\n")
    
    return all_players


# ============================================
# EJECUTAR
# ============================================

if __name__ == "__main__":
    migrar_jornada_1_balanceada()
