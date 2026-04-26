"""
Script de Actualización Diaria
Se ejecuta LUNES a VIERNES (entre semana)

Función:
Aplica INERCIA a los precios, moviéndolos gradualmente hacia el precio objetivo
establecido el fin de semana.

Esto evita volatilidad extrema y crea un mercado más realista.
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import SessionLocal, test_connection
from app.models.models import Player
from app.services.economy import PriceInertiaSystem
from datetime import datetime


def update_daily_prices():
    """
    Actualización diaria de precios con inercia
    """
    
    print("📊 ACTUALIZACIÓN DIARIA DE PRECIOS")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Aplicando inercia de precios...\n")
    
    # Verificar conexión
    if not test_connection():
        print("❌ Error: No se pudo conectar a la base de datos")
        return
    
    db = SessionLocal()
    economy_system = PriceInertiaSystem(db)
    
    try:
        # Obtener todos los jugadores activos (no leyendas)
        active_players = (
            db.query(Player)
            .filter(Player.is_legend == False)
            .all()
        )
        
        print(f"🔧 Procesando {len(active_players)} jugadores...\n")
        
        movements = []
        
        for player in active_players:
            result = economy_system.apply_daily_inertia(player.id)
            
            # Solo registrar movimientos significativos (> €1000)
            if abs(result["movement"]) > 1000:
                movements.append({
                    "name": player.name,
                    "position": player.position.value,
                    "old": result["old_price"],
                    "new": result["new_price"],
                    "target": result["target_price"],
                    "movement": result["movement"],
                    "movement_pct": result["movement_percentage"]
                })
        
        # Ordenar por mayor movimiento absoluto
        movements.sort(key=lambda x: abs(x["movement"]), reverse=True)
        
        print("📊 RESUMEN DE MOVIMIENTOS SIGNIFICATIVOS:")
        print(f"   Total jugadores con cambios > €1000: {len(movements)}\n")
        
        if movements:
            print("🔝 TOP 10 MOVIMIENTOS MÁS GRANDES:\n")
            
            for i, m in enumerate(movements[:10], 1):
                direction = "↗️" if m["movement"] > 0 else "↘️"
                print(f"{i:2d}. {direction} {m['name']} ({m['position']})")
                print(f"     €{m['old']:,.0f} → €{m['new']:,.0f} ({m['movement_pct']:+.2f}%)")
                print(f"     Objetivo: €{m['target']:,.0f}")
                print()
        else:
            print("   ✅ No hay movimientos significativos hoy")
            print("   📍 Los precios están estables cerca de sus objetivos")
        
        # Estadísticas generales
        total_increases = sum(1 for m in movements if m["movement"] > 0)
        total_decreases = sum(1 for m in movements if m["movement"] < 0)
        
        print("\n" + "=" * 60)
        print("📈 ESTADÍSTICAS:")
        print(f"   Subidas: {total_increases}")
        print(f"   Bajadas: {total_decreases}")
        print(f"   Sin cambios significativos: {len(active_players) - len(movements)}")
        
        print("\n✅ ACTUALIZACIÓN DIARIA COMPLETADA")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    update_daily_prices()
