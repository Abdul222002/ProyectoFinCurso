"""
SISTEMA BALANCEADO DE PUNTUACIÓN FANTASY FOOTBALL
Versión ajustada para dar más peso a goles y acciones decisivas
"""

from dataclasses import dataclass
from fantasy_scoring_system_improved import *

# ============================================
# CONFIGURACIÓN BALANCEADA
# ============================================

@dataclass
class BalancedScoringConfig(ScoringConfig):
    """
    Configuración balanceada que prioriza:
    1. Acciones DECISIVAS (goles, asistencias)
    2. Rating (rendimiento general)
    3. Bonus acumulativos (más difíciles de conseguir)
    
    FILOSOFÍA:
    - 1 gol debe valer MÁS que trabajar mucho sin ser decisivo
    - Los acumuladores son BONUS, no el punto principal
    """
    
    # ========================================
    # ACCIONES DECISIVAS (AUMENTADAS)
    # ========================================
    
    # Goles por posición - AUMENTADO SIGNIFICATIVAMENTE
    goals_gk_def: int = 10        # Era 6 → Ahora 10 (portero/defensa marcando es MUY raro)
    goals_mid: int = 7            # Era 5 → Ahora 7
    goals_fwd: int = 6            # Era 4 → Ahora 6 (delanteros DEBEN marcar)
    
    # Asistencias - AUMENTADO
    assist_goal: int = 5          # Era 3 → Ahora 5 (asistencia es MUY importante)
    assist_chance: int = 2        # Era 1 → Ahora 2 (crear ocasiones)
    
    # ========================================
    # RATING - IGUAL (ya está bien)
    # ========================================
    rating_max_points: int = 4
    rating_min_threshold: float = 5.0
    rating_max_threshold: float = 8.0
    
    # ========================================
    # ACUMULADORES - MUCHO MÁS DIFÍCILES
    # ========================================
    
    # Ataque - REDUCIDO DRÁSTICAMENTE
    saves_per_point: int = 3              # Era 2 → Ahora 3
    shots_on_target_per_point: int = 4    # Era 2 → Ahora 4 (más difícil)
    dribbles_per_point: int = 5           # Era 3 → Ahora 5 (más difícil)
    crosses_per_point: int = 4            # Era 2 → Ahora 4
    
    # Defensa - REDUCIDO DRÁSTICAMENTE  
    ball_recoveries_per_point: int = 10   # Era 5 → Ahora 10 (el doble)
    clearances_per_point: int = 6         # Era 3 → Ahora 6 (el doble)
    tackles_per_point: int = 8            # Era 5 → Ahora 8
    interceptions_per_point: int = 8      # Era 5 → Ahora 8
    
    # Extras - REDUCIDO DRÁSTICAMENTE
    duels_won_per_point: int = 10         # Era 6 → Ahora 10
    accurate_passes_per_point: int = 50   # Era 30 → Ahora 50 (mucho más difícil)
    fouls_per_penalty: int = 2            # Era 3 → Ahora 2 (más estricto)
    
    # ========================================
    # CLEAN SHEET - LIGERAMENTE AUMENTADO
    # ========================================
    clean_sheet_gk: int = 5       # Era 4 → Ahora 5
    clean_sheet_def: int = 4      # Era 3 → Ahora 4
    clean_sheet_mid: int = 2      # Igual
    clean_sheet_fwd: int = 1      # Igual
    
    # ========================================
    # PENALIZACIONES - MÁS ESTRICTAS
    # ========================================
    yellow_card_penalty: int = -2         # Era -1 → Ahora -2
    red_card_penalty: int = -5            # Era -3 → Ahora -5
    
    # Goles recibidos - MÁS ESTRICTO
    goals_conceded_per_penalty: int = 2
    goals_conceded_penalty_gk_def: int = -3   # Era -2 → Ahora -3
    goals_conceded_penalty_mid_fwd: int = -1  # Igual
    
    # Pérdidas - LIGERAMENTE MÁS ESTRICTO
    losses_gk_def_threshold: int = 6      # Era 8 → Ahora 6
    losses_mid_threshold: int = 8         # Era 10 → Ahora 8
    losses_fwd_threshold: int = 10        # Era 12 → Ahora 10


