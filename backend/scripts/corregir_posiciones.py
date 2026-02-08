"""
Script para corregir las posiciones usando los datos de Sportmonks
que ya están en la base de datos (sportmonks_id permite consultar)
"""

import sys
import os
import logging
from sqlalchemy import text

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Player, Position

# Mapeo de nombres que indican posición
PORTEROS_KEYWORDS = ['keeper', 'schmeichel', 'gordon', 'clark', 'kelly', 'sinisalo', 'mitov']
DEFENSAS_KEYWORDS = ['carter-vickers', 'johnston', 'tierney', 'taylor', 'scales', 'welsh', 
                     'tavernier', 'goldson', 'souttar', 'yilmaz', 'proctor', 'devlin',
                     'kingsley', 'kent']
DELANTEROS_KEYWORDS = ['maeda', 'kyogo', 'idah', 'forrest', 'jota', 'yang', 'palma',
                       'dessers', 'colak', 'matondo', 'lawrence', 'cantwell']

def detectar_posicion_por_nombre(nombre: str) -> Position:
    """Detecta la posición basándose en el nombre del jugador"""
    nombre_lower = nombre.lower()
    
    # Porteros
    for keyword in PORTEROS_KEYWORDS:
        if keyword in nombre_lower:
            return Position.GK
    
    # Delanteros
    for keyword in DELANTEROS_KEYWORDS:
        if keyword in nombre_lower:
            return Position.FWD
    
    # Defensas
    for keyword in DEFENSAS_KEYWORDS:
        if keyword in nombre_lower:
            return Position.DEF
    
    return None


def detectar_posicion_por_stats(player) -> Position:
    """Detecta la posición basándose en las estadísticas del jugador"""
    
    # Porteros: defending alto, shooting muy bajo
    if player.shooting < 40 and player.defending > 60:
        return Position.GK
    
    # Defensas: defending alto, shooting bajo
    if player.defending > 70 and player.shooting < 60:
        return Position.DEF
    
    # Delanteros: shooting alto, defending bajo
    if player.shooting > 65 and player.defending < 50:
        return Position.FWD
    
    # Delanteros alternativos: pace y dribbling altos
    if player.pace > 75 and player.dribbling > 70 and player.defending < 55:
        return Position.FWD
    
    # Por defecto: MID
    return Position.MID


def corregir_posiciones():
    """Corrige las posiciones de todos los jugadores"""
    
    print("="*60)
    print("🔧 CORRECCIÓN DE POSICIONES")
    print("="*60 + "\n")
    
    db = SessionLocal()
    
    try:
        # Obtener todos los jugadores
        players = db.query(Player).all()
        print(f"📊 Total jugadores: {len(players)}\n")
        
        # Estadísticas antes
        print("📈 ANTES:")
        result = db.execute(text("""
            SELECT position, COUNT(*) as count
            FROM players
            GROUP BY position
            ORDER BY 
                CASE position
                    WHEN 'GK' THEN 1
                    WHEN 'DEF' THEN 2
                    WHEN 'MID' THEN 3
                    WHEN 'FWD' THEN 4
                END
        """))
        for row in result:
            porcentaje = (row[1] / len(players)) * 100
            print(f"   {row[0]}: {row[1]} ({porcentaje:.1f}%)")
        
        print("\n" + "="*60)
        print("🔄 Corrigiendo posiciones...")
        print("="*60 + "\n")
        
        corregidos = 0
        
        for player in players:
            posicion_original = player.position
            
            # Intentar detectar por nombre primero
            nueva_posicion = detectar_posicion_por_nombre(player.name)
            
            # Si no se detectó por nombre, usar stats
            if nueva_posicion is None:
                nueva_posicion = detectar_posicion_por_stats(player)
            
            # Actualizar si cambió
            if nueva_posicion != posicion_original:
                player.position = nueva_posicion
                corregidos += 1
                
                # Mostrar algunos ejemplos
                if corregidos <= 20:
                    print(f"   {player.name}: {posicion_original.value} → {nueva_posicion.value}")
        
        # Commit
        db.commit()
        print(f"\n✅ Posiciones corregidas: {corregidos}/{len(players)}\n")
        
        # Estadísticas después
        print("="*60)
        print("📊 DESPUÉS:")
        print("="*60 + "\n")
        
        result = db.execute(text("""
            SELECT position, COUNT(*) as count
            FROM players
            GROUP BY position
            ORDER BY 
                CASE position
                    WHEN 'GK' THEN 1
                    WHEN 'DEF' THEN 2
                    WHEN 'MID' THEN 3
                    WHEN 'FWD' THEN 4
                END
        """))
        
        for row in result:
            porcentaje = (row[1] / len(players)) * 100
            print(f"   {row[0]}: {row[1]} ({porcentaje:.1f}%)")
        
        # Mostrar algunos jugadores de cada posición
        print("\n📋 Ejemplos por posición:\n")
        
        for pos in [Position.GK, Position.DEF, Position.MID, Position.FWD]:
            print(f"   {pos.value}:")
            result = db.execute(text(f"""
                SELECT name, overall_rating
                FROM players
                WHERE position = '{pos.value}'
                ORDER BY overall_rating DESC
                LIMIT 5
            """))
            for row in result:
                print(f"      - {row[0]} (OVR {row[1]})")
            print()
        
        print("="*60)
        print("✅ CORRECCIÓN COMPLETADA")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    corregir_posiciones()
