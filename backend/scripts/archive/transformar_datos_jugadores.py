"""
Script para transformar las medias de los jugadores y corregir posiciones
SIN hacer llamadas a la API - Solo modifica la BD existente
"""

import sys
import os
import logging
from sqlalchemy import text

# Desactivar logging verboso
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

# Ajuste de rutas
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Player, Position, CardRarity

# ==========================================
# CONFIGURACIÓN DE TRANSFORMACIÓN
# ==========================================

# Rango actual: 52-79
# Rango nuevo: 60-90 (Callum McGregor = 90)
OVR_MIN_ACTUAL = 52
OVR_MAX_ACTUAL = 79
OVR_MIN_NUEVO = 60
OVR_MAX_NUEVO = 90

# Distribución de rarezas con nuevo sistema:
# Bronze: 60-74 (jugadores normales)
# Silver: 75-84 (jugadores buenos)
# Gold: 85-90 (estrellas)

def transformar_ovr(ovr_actual: int) -> int:
    """
    Transforma el OVR actual a un rango más atractivo
    Usa transformación no-lineal para comprimir bronces y expandir oros
    """
    # Normalizar a 0-1
    normalized = (ovr_actual - OVR_MIN_ACTUAL) / (OVR_MAX_ACTUAL - OVR_MIN_ACTUAL)
    
    # Aplicar transformación exponencial suave para hacer más atractivo
    # Esto hace que los buenos sean MUY buenos y los normales sean decentes
    transformed = normalized ** 0.8  # Exponente < 1 para comprimir abajo y expandir arriba
    
    # Escalar al nuevo rango
    nuevo_ovr = int(OVR_MIN_NUEVO + transformed * (OVR_MAX_NUEVO - OVR_MIN_NUEVO))
    
    return min(max(nuevo_ovr, OVR_MIN_NUEVO), OVR_MAX_NUEVO)


def determinar_rareza_nueva(ovr: int) -> CardRarity:
    """Determina la rareza basada en el nuevo OVR"""
    if ovr >= 85:
        return CardRarity.GOLD
    elif ovr >= 75:
        return CardRarity.SILVER
    else:
        return CardRarity.BRONZE


def calcular_precio_nuevo(ovr: int) -> float:
    """Calcula precio basado en el nuevo OVR"""
    if ovr < 65:
        return 800000 + (ovr - 60) * 80000
    elif ovr < 70:
        return 1500000 + (ovr - 65) * 200000
    elif ovr < 75:
        return 2500000 + (ovr - 70) * 300000
    elif ovr < 80:
        return 4000000 + (ovr - 75) * 600000
    elif ovr < 85:
        return 7000000 + (ovr - 80) * 1200000
    else:  # 85-90 (GOLD)
        return 13000000 + (ovr - 85) * 3000000


def mapear_posicion_correcta(player_name: str, sportmonks_position_id: int) -> Position:
    """
    Mapea la posición correcta basándose en el position_id de Sportmonks
    Position IDs comunes:
    - 24: Goalkeeper (GK)
    - 25-27: Defenders (DEF)
    - 28-30: Midfielders (MID)
    - 31-32: Forwards (FWD)
    """
    # Porteros
    if sportmonks_position_id == 24:
        return Position.GK
    
    # Defensas (25=Defender, 26=Centre-Back, 27=Full-Back, etc.)
    elif 25 <= sportmonks_position_id <= 27:
        return Position.DEF
    
    # Centrocampistas (28=Midfielder, 29=Defensive Mid, 30=Attacking Mid)
    elif 28 <= sportmonks_position_id <= 30:
        return Position.MID
    
    # Delanteros (31=Attacker, 32=Forward, 33=Striker)
    elif 31 <= sportmonks_position_id <= 33:
        return Position.FWD
    
    # Por defecto, intentar deducir del nombre o asumir MID
    else:
        # Porteros por nombre
        if any(word in player_name.lower() for word in ['keeper', 'goalkeeper', 'gk']):
            return Position.GK
        return Position.MID


def actualizar_stats_proporcionalmente(player, nuevo_ovr: int):
    """Actualiza las stats del jugador proporcionalmente al nuevo OVR"""
    ovr_antiguo = player.overall_rating
    
    # Si el OVR antiguo es muy bajo, no queremos una diferencia brutal
    if ovr_antiguo < 55:
        ovr_antiguo = 55
    
    # Factor de escala
    factor = nuevo_ovr / ovr_antiguo if ovr_antiguo > 0 else 1.2
    
    # Limitar el factor para evitar stats irreales
    factor = min(factor, 1.5)
    factor = max(factor, 0.9)
    
    # Actualizar stats
    player.pace = min(99, max(20, int(player.pace * factor)))
    player.shooting = min(99, max(20, int(player.shooting * factor)))
    player.passing = min(99, max(20, int(player.passing * factor)))
    player.dribbling = min(99, max(20, int(player.dribbling * factor)))
    player.defending = min(99, max(20, int(player.defending * factor)))
    player.physical = min(99, max(20, int(player.physical * factor)))
    
    # Actualizar potential también
    player.potential = min(99, nuevo_ovr + 3)