# ============================================
# CONFIGURACIÓN ULTRA OFENSIVA
# ============================================

@dataclass  
class OffensiveScoringConfig(ScoringConfig):
    """
    Para ligas que quieren MÁXIMO protagonismo a goles/asistencias
    """
    
    # GOLES - VALOR MÁXIMO
    goals_gk_def: int = 12
    goals_mid: int = 8
    goals_fwd: int = 7
    
    # ASISTENCIAS - VALOR MUY ALTO
    assist_goal: int = 6
    assist_chance: int = 3
    
    # ACUMULADORES - PRÁCTICAMENTE IGNORADOS
    shots_on_target_per_point: int = 6
    dribbles_per_point: int = 8
    crosses_per_point: int = 6
    ball_recoveries_per_point: int = 15
    clearances_per_point: int = 10
    tackles_per_point: int = 12
    interceptions_per_point: int = 12
    duels_won_per_point: int = 15
    accurate_passes_per_point: int = 80
    
    # CLEAN SHEET - ALTO
    clean_sheet_gk: int = 6
    clean_sheet_def: int = 5


# ============================================
# COMPARACIÓN DE CONFIGURACIONES
# ============================================

def comparar_configuraciones_ejemplo():
    """
    Compara mismo jugador con diferentes configs
    """
    
    print("\n" + "="*100)
    print("COMPARACIÓN DE CONFIGURACIONES - MISMO RENDIMIENTO")
    print("="*100 + "\n")
    
    # Caso 1: Delantero con 2 goles
    print("📊 CASO 1: DELANTERO CON 2 GOLES")
    print("-" * 100)
    
    delantero = PlayerStats(
        player_name="Kieron Bowie",
        position=Position.FWD,
        minutes_played=90,
        goals=2,
        rating=7.5,
        shots_on_target=6,
        dribbles=4,
        duels_won=8
    )
    
    configs = {
        "Original": ScoringConfig(),
        "Balanceada": BalancedScoringConfig(),
        "Ultra Ofensiva": OffensiveScoringConfig()
    }
    
    print(f"\n{'CONFIGURACIÓN':<20} | {'PUNTOS TOTALES':<15} | {'Pts por Goles':<15} | {'Pts por Bonus':<15}")
    print("-" * 100)
    
    for nombre, config in configs.items():
        engine = FantasyScoringEngine(config)
        resultado = engine.calculate_points(delantero)
        
        pts_goles = resultado.points_breakdown.get('Goles', 0)
        pts_bonus = (resultado.points_breakdown.get('Bonus ataque', 0) + 
                    resultado.points_breakdown.get('Bonus extras', 0))
        
        print(f"{nombre:<20} | {resultado.fantasy_points:<15} | {pts_goles:<15.0f} | {pts_bonus:<15.0f}")
    
    # Caso 2: Mediocentro con 1 asistencia y muchas stats
    print("\n\n📊 CASO 2: MEDIOCENTRO CON 1 ASISTENCIA + MUCHAS STATS")
    print("-" * 100)
    
    mediocentro = PlayerStats(
        player_name="Panutche Camara",
        position=Position.MID,
        minutes_played=90,
        assists=1,
        rating=7.8,
        tackles=10,
        interceptions=6,
        duels_won=12,
        accurate_passes=60,
        ball_recoveries=12
    )
    
    print(f"\n{'CONFIGURACIÓN':<20} | {'PUNTOS TOTALES':<15} | {'Pts Asistencia':<15} | {'Pts Bonus':<15}")
    print("-" * 100)
    
    for nombre, config in configs.items():
        engine = FantasyScoringEngine(config)
        resultado = engine.calculate_points(mediocentro)
        
        pts_asist = resultado.points_breakdown.get('Asistencias', 0)
        pts_bonus = (resultado.points_breakdown.get('Bonus defensa', 0) + 
                    resultado.points_breakdown.get('Bonus extras', 0))
        
        print(f"{nombre:<20} | {resultado.fantasy_points:<15} | {pts_asist:<15.0f} | {pts_bonus:<15.0f}")
    
    print("\n" + "="*100)
    print("ANÁLISIS:")
    print("="*100)
    print("""
    CONFIG ORIGINAL:
    ❌ Problema: El mediocentro con solo 1 asistencia puede superar al delantero con 2 goles
    ❌ Los acumuladores valen demasiado
    
    CONFIG BALANCEADA:
    ✅ El delantero con 2 goles tiene MÁS puntos que el mediocentro trabajador
    ✅ Los goles valen significativamente más (6 pts vs 4 pts)
    ✅ Los acumuladores son bonus, no lo principal
    ✅ Se reconoce el trabajo defensivo pero sin exagerar
    
    CONFIG ULTRA OFENSIVA:
    ⚡ MÁXIMA prioridad a goles/asistencias
    ⚡ Los acumuladores casi no cuentan
    ⚡ Ideal para ligas que quieren solo protagonismo ofensivo
    """)


