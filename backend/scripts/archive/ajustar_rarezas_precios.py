"""
Script para ajustar rarezas, posiciones y precios
SIN llamadas a la API - Solo modifica la BD
"""

import sys
import os
import logging
from sqlalchemy import text
import random

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Player, Position, CardRarity

# ==========================================
# NUEVAS CONFIGURACIONES
# ==========================================

def determinar_rareza_nueva(ovr: int) -> CardRarity:
    """
    Nueva distribución de rarezas:
    - GOLD: 78+ (más oros)
    - SILVER: 70-77
    - BRONZE: 60-69
    """
    if ovr >= 78:
        return CardRarity.GOLD
    elif ovr >= 70:
        return CardRarity.SILVER
    else:
        return CardRarity.BRONZE


def calcular_precio_nuevo(ovr: int) -> float:
    """
    Nuevo sistema de precios con jugadores de 90 OVR valiendo 70-80M
    """
    # Base exponencial para que crezca más rápido
    if ovr < 65:
        base = 1000000
        factor = (ovr - 60) * 150000
    elif ovr < 70:
        base = 1800000
        factor = (ovr - 65) * 300000
    elif ovr < 75:
        base = 3300000
        factor = (ovr - 70) * 600000
    elif ovr < 80:
        base = 6300000
        factor = (ovr - 75) * 1200000
    elif ovr < 85:
        base = 12300000
        factor = (ovr - 80) * 3000000
    else:  # 85-90 - Los más caros
        # OVR 85: ~27M
        # OVR 90: 70-80M
        base = 27300000
        factor = (ovr - 85) * 10000000  # 10M por punto de OVR
    
    precio_base = base + factor
    
    # Añadir variación aleatoria ±5%
    variacion = random.uniform(0.95, 1.05)
    
    return int(precio_base * variacion)


def rebalancear_posiciones_inteligente(players):
    """
    Convierte algunos MID en DEF o FWD basándose en sus stats
    para lograr una distribución más equilibrada
    """
    mid_players = [p for p in players if p.position == Position.MID]
    
    # Objetivo: reducir MID de ~180 a ~135 (40% del total)
    # Necesitamos convertir ~45 MID
    
    convertidos = 0
    objetivo = 45
    
    for player in mid_players:
        if convertidos >= objetivo:
            break
        
        # Convertir a DEF si tiene defending alto
        if player.defending > player.shooting and player.defending > 70:
            player.position = Position.DEF
            convertidos += 1
        # Convertir a FWD si tiene shooting y pace altos
        elif player.shooting > player.defending and player.pace > 70:
            player.position = Position.FWD
            convertidos += 1
        # Convertir a FWD si tiene shooting muy alto
        elif player.shooting > 75 and player.defending < 60:
            player.position = Position.FWD
            convertidos += 1
    
    return convertidos


def ejecutar_ajustes():
    """Ejecuta todos los ajustes en la base de datos"""
    
    print("="*60)
    print("🔧 AJUSTES FINALES - RAREZAS, POSICIONES Y PRECIOS")
    print("="*60 + "\n")
    
    db = SessionLocal()
    
    try:
        # 1. Cargar todos los jugadores
        players = db.query(Player).all()
        print(f"📊 Total jugadores: {len(players)}\n")
        
        # 2. ESTADÍSTICAS ANTES
        print("📈 ANTES DE LOS AJUSTES:")
        print("-" * 60)
        
        # Rarezas
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
        print("\n   Rarezas:")
        for row in result:
            porcentaje = (row[1] / len(players)) * 100
            print(f"      {row[0]}: {row[1]} ({porcentaje:.1f}%)")
        
        # Posiciones
        result = db.execute(text("""
            SELECT position, COUNT(*) as count
            FROM players
            GROUP BY position
            ORDER BY count DESC
        """))
        print("\n   Posiciones:")
        for row in result:
            porcentaje = (row[1] / len(players)) * 100
            print(f"      {row[0]}: {row[1]} ({porcentaje:.1f}%)")
        
        # Precio promedio por rareza
        result = db.execute(text("""
            SELECT base_rarity, 
                   AVG(current_price) as avg_price,
                   MAX(current_price) as max_price
            FROM players
            GROUP BY base_rarity
        """))
        print("\n   Precios promedio:")
        for row in result:
            print(f"      {row[0]}: €{row[1]:,.0f} (máx: €{row[2]:,.0f})")
        
        # 3. APLICAR AJUSTES
        print("\n" + "="*60)
        print("🔄 APLICANDO AJUSTES...")
        print("="*60 + "\n")
        
        rarezas_cambiadas = 0
        posiciones_cambiadas = 0
        
        # Ajustar rarezas y precios
        for player in players:
            # Nueva rareza
            nueva_rareza = determinar_rareza_nueva(player.overall_rating)
            if nueva_rareza != player.base_rarity:
                player.base_rarity = nueva_rareza
                rarezas_cambiadas += 1
            
            # Nuevo precio
            player.current_price = calcular_precio_nuevo(player.overall_rating)
            player.target_price = player.current_price
        
        print(f"✅ Rarezas actualizadas: {rarezas_cambiadas}")
        
        # Rebalancear posiciones
        convertidos = rebalancear_posiciones_inteligente(players)
        print(f"✅ Posiciones rebalanceadas: {convertidos} MID convertidos\n")
        
        # Commit
        db.commit()
        
        # 4. ESTADÍSTICAS DESPUÉS
        print("="*60)
        print("📊 DESPUÉS DE LOS AJUSTES:")
        print("-" * 60)
        
        # Rarezas
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
        print("\n   Rarezas:")
        for row in result:
            porcentaje = (row[1] / len(players)) * 100
            print(f"      {row[0]}: {row[1]} ({porcentaje:.1f}%)")
        
        # Posiciones
        result = db.execute(text("""
            SELECT position, COUNT(*) as count
            FROM players
            GROUP BY position
            ORDER BY count DESC
        """))
        print("\n   Posiciones:")
        for row in result:
            porcentaje = (row[1] / len(players)) * 100
            print(f"      {row[0]}: {row[1]} ({porcentaje:.1f}%)")
        
        # Precios por rareza
        result = db.execute(text("""
            SELECT base_rarity, 
                   AVG(current_price) as avg_price,
                   MAX(current_price) as max_price,
                   MIN(current_price) as min_price
            FROM players
            GROUP BY base_rarity
        """))
        print("\n   Precios:")
        for row in result:
            print(f"      {row[0]}:")
            print(f"         Promedio: €{row[1]:,.0f}")
            print(f"         Máximo: €{row[2]:,.0f}")
            print(f"         Mínimo: €{row[3]:,.0f}")
        
        # Top 10 jugadores con nuevos precios
        result = db.execute(text("""
            SELECT name, position, overall_rating, base_rarity, current_price, current_team
            FROM players
            ORDER BY overall_rating DESC, current_price DESC
            LIMIT 10
        """))
        print("\n⭐ Top 10 jugadores con nuevos precios:")
        for i, row in enumerate(result, 1):
            print(f"   {i}. {row[0]} ({row[1]}) - OVR {row[2]} [{row[3]}]")
            print(f"      Precio: €{row[4]:,.0f} - {row[5]}")
        
        # Valor total del mercado
        result = db.execute(text("SELECT SUM(current_price) FROM players"))
        total = result.fetchone()[0]
        print(f"\n💰 Valor total del mercado: €{total:,.0f}")
        
        print("\n" + "="*60)
        print("✅ AJUSTES COMPLETADOS")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    ejecutar_ajustes()