def ejecutar_transformacion():
    """Ejecuta la transformación completa de la base de datos"""
    
    print("="*60)
    print("🔄 TRANSFORMACIÓN DE DATOS - SIN API")
    print("="*60 + "\n")
    
    db = SessionLocal()
    
    try:
        # 1. Obtener todos los jugadores
        print("📊 Cargando jugadores de la base de datos...")
        players = db.query(Player).all()
        print(f"✅ {len(players)} jugadores encontrados\n")
        
        # 2. Mostrar estadísticas actuales
        print("📈 ANTES DE LA TRANSFORMACIÓN:")
        result = db.execute(text("""
            SELECT 
                MIN(overall_rating) as min_ovr,
                MAX(overall_rating) as max_ovr,
                AVG(overall_rating) as avg_ovr,
                COUNT(*) as total
            FROM players
        """))
        stats = result.fetchone()
        print(f"   OVR: {stats[0]} - {stats[1]} (promedio: {stats[2]:.1f})")
        print(f"   Total: {stats[3]} jugadores")
        
        # Distribución de posiciones actual
        result = db.execute(text("""
            SELECT position, COUNT(*) as count
            FROM players
            GROUP BY position
            ORDER BY count DESC
        """))
        print(f"\n   Posiciones actuales:")
        for row in result:
            print(f"      {row[0]}: {row[1]}")
        
        print("\n" + "="*60)
        print("🔄 TRANSFORMANDO JUGADORES...")
        print("="*60 + "\n")
        
        # 3. Transformar cada jugador
        transformados = 0
        posiciones_corregidas = 0
        
        for i, player in enumerate(players, 1):
            # Obtener OVR antiguo
            ovr_antiguo = player.overall_rating
            
            # Transformar OVR
            nuevo_ovr = transformar_ovr(ovr_antiguo)
            
            # Corregir posición (aquí necesitamos el position_id de los datos originales)
            # Como no tenemos position_id almacenado, vamos a usar una lógica basada en stats
            posicion_antigua = player.position
            
            # Lógica para corregir posición basada en stats
            if player.defending > player.pace and player.defending > player.shooting:
                if player.shooting < 30:  # Probablemente portero
                    nueva_posicion = Position.GK
                else:
                    nueva_posicion = Position.DEF
            elif player.shooting > player.defending and player.pace > player.defending:
                nueva_posicion = Position.FWD
            else:
                nueva_posicion = Position.MID
            
            # Si era MID y no tiene sentido, mantener MID
            if posicion_antigua == Position.MID and nueva_posicion == Position.MID:
                # Usar el nombre para detectar porteros
                if 'keeper' in player.name.lower() or 'schmeichel' in player.name.lower():
                    nueva_posicion = Position.GK
            
            # Actualizar jugador
            player.overall_rating = nuevo_ovr
            player.position = nueva_posicion
            player.base_rarity = determinar_rareza_nueva(nuevo_ovr)
            player.current_price = calcular_precio_nuevo(nuevo_ovr)
            player.target_price = player.current_price
            
            # Actualizar stats proporcionalmente
            actualizar_stats_proporcionalmente(player, nuevo_ovr)
            
            transformados += 1
            if posicion_antigua != nueva_posicion:
                posiciones_corregidas += 1
            
            # Mostrar progreso cada 50
            if i % 50 == 0:
                print(f"   Procesados: {i}/{len(players)}")
        
        # Commit
        db.commit()
        print(f"\n✅ Transformación completada: {transformados} jugadores")
        print(f"✅ Posiciones corregidas: {posiciones_corregidas}\n")
        
        # 4. Mostrar estadísticas nuevas
        print("="*60)
        print("📊 DESPUÉS DE LA TRANSFORMACIÓN:")
        print("="*60 + "\n")
        
        result = db.execute(text("""
            SELECT 
                MIN(overall_rating) as min_ovr,
                MAX(overall_rating) as max_ovr,
                AVG(overall_rating) as avg_ovr
            FROM players
        """))
        stats = result.fetchone()
        print(f"   OVR: {stats[0]} - {stats[1]} (promedio: {stats[2]:.1f})")
        
        # Distribución por rarezas
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
        print(f"\n   Distribución por rarezas:")
        for row in result:
            porcentaje = (row[1] / len(players)) * 100
            print(f"      {row[0]}: {row[1]} ({porcentaje:.1f}%)")
        
        # Distribución de posiciones
        result = db.execute(text("""
            SELECT position, COUNT(*) as count
            FROM players
            GROUP BY position
            ORDER BY count DESC
        """))
        print(f"\n   Distribución por posiciones:")
        for row in result:
            porcentaje = (row[1] / len(players)) * 100
            print(f"      {row[0]}: {row[1]} ({porcentaje:.1f}%)")
        
        # Top 10 jugadores
        result = db.execute(text("""
            SELECT name, position, overall_rating, current_team, base_rarity
            FROM players
            ORDER BY overall_rating DESC
            LIMIT 10
        """))
        print(f"\n⭐ Top 10 jugadores:")
        for row in result:
            print(f"   {row[0]} ({row[1]}) - OVR {row[2]} [{row[4]}] - {row[3]}")
        
        print("\n" + "="*60)
        print("✅ TRANSFORMACIÓN COMPLETADA EXITOSAMENTE")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    ejecutar_transformacion()