# ============================================
# ANÁLISIS DETALLADO
# ============================================

def analisis_detallado_balanceo():
    """
    Muestra desglose completo de puntos
    """
    
    print("\n" + "="*100)
    print("ANÁLISIS DETALLADO - CONFIG BALANCEADA")
    print("="*100 + "\n")
    
    config = BalancedScoringConfig()
    engine = FantasyScoringEngine(config)
    
    # Delantero goleador
    delantero = PlayerStats(
        player_name="Goleador",
        position=Position.FWD,
        minutes_played=90,
        goals=2,
        assists=1,
        rating=8.0,
        shots_on_target=7,
        dribbles=5
    )
    
    resultado_del = engine.calculate_points(delantero)
    
    print("🎯 DELANTERO GOLEADOR (2 goles, 1 asistencia)")
    print("-" * 100)
    for cat, pts in resultado_del.points_breakdown.items():
        print(f"  {cat:<30}: {pts:>+6.1f} pts")
    print(f"\n  {'TOTAL':<30}: {resultado_del.fantasy_points:>6} pts")
    
    # Mediocentro trabajador
    mediocentro = PlayerStats(
        player_name="Trabajador",
        position=Position.MID,
        minutes_played=90,
        assists=1,
        rating=7.5,
        tackles=12,
        interceptions=8,
        duels_won=15,
        accurate_passes=70,
        ball_recoveries=15,
        clearances=8
    )
    
    resultado_mid = engine.calculate_points(mediocentro)
    
    print("\n\n💪 MEDIOCENTRO TRABAJADOR (1 asistencia, muchas stats defensivas)")
    print("-" * 100)
    for cat, pts in resultado_mid.points_breakdown.items():
        print(f"  {cat:<30}: {pts:>+6.1f} pts")
    print(f"\n  {'TOTAL':<30}: {resultado_mid.fantasy_points:>6} pts")
    
    print("\n" + "="*100)
    print(f"✅ RESULTADO: El delantero goleador tiene {resultado_del.fantasy_points} pts vs {resultado_mid.fantasy_points} pts del mediocentro")
    print(f"✅ DIFERENCIA: +{resultado_del.fantasy_points - resultado_mid.fantasy_points} pts a favor del que marca goles")
    print("="*100)


# ============================================
# TABLA COMPARATIVA
# ============================================

