"""
MIGRACIÓN JORNADA 1 - Usando Sistema Profesional Rebalanceado
"""

import sys
sys.path.append('c:\\Users\\abdul22\\OneDrive\\Escritorio\\ProyectoFinCurso\\backend\\scripts')

from sistema_puntos_oficial import (
    analyze_fixture,
    ScoringConfig,
    FantasyScoringEngine,
    SportmonksAPIClient,
    StatsExtractor,
    logger
)

FIXTURES_JORNADA_1 = [
    19428039,  # Kilmarnock vs Livingston
    19428040,  # Motherwell vs Rangers
    19428041,  # Falkirk vs Dundee United
    19428042,  # Dundee vs Hibernian
    19428043,  # Celtic vs St. Mirren
]

print("\n" + "="*130)
print("📅 MIGRACIÓN JORNADA 1 - Sistema Profesional Rebalanceado ✅")
print("="*130 + "\n")

all_players = []

for idx, fixture_id in enumerate(FIXTURES_JORNADA_1, 1):
    print(f"\n{'='*130}")
    print(f"Partido {idx}/{len(FIXTURES_JORNADA_1)}")
    print(f"{'='*130}")
    
    players = analyze_fixture(fixture_id, show_detailed=False, top_n=0)
    if players:
        all_players.extend([p for p in players if p.minutes_played > 0])

# Resumen global
print("\n" + "="*130)
print("📊 RESUMEN JORNADA 1 COMPLETA")
print("="*130 + "\n")

all_players.sort(key=lambda x: x.fantasy_points, reverse=True)

print(f"✅ Total jugadores procesados: {len(all_players)}\n")

print("🏆 TOP 20 JUGADORES:\n")
print(f"{'#':<3} | {'JUGADOR':<25} | {'POS':<10} | {'MIN':<3} | {'GOL':<3} | {'AST':<3} | {'NOTA':<5} | {'PUNTOS'}")
print("-" * 130)

for idx, player in enumerate(all_players[:20], 1):
    print(f"{idx:<3} | {player.player_name:<25} | {str(player.position):<10} | "
          f"{player.minutes_played:<3} | {player.goals:<3} | {player.assists:<3} | "
          f"{player.rating:<5.1f} | {player.fantasy_points}")

# Estadísticas
total_puntos = sum(p.fantasy_points for p in all_players)
promedio = total_puntos / len(all_players) if all_players else 0

print(f"\n📈 ESTADÍSTICAS:")
print(f"   - Puntos totales: {total_puntos}")
print(f"   - Promedio: {promedio:.2f} pts/jugador")
print(f"   - Máximo: {all_players[0].fantasy_points} pts ({all_players[0].player_name})")
print(f"   - Mínimo: {all_players[-1].fantasy_points} pts ({all_players[-1].player_name})")

print("\n" + "="*130 + "\n")
