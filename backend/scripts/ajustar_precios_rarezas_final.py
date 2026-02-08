"""
Script para ajustar PRECIOS y RAREZAS de la base de datos

NUEVAS RAREZAS:
- BRONZE: 60-69
- SILVER: 70-77
- GOLD: 78-90

NUEVOS PRECIOS:
- OVR 90 = EUR 85,000,000
- Decrecimiento exponencial hacia valores mas bajos
"""

import sys
import os
from sqlalchemy import text
import logging

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Player, Position, CardRarity


def determinar_rareza(ovr: int) -> CardRarity:
    """Nueva distribucion de rarezas"""
    if ovr >= 78:
        return CardRarity.GOLD
    elif ovr >= 70:
        return CardRarity.SILVER
    else:
        return CardRarity.BRONZE


def calcular_precio_exponencial(ovr: int, position: Position) -> float:
    """
    Calcula precio con OVR 90 = 85M EUR
    Decrecimiento exponencial
    """
    # Multiplicador por posicion (GK y DEF valen menos, FWD valen mas)
    position_multiplier = {
        Position.GK: 0.85,
        Position.DEF: 0.90,
        Position.MID: 1.0,
        Position.FWD: 1.15
    }
    
    multiplier = position_multiplier.get(position, 1.0)
    
    # Formula exponencial
    # OVR 90 = 85M, OVR 60 = ~500K
    # Usamos formula: precio = base * e^(k * ovr)
    
    # Puntos de referencia:
    # OVR 90 -> 85,000,000
    # OVR 85 -> ~45,000,000
    # OVR 80 -> ~22,000,000
    # OVR 75 -> ~10,000,000
    # OVR 70 -> ~4,500,000
    # OVR 65 -> ~2,000,000
    # OVR 60 -> ~800,000
    
    if ovr >= 88:
        base = 60000000 + (ovr - 88) * 12500000  # 60M - 85M
    elif ovr >= 85:
        base = 45000000 + (ovr - 85) * 5000000   # 45M - 60M
    elif ovr >= 82:
        base = 30000000 + (ovr - 82) * 5000000   # 30M - 45M
    elif ovr >= 80:
        base = 22000000 + (ovr - 80) * 4000000   # 22M - 30M
    elif ovr >= 78:
        base = 16000000 + (ovr - 78) * 3000000   # 16M - 22M
    elif ovr >= 75:
        base = 10000000 + (ovr - 75) * 2000000   # 10M - 16M
    elif ovr >= 72:
        base = 6500000 + (ovr - 72) * 1166666    # 6.5M - 10M
    elif ovr >= 70:
        base = 4500000 + (ovr - 70) * 1000000    # 4.5M - 6.5M
    elif ovr >= 68:
        base = 3200000 + (ovr - 68) * 650000     # 3.2M - 4.5M
    elif ovr >= 65:
        base = 2000000 + (ovr - 65) * 400000     # 2M - 3.2M
    elif ovr >= 62:
        base = 1200000 + (ovr - 62) * 266666     # 1.2M - 2M
    else:
        base = 800000 + (ovr - 60) * 200000      # 800K - 1.2M
    
    return base * multiplier


def ajustar_precios_rarezas():
    """Ajusta precios y rarezas de todos los jugadores"""
    
    print("=" * 80)
    print("AJUSTAR PRECIOS Y RAREZAS")
    print("=" * 80 + "\n")
    
    db = SessionLocal()
    
    try:
        # Obtener jugadores
        players = db.query(Player).all()
        print(f"Jugadores en BD: {len(players)}\n")
        
        # ANTES
        print("=" * 80)
        print("ANTES:")
        print("=" * 80)
        
        result = db.execute(text("""
            SELECT base_rarity, COUNT(*) as count
            FROM players
            GROUP BY base_rarity
            ORDER BY 
                CASE base_rarity
                    WHEN 'GOLD' THEN 1
                    WHEN 'SILVER' THEN 2
                    WHEN 'BRONZE' THEN 3
                END
        """))
        print("\nRarezas:")
        for row in result:
            pct = (row[1] / len(players)) * 100
            print(f"  {row[0]}: {row[1]} ({pct:.1f}%)")
        
        result = db.execute(text("""
            SELECT AVG(current_price), MIN(current_price), MAX(current_price)
            FROM players
        """))
        stats = result.fetchone()
        print(f"\nPrecios:")
        print(f"  Promedio: EUR {stats[0]:,.0f}")
        print(f"  Minimo: EUR {stats[1]:,.0f}")
        print(f"  Maximo: EUR {stats[2]:,.0f}")
        
        # AJUSTAR
        print("\n" + "=" * 80)
        print("AJUSTANDO...")
        print("=" * 80 + "\n")
        
        rarezas_cambiadas = 0
        precios_cambiados = 0
        
        for player in players:
            # Nueva rareza
            nueva_rareza = determinar_rareza(player.overall_rating)
            if nueva_rareza != player.base_rarity:
                player.base_rarity = nueva_rareza
                rarezas_cambiadas += 1
            
            # Nuevo precio
            nuevo_precio = calcular_precio_exponencial(player.overall_rating, player.position)
            player.current_price = nuevo_precio
            player.target_price = nuevo_precio
            precios_cambiados += 1
        
        # Commit
        db.commit()
        print(f"Rarezas actualizadas: {rarezas_cambiadas}")
        print(f"Precios actualizados: {precios_cambiados}\n")
        
        # DESPUES
        print("=" * 80)
        print("DESPUES:")
        print("=" * 80)
        
        result = db.execute(text("""
            SELECT base_rarity, COUNT(*) as count
            FROM players
            GROUP BY base_rarity
            ORDER BY 
                CASE base_rarity
                    WHEN 'GOLD' THEN 1
                    WHEN 'SILVER' THEN 2
                    WHEN 'BRONZE' THEN 3
                END
        """))
        print("\nRarezas:")
        for row in result:
            pct = (row[1] / len(players)) * 100
            print(f"  {row[0]}: {row[1]} ({pct:.1f}%)")
        
        result = db.execute(text("""
            SELECT AVG(current_price), MIN(current_price), MAX(current_price)
            FROM players
        """))
        stats = result.fetchone()
        print(f"\nPrecios:")
        print(f"  Promedio: EUR {stats[0]:,.0f}")
        print(f"  Minimo: EUR {stats[1]:,.0f}")
        print(f"  Maximo: EUR {stats[2]:,.0f}")
        
        # TOP 10
        print("\n" + "=" * 80)
        print("TOP 10 JUGADORES:")
        print("=" * 80 + "\n")
        
        result = db.execute(text("""
            SELECT name, position, overall_rating, current_team, base_rarity, current_price
            FROM players
            ORDER BY overall_rating DESC, current_price DESC
            LIMIT 10
        """))
        
        for i, row in enumerate(result, 1):
            print(f"{i}. {row[0]} ({row[1]}) - OVR {row[2]} [{row[4]}] - {row[3]}")
            print(f"   Precio: EUR {row[5]:,.0f}\n")
        
        print("=" * 80)
        print("AJUSTE COMPLETADO")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    ajustar_precios_rarezas()