def tabla_comparativa_valores():
    """
    Tabla visual de cambios
    """
    
    print("\n" + "="*100)
    print("TABLA COMPARATIVA DE VALORES")
    print("="*100 + "\n")
    
    print(f"{'STAT':<30} | {'ORIGINAL':<20} | {'BALANCEADA':<20} | {'CAMBIO':<20}")
    print("-" * 100)
    
    comparaciones = [
        ("Gol Delantero", "4 pts", "6 pts", "⬆️ +50%"),
        ("Gol Mediocentro", "5 pts", "7 pts", "⬆️ +40%"),
        ("Gol Defensa/GK", "6 pts", "10 pts", "⬆️ +67%"),
        ("Asistencia de gol", "3 pts", "5 pts", "⬆️ +67%"),
        ("Ocasión creada", "1 pt", "2 pts", "⬆️ +100%"),
        ("", "", "", ""),
        ("Tiros a puerta", "cada 2 = 1pt", "cada 4 = 1pt", "⬇️ -50%"),
        ("Regates", "cada 3 = 1pt", "cada 5 = 1pt", "⬇️ -40%"),
        ("Tackles", "cada 5 = 1pt", "cada 8 = 1pt", "⬇️ -38%"),
        ("Recuperaciones", "cada 5 = 1pt", "cada 10 = 1pt", "⬇️ -50%"),
        ("Pases precisos", "cada 30 = 1pt", "cada 50 = 1pt", "⬇️ -40%"),
        ("Duelos ganados", "cada 6 = 1pt", "cada 10 = 1pt", "⬇️ -40%"),
        ("", "", "", ""),
        ("Tarjeta amarilla", "-1 pt", "-2 pts", "⬇️ Más estricto"),
        ("Tarjeta roja", "-3 pts", "-5 pts", "⬇️ Más estricto"),
    ]
    
    for stat, orig, bal, cambio in comparaciones:
        print(f"{stat:<30} | {orig:<20} | {bal:<20} | {cambio:<20}")
    
    print("\n" + "="*100)
    print("RESUMEN:")
    print("  ⬆️  ACCIONES DECISIVAS: +40% a +100% más valor")
    print("  ⬇️  ACUMULADORES: -38% a -50% menos valor")
    print("  ✅ RESULTADO: Goles y asistencias son claramente lo más importante")
    print("="*100)


# ============================================
# FUNCIÓN PRINCIPAL MEJORADA
# ============================================

def analyze_fixture_balanced(fixture_id: int, config_type: str = 'balanced',
                             show_detailed: bool = False, top_n: int = 5):
    """
    Analiza un fixture con configuración balanceada
    
    Args:
        fixture_id: ID del fixture
        config_type: 'original', 'balanced', 'offensive'
        show_detailed: Mostrar desglose
        top_n: Top N jugadores
    """
    
    configs = {
        'original': ScoringConfig(),
        'balanced': BalancedScoringConfig(),
        'offensive': OffensiveScoringConfig()
    }
    
    config = configs.get(config_type, BalancedScoringConfig())
    
    print(f"\n🎮 Usando configuración: {config_type.upper()}")
    
    analyze_fixture(fixture_id, config=config, show_detailed=show_detailed, top_n=top_n)


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║              SISTEMA BALANCEADO DE PUNTUACIÓN FANTASY                     ║
║                                                                            ║
║  Versión ajustada donde GOLES y ASISTENCIAS valen significativamente     ║
║  MÁS que simplemente "trabajar mucho" sin ser decisivo.                  ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Ejecutar demostraciones
    tabla_comparativa_valores()
    input("\nPresiona ENTER para ver comparación de configuraciones...")
    
    comparar_configuraciones_ejemplo()
    input("\nPresiona ENTER para ver análisis detallado...")
    
    analisis_detallado_balanceo()
    
    print("\n\n" + "="*100)
    print("🎯 RECOMENDACIÓN PARA TU LIGA:")
    print("="*100)
    print("""
    Para una liga EQUILIBRADA donde los goles sean protagonistas:
    👉 Usa: BalancedScoringConfig()
    
    Para una liga ULTRA OFENSIVA donde solo importan goles/asistencias:
    👉 Usa: OffensiveScoringConfig()
    
    Ejemplo de uso:
    
        from fantasy_scoring_balanced import BalancedScoringConfig
        
        config = BalancedScoringConfig()
        analyze_fixture(19428171, config=config)
    
    """)
    print("="*100)
