"""
Script de Actualización de Fin de Semana
Se ejecuta TRAS LOS PARTIDOS (Domingos por la noche)

Función:
1. Recoge estadísticas de los partidos del fin de semana desde Sportmonks
2. Calcula los puntos Fantasy de cada jugador
3. Establece los PRECIOS OBJETIVO basados en rendimiento
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import SessionLocal, test_connection
from app.models.models import Player, PlayerMatchStats, Gameweek, Match, Position
from app.services.calculator import calculator
from app.services.economy import PriceInertiaSystem
from datetime import datetime


def update_weekend_stats():
    """
    Actualización de fin de semana completa
    """
    
    print("🏁 ACTUALIZACIÓN DE FIN DE SEMANA")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Verificar conexión
    if not test_connection():
        print("❌ Error: No se pudo conectar a la base de datos")
        return
    
    db = SessionLocal()
    economy_system = PriceInertiaSystem(db)
    
    try:
        # 1. Obtener la jornada activa
        active_gameweek = db.query(Gameweek).filter(Gameweek.is_active == True).first()
        
        if not active_gameweek:
            print("⚠️ No hay jornada activa")
            return
        
        print(f"📅 Jornada {active_gameweek.number} - Procesando...\n")
        
        # 2. Obtener todos los partidos de esta jornada
        matches = (
            db.query(Match)
            .filter(Match.gameweek_id == active_gameweek.id)
            .all()
        )
        
        print(f"⚽ {len(matches)} partidos encontrados\n")
        
        # 3. Procesar estadísticas de cada partido
        total_players_updated = 0
        total_points_calculated = 0
        
        for match in matches:
            print(f"  {match.home_team} {match.home_score} - {match.away_score} {match.away_team}")
            
            # Obtener estadísticas de jugadores en este partido
            player_stats = (
                db.query(PlayerMatchStats)
                .filter(PlayerMatchStats.match_id == match.id)
                .all()
            )
            
            for stats in player_stats:
                # Obtener el jugador para saber su posición
                player = db.query(Player).filter(Player.id == stats.player_id).first()
                
                if not player:
                    continue
                
                # Calcular puntos Fantasy
                fantasy_points = calculator.calculate_total_points(stats, player.position)
                
                # Actualizar en la BD
                stats.fantasy_points = fantasy_points
                
                total_points_calculated += fantasy_points
                total_players_updated += 1
                
                print(f"    ✅ {player.name} ({player.position.value}): {fantasy_points:.1f} puntos")
        
        db.commit()
        
        print(f"\n📊 RESUMEN:")
        print(f"   - Jugadores procesados: {total_players_updated}")
        print(f"   - Puntos totales generados: {total_points_calculated:.1f}")
        
        # 4. Establecer PRECIOS OBJETIVO basados en rendimiento
        print(f"\n💰 ACTUALIZANDO PRECIOS OBJETIVO...\n")
        
        # Obtener todos los jugadores que participaron
        active_players = (
            db.query(Player)
            .join(PlayerMatchStats)
            .filter(PlayerMatchStats.match_id.in_([m.id for m in matches]))
            .distinct()
            .all()
        )
        
        price_changes = []
        
        for player in active_players:
            if player.is_legend:
                continue  # Las leyendas no fluctúan
            
            result = economy_system.set_target_price(player.id)
            
            price_changes.append({
                "name": player.name,
                "old": result["old_target"],
                "new": result["new_target"],
                "change_pct": result["change_percentage"]
            })
        
        # Mostrar top 10 subidas y bajadas
        price_changes.sort(key=lambda x: x["change_pct"], reverse=True)
        
        print("📈 TOP 5 SUBIDAS:")
        for pc in price_changes[:5]:
            print(f"   ↗️  {pc['name']}: €{pc['old']:,.0f} → €{pc['new']:,.0f} ({pc['change_pct']:+.1f}%)")
        
        print("\n📉 TOP 5 BAJADAS:")
        for pc in price_changes[-5:]:
            print(f"   ↘️  {pc['name']}: €{pc['old']:,.0f} → €{pc['new']:,.0f} ({pc['change_pct']:+.1f}%)")
        
        # 5. Marcar la jornada como finalizada
        active_gameweek.is_active = False
        active_gameweek.is_finished = True
        db.commit()
        
        print(f"\n✅ Jornada {active_gameweek.number} marcada como finalizada")
        print("\n" + "=" * 60)
        print("🎉 ACTUALIZACIÓN COMPLETADA CON ÉXITO")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    update_weekend_stats()
