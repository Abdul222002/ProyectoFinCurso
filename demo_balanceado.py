#!/usr/bin/env python3
"""
DEMO - Sistema Fantasy Balanceado
Ejecuta este script para ver el sistema balanceado en acción
"""

import sys
import os

# Asegurar que los imports funcionen
sys.path.insert(0, os.path.dirname(__file__))

from fantasy_scoring_system_improved import *
from fantasy_scoring_balanced import *


def demo_completa():
    """Demostración completa del sistema balanceado"""
    
    print("""
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║                      🎮 DEMO - SISTEMA FANTASY BALANCEADO                         ║
║                                                                                    ║
║   Esta demo te muestra la diferencia entre la configuración original             ║
║   y la configuración balanceada que soluciona el problema de puntuación.         ║
║                                                                                    ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    input("\n🎯 Presiona ENTER para ver el PROBLEMA ORIGINAL...")
    
    # ========================================
    # PARTE 1: EL PROBLEMA
    # ========================================
    
    print("\n" + "="*100)
    print("PARTE 1: EL PROBLEMA CON LA CONFIGURACIÓN ORIGINAL")
    print("="*100 + "\n")
    
    print("Vamos a analizar dos jugadores de la Jornada 1 de la Premiership Escocesa:\n")
    
    # Crear jugadores basados en datos reales
    kieron_bowie = PlayerStats(
        player_name="Kieron Bowie",
        position=Position.FWD,
        minutes_played=90,
        goals=2,  # ¡2 GOLES!
        assists=0,
        rating=7.5,
        shots_on_target=6,
        dribbles=4,
        duels_won=8,
        accurate_passes=20
    )
    
    panutche_camara = PlayerStats(
        player_name="Panutche Camara",
        position=Position.MID,
        minutes_played=90,
        goals=0,
        assists=1,  # Solo 1 asistencia
        rating=7.8,
        tackles=10,
        interceptions=6,
        duels_won=12,
        accurate_passes=60,
        ball_recoveries=12
    )
    
    # Calcular con config ORIGINAL
    engine_original = FantasyScoringEngine(ScoringConfig())
    
    resultado_bowie_orig = engine_original.calculate_points(kieron_bowie)
    resultado_camara_orig = engine_original.calculate_points(panutche_camara)
    
    print("📊 CON CONFIGURACIÓN ORIGINAL:")
    print("-" * 100)
    print(f"\n🥇 {resultado_camara_orig.player_name} (Mediocentro)")
    print(f"   Stats: {panutche_camara.goals}G, {panutche_camara.assists}A, {panutche_camara.tackles} tackles, {panutche_camara.accurate_passes} pases")
    print(f"   Puntos: {resultado_camara_orig.fantasy_points} pts")
    print(f"\n   Desglose:")
    for cat, pts in sorted(resultado_camara_orig.points_breakdown.items(), key=lambda x: x[1], reverse=True):
        if pts != 0:
            print(f"      {cat:<25}: {pts:>+6.1f} pts")
    
    print(f"\n🥉 {resultado_bowie_orig.player_name} (Delantero)")
    print(f"   Stats: {kieron_bowie.goals}G (¡2 GOLES!), {kieron_bowie.assists}A")
    print(f"   Puntos: {resultado_bowie_orig.fantasy_points} pts")
    print(f"\n   Desglose:")
    for cat, pts in sorted(resultado_bowie_orig.points_breakdown.items(), key=lambda x: x[1], reverse=True):
        if pts != 0:
            print(f"      {cat:<25}: {pts:>+6.1f} pts")
    
    print("\n" + "="*100)
    print("❌ PROBLEMA DETECTADO:")
    print("="*100)
    print(f"""
    El mediocentro con SOLO 1 ASISTENCIA tiene {resultado_camara_orig.fantasy_points} puntos
    El delantero con 2 GOLES tiene {resultado_bowie_orig.fantasy_points} puntos
    
    ❌ Diferencia: {resultado_camara_orig.fantasy_points - resultado_bowie_orig.fantasy_points} puntos a favor del mediocentro
    
    ¿Por qué? Los ACUMULADORES (tackles, pases, duelos) valen demasiado.
    El mediocentro consigue ~9 puntos solo por "trabajar" sin ser decisivo.
    """)
    
    input("\n⚡ Presiona ENTER para ver la SOLUCIÓN...")
    
    # ========================================
    # PARTE 2: LA SOLUCIÓN
    # ========================================
    
    print("\n" + "="*100)
    print("PARTE 2: LA SOLUCIÓN - CONFIGURACIÓN BALANCEADA")
    print("="*100 + "\n")
    
    print("Ahora vamos a calcular con la CONFIGURACIÓN BALANCEADA:\n")
    print("Cambios principales:")
    print("  ⬆️  Goles: 4 pts → 6 pts (+50%)")
    print("  ⬆️  Asistencias: 3 pts → 5 pts (+67%)")
    print("  ⬇️  Tackles: cada 5 → cada 8 (-38%)")
    print("  ⬇️  Pases: cada 30 → cada 50 (-40%)")
    print("  ⬇️  Duelos: cada 6 → cada 10 (-40%)")
    print()
    
    # Calcular con config BALANCEADA
    engine_balanced = FantasyScoringEngine(BalancedScoringConfig())
    
    resultado_bowie_bal = engine_balanced.calculate_points(kieron_bowie)
    resultado_camara_bal = engine_balanced.calculate_points(panutche_camara)
    
    print("📊 CON CONFIGURACIÓN BALANCEADA:")
    print("-" * 100)
    print(f"\n🥇 {resultado_bowie_bal.player_name} (Delantero)")
    print(f"   Stats: {kieron_bowie.goals}G (¡2 GOLES!), {kieron_bowie.assists}A")
    print(f"   Puntos: {resultado_bowie_bal.fantasy_points} pts")
    print(f"\n   Desglose:")
    for cat, pts in sorted(resultado_bowie_bal.points_breakdown.items(), key=lambda x: x[1], reverse=True):
        if pts != 0:
            print(f"      {cat:<25}: {pts:>+6.1f} pts")
    
    print(f"\n🥈 {resultado_camara_bal.player_name} (Mediocentro)")
    print(f"   Stats: {panutche_camara.goals}G, {panutche_camara.assists}A, {panutche_camara.tackles} tackles, {panutche_camara.accurate_passes} pases")
    print(f"   Puntos: {resultado_camara_bal.fantasy_points} pts")
    print(f"\n   Desglose:")
    for cat, pts in sorted(resultado_camara_bal.points_breakdown.items(), key=lambda x: x[1], reverse=True):
        if pts != 0:
            print(f"      {cat:<25}: {pts:>+6.1f} pts")
    
    print("\n" + "="*100)
    print("✅ SOLUCIÓN IMPLEMENTADA:")
    print("="*100)
    print(f"""
    El delantero con 2 GOLES ahora tiene {resultado_bowie_bal.fantasy_points} puntos
    El mediocentro con 1 asistencia tiene {resultado_camara_bal.fantasy_points} puntos
    
    ✅ Diferencia: {resultado_bowie_bal.fantasy_points - resultado_camara_bal.fantasy_points} puntos a favor del goleador
    
    ✅ Los GOLES son claramente lo más importante
    ✅ Los acumuladores son BONUS, no lo principal
    ✅ Marcar 2 goles vale más que simplemente "trabajar mucho"
    """)
    
    input("\n🎯 Presiona ENTER para ver COMPARACIÓN LADO A LADO...")
    
    # ========================================
    # PARTE 3: COMPARACIÓN
    # ========================================
    
    print("\n" + "="*100)
    print("PARTE 3: COMPARACIÓN LADO A LADO")
    print("="*100 + "\n")
    
    print(f"{'JUGADOR':<25} | {'CONFIG':<15} | {'PUNTOS':<8} | {'DIFERENCIA':<12}")
    print("-" * 100)
    print(f"{kieron_bowie.player_name:<25} | {'Original':<15} | {resultado_bowie_orig.fantasy_points:<8} | Baseline")
    print(f"{kieron_bowie.player_name:<25} | {'Balanceada':<15} | {resultado_bowie_bal.fantasy_points:<8} | {resultado_bowie_bal.fantasy_points - resultado_bowie_orig.fantasy_points:>+4} pts ({((resultado_bowie_bal.fantasy_points - resultado_bowie_orig.fantasy_points)/resultado_bowie_orig.fantasy_points*100):>+.0f}%)")
    print()
    print(f"{panutche_camara.player_name:<25} | {'Original':<15} | {resultado_camara_orig.fantasy_points:<8} | Baseline")
    print(f"{panutche_camara.player_name:<25} | {'Balanceada':<15} | {resultado_camara_bal.fantasy_points:<8} | {resultado_camara_bal.fantasy_points - resultado_camara_orig.fantasy_points:>+4} pts ({((resultado_camara_bal.fantasy_points - resultado_camara_orig.fantasy_points)/resultado_camara_orig.fantasy_points*100):>+.0f}%)")
    
    input("\n🎮 Presiona ENTER para ver todas las CONFIGURACIONES...")
    
    # ========================================
    # PARTE 4: TODAS LAS CONFIGS
    # ========================================
    
    print("\n" + "="*100)
    print("PARTE 4: COMPARANDO LAS 3 CONFIGURACIONES")
    print("="*100 + "\n")
    
    # Ultra Ofensiva
    engine_offensive = FantasyScoringEngine(OffensiveScoringConfig())
    resultado_bowie_off = engine_offensive.calculate_points(kieron_bowie)
    resultado_camara_off = engine_offensive.calculate_points(panutche_camara)
    
    print(f"{'JUGADOR':<25} | {'CONFIG':<20} | {'PUNTOS':<8} | {'RANKING':<10}")
    print("-" * 100)
    
    # Bowie en las 3 configs
    resultados_bowie = [
        ("Original", resultado_bowie_orig.fantasy_points),
        ("Balanceada", resultado_bowie_bal.fantasy_points),
        ("Ultra Ofensiva", resultado_bowie_off.fantasy_points)
    ]
    
    for config_name, pts in resultados_bowie:
        emoji = "🥇" if config_name == "Balanceada" else "⚡" if config_name == "Ultra Ofensiva" else ""
        print(f"{kieron_bowie.player_name:<25} | {config_name:<20} | {pts:<8} | {emoji}")
    
    print()
    
    # Camara en las 3 configs
    resultados_camara = [
        ("Original", resultado_camara_orig.fantasy_points),
        ("Balanceada", resultado_camara_bal.fantasy_points),
        ("Ultra Ofensiva", resultado_camara_off.fantasy_points)
    ]
    
    for config_name, pts in resultados_camara:
        emoji = "🥇" if config_name == "Original" else ""
        print(f"{panutche_camara.player_name:<25} | {config_name:<20} | {pts:<8} | {emoji}")
    
    print("\n" + "="*100)
    print("ANÁLISIS:")
    print("="*100)
    print("""
    CONFIG ORIGINAL:
      ❌ Camara (1A) > Bowie (2G) - El problema
    
    CONFIG BALANCEADA: ⭐ RECOMENDADA
      ✅ Bowie (2G) > Camara (1A) - Los goles son protagonistas
      ✅ Pero se valora también el trabajo defensivo
      ✅ Balance perfecto entre ataque y defensa
    
    CONFIG ULTRA OFENSIVA:
      ⚡ Bowie (2G) >>> Camara (1A) - Diferencia muy grande
      ⚡ SOLO importa ser decisivo (goles/asistencias)
      ⚡ Ideal para ligas muy ofensivas
    """)
    
    input("\n✨ Presiona ENTER para ver RECOMENDACIONES...")
    
    # ========================================
    # PARTE 5: RECOMENDACIONES
    # ========================================
    
    print("\n" + "="*100)
    print("PARTE 5: ¿QUÉ CONFIGURACIÓN USAR?")
    print("="*100 + "\n")
    
    print("🎯 PARA TU TFG:")
    print("-" * 100)
    print("""
    1. USA LA CONFIG BALANCEADA por defecto
    2. Explica el problema del original en tu memoria
    3. Justifica los cambios con datos reales
    4. Menciona que el sistema es flexible y configurable
    5. Incluye esta demo en tu presentación
    """)
    
    print("\n🎮 PARA TU APLICACIÓN:")
    print("-" * 100)
    print("""
    OPCIÓN 1: Dejar elegir al usuario
    ├─ Liga Equilibrada   → BalancedScoringConfig()
    ├─ Liga Ofensiva      → OffensiveScoringConfig()
    └─ Liga Personalizada → El usuario ajusta valores
    
    OPCIÓN 2: Una sola configuración
    └─ Usar BalancedScoringConfig() por defecto
       (Es la más justa y realista)
    """)
    
    print("\n💻 CÓDIGO DE EJEMPLO:")
    print("-" * 100)
    print("""
    from fantasy_scoring_balanced import BalancedScoringConfig
    from fantasy_scoring_system_improved import analyze_fixture
    
    # Usar config balanceada
    config = BalancedScoringConfig()
    analyze_fixture(19428171, config=config)
    
    # O directamente
    from fantasy_scoring_balanced import analyze_fixture_balanced
    analyze_fixture_balanced(19428171, config_type='balanced')
    """)
    
    print("\n" + "="*100)
    print("✅ DEMO COMPLETADA")
    print("="*100)
    print("""
    Archivos creados:
    ├─ fantasy_scoring_system_improved.py  (Sistema base)
    ├─ fantasy_scoring_balanced.py         (Configs balanceadas)
    ├─ GUIA_CONFIGURACION.md              (Guía completa)
    └─ demo_balanceado.py                 (Este archivo)
    
    Siguiente paso:
    👉 Integra BalancedScoringConfig en tu aplicación
    👉 Prueba con más fixtures de la jornada
    👉 Documenta el proceso en tu TFG
    
    ¡Buena suerte con tu TFG! 🎓⚽
    """)


def ejemplo_rapido():
    """Ejemplo rápido sin interacción"""
    
    print("\n🚀 EJEMPLO RÁPIDO - SISTEMA BALANCEADO\n")
    
    # Delantero con 2 goles
    delantero = PlayerStats(
        player_name="Goleador",
        position=Position.FWD,
        minutes_played=90,
        goals=2,
        rating=7.5
    )
    
    # Mediocentro trabajador
    mediocentro = PlayerStats(
        player_name="Trabajador",
        position=Position.MID,
        minutes_played=90,
        assists=1,
        tackles=10,
        duels_won=12,
        accurate_passes=60,
        rating=7.5
    )
    
    # Calcular con ambas configs
    engine_orig = FantasyScoringEngine(ScoringConfig())
    engine_bal = FantasyScoringEngine(BalancedScoringConfig())
    
    del_orig = engine_orig.calculate_points(delantero)
    del_bal = engine_bal.calculate_points(delantero)
    
    mid_orig = engine_orig.calculate_points(mediocentro)
    mid_bal = engine_bal.calculate_points(mediocentro)
    
    print(f"{'JUGADOR':<20} | {'ORIGINAL':<10} | {'BALANCEADA':<10} | {'CAMBIO':<10}")
    print("-" * 65)
    print(f"{delantero.player_name:<20} | {del_orig.fantasy_points:<10} | {del_bal.fantasy_points:<10} | {del_bal.fantasy_points - del_orig.fantasy_points:>+4} pts")
    print(f"{mediocentro.player_name:<20} | {mid_orig.fantasy_points:<10} | {mid_bal.fantasy_points:<10} | {mid_bal.fantasy_points - mid_orig.fantasy_points:>+4} pts")
    
    print(f"\n✅ Con config balanceada: El goleador ahora es TOP")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        ejemplo_rapido()
    else:
        demo_completa()
