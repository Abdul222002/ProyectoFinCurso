"""
Script COMPLETO para corregir TODOS los datos de jugadores:
1. Transformar OVR (52-79) -> (60-90)
2. Corregir posiciones usando FIFA CSV
3. Corregir nacionalidades usando FIFA CSV
4. Recalcular precios con formula correcta
"""

import sys
import os
import pandas as pd
from fuzzywuzzy import fuzz
from sqlalchemy import text
import logging

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Player, Position, CardRarity

CSV_PATH = os.path.join(os.path.dirname(__file__), '../data/EAFC26-Men.csv')

# ==============================================================================
# TRANSFORMACION DE OVR
# ==============================================================================

def transformar_ovr(ovr_actual: int) -> int:
    """Transforma OVR del rango FIFA (52-79) al rango ficticio (60-90)"""
    if ovr_actual >= 85:
        return min(90, ovr_actual + 3)
    elif ovr_actual >= 80:
        return min(89, ovr_actual + 5)
    elif ovr_actual >= 75:
        return min(84, ovr_actual + 7)
    elif ovr_actual >= 70:
        return min(79, ovr_actual + 8)
    elif ovr_actual >= 65:
        return min(74, ovr_actual + 9)
    else:
        # Para OVR bajos (52-64)
        OVR_MIN_ACTUAL = 52
        OVR_MAX_ACTUAL = 90
        OVR_MIN_NUEVO = 60
        OVR_MAX_NUEVO = 90
        
        normalized = (ovr_actual - OVR_MIN_ACTUAL) / (OVR_MAX_ACTUAL - OVR_MIN_ACTUAL)
        transformed = normalized ** 0.8
        nuevo_ovr = int(OVR_MIN_NUEVO + transformed * (OVR_MAX_NUEVO - OVR_MIN_NUEVO))
        return min(max(nuevo_ovr, OVR_MIN_NUEVO), 74)


# ==============================================================================
# MAPEO DE POSICIONES
# ==============================================================================

POSITION_MAP = {
    'GK': Position.GK,
    'CB': Position.DEF, 'LB': Position.DEF, 'RB': Position.DEF,
    'LWB': Position.DEF, 'RWB': Position.DEF,
    'CDM': Position.MID, 'CM': Position.MID, 'CAM': Position.MID,
    'LM': Position.MID, 'RM': Position.MID,
    'LW': Position.FWD, 'RW': Position.FWD, 'CF': Position.FWD,
    'ST': Position.FWD,
}

def mapear_posicion_fifa(pos_fifa: str) -> Position:
    """Mapea la posicion de FIFA a nuestro enum"""
    if not pos_fifa or pd.isna(pos_fifa):
        return Position.MID
    
    if ',' in str(pos_fifa):
        pos_fifa = pos_fifa.split(',')[0].strip()
    
    return POSITION_MAP.get(pos_fifa, Position.MID)


# ==============================================================================
# CALCULO DE PRECIO
# ==============================================================================

def calcular_precio(ovr: int, position: Position) -> float:
    """Calcula precio basado en OVR y posicion - genera precios altos"""
    # Multiplicador por posicion
    base_multiplier = {
        Position.GK: 0.8,
        Position.DEF: 0.9,
        Position.MID: 1.0,
        Position.FWD: 1.1
    }
    
    multiplier = base_multiplier.get(position, 1.0)
    
    # Calculo base por OVR (precios altos)
    if ovr >= 85:
        base = 13000000 + (ovr - 85) * 3000000  # 13M - 28M
    elif ovr >= 80:
        base = 7000000 + (ovr - 80) * 1200000   # 7M - 13M
    elif ovr >= 75:
        base = 4000000 + (ovr - 75) * 600000    # 4M - 7M
    elif ovr >= 70:
        base = 2500000 + (ovr - 70) * 300000    # 2.5M - 4M
    elif ovr >= 65:
        base = 1500000 + (ovr - 65) * 200000    # 1.5M - 2.5M
    else:
        base = 800000 + (ovr - 60) * 80000      # 800K - 1.5M
    
    return base * multiplier


# ==============================================================================
# CALCULO DE RAREZA
# ==============================================================================

def determinar_rareza(ovr: int) -> CardRarity:
    """Determina rareza basada en OVR"""
    if ovr >= 85:
        return CardRarity.GOLD
    elif ovr >= 75:
        return CardRarity.SILVER
    else:
        return CardRarity.BRONZE


# ==============================================================================
# SCRIPT PRINCIPAL
# ==============================================================================

def corregir_todo():
    """Ejecuta TODAS las correcciones de una vez"""
    
    print("=" * 80)
    print("CORRECCION COMPLETA DE DATOS DE JUGADORES")
    print("=" * 80 + "\n")
    
    db = SessionLocal()
    
    try:
        # 1. CARGAR CSV DE FIFA
        print(f"Cargando CSV de FIFA: {CSV_PATH}")
        df_fifa = pd.read_csv(CSV_PATH)
        
        equipos_escoceses = [
            "Celtic", "Rangers", "Aberdeen", "Hearts",
            "Hibernian", "Livingston", "Motherwell",
            "St. Mirren", "Dundee FC", "Kilmarnock", "Dundee United"
        ]
        df_fifa = df_fifa[df_fifa['Team'].isin(equipos_escoceses)]
        print(f"OK {len(df_fifa)} jugadores de equipos escoceses en FIFA\n")
        
        # 2. OBTENER JUGADORES DE LA BD
        players = db.query(Player).all()
        print(f"Jugadores en BD: {len(players)}\n")
        
        # 3. ESTADISTICAS ANTES
        print("=" * 80)
        print("ANTES DE CORRECCION:")
        print("=" * 80)
        
        result = db.execute(text("""
            SELECT 
                MIN(overall_rating) as min_ovr,
                MAX(overall_rating) as max_ovr,
                AVG(overall_rating) as avg_ovr
            FROM players
        """))
        stats = result.fetchone()
        print(f"OVR Range: {stats[0]} - {stats[1]} (avg: {stats[2]:.1f})")
        
        result = db.execute(text("""
            SELECT position, COUNT(*) as count
            FROM players
            GROUP BY position
        """))
        print("\nPosiciones:")
        for row in result:
            print(f"   {row[0]}: {row[1]}")
        
        result = db.execute(text("""
            SELECT nationality, COUNT(*) as count
            FROM players
            GROUP BY nationality
            ORDER BY count DESC
            LIMIT 5
        """))
        print("\nTop 5 nacionalidades:")
        for row in result:
            print(f"   {row[0]}: {row[1]}")
        
        # 4. PROCESAR JUGADORES
        print("\n" + "=" * 80)
        print("PROCESANDO JUGADORES...")
        print("=" * 80 + "\n")
        
        ovr_transformados = 0
        posiciones_corregidas = 0
        nacionalidades_corregidas = 0
        precios_recalculados = 0
        no_encontrados = 0
        
        for i, player in enumerate(players, 1):
            # Buscar match en FIFA
            best_score = 0
            fifa_match = None
            
            for _, row in df_fifa.iterrows():
                fifa_name = str(row.get('Name', ''))
                score = fuzz.token_sort_ratio(player.name, fifa_name)
                
                if score > 85 and score > best_score:
                    best_score = score
                    fifa_match = row
            
            if fifa_match is not None:
                # TRANSFORMAR OVR
                ovr_original = player.overall_rating
                ovr_transformado = transformar_ovr(ovr_original)
                
                if ovr_transformado != ovr_original:
                    player.overall_rating = ovr_transformado
                    player.potential = min(99, ovr_transformado + 3)
                    ovr_transformados += 1
                
                # CORREGIR POSICION
                pos_fifa = fifa_match.get('Position', fifa_match.get('Positions', None))
                nueva_posicion = mapear_posicion_fifa(pos_fifa)
                
                if nueva_posicion and nueva_posicion != player.position:
                    player.position = nueva_posicion
                    posiciones_corregidas += 1
                
                # CORREGIR NACIONALIDAD
                nationality_fifa = fifa_match.get('Nation', fifa_match.get('Nationality', 'Scotland'))
                if pd.notna(nationality_fifa) and str(nationality_fifa) != str(player.nationality):
                    player.nationality = str(nationality_fifa)
                    nacionalidades_corregidas += 1
                
                # RECALCULAR PRECIO
                nuevo_precio = calcular_precio(player.overall_rating, player.position)
                player.current_price = nuevo_precio
                player.target_price = nuevo_precio
                precios_recalculados += 1
                
                # ACTUALIZAR RAREZA
                player.base_rarity = determinar_rareza(player.overall_rating)
                
                # ACTUALIZAR STATS PROPORCIONALES
                if ovr_original > 0:
                    factor = player.overall_rating / ovr_original
                    factor = min(factor, 1.5)
                    factor = max(factor, 0.9)
                    
                    player.pace = min(99, max(20, int(player.pace * factor)))
                    player.shooting = min(99, max(20, int(player.shooting * factor)))
                    player.passing = min(99, max(20, int(player.passing * factor)))
                    player.dribbling = min(99, max(20, int(player.dribbling * factor)))
                    player.defending = min(99, max(20, int(player.defending * factor)))
                    player.physical = min(99, max(20, int(player.physical * factor)))
                
            else:
                no_encontrados += 1
            
            # Mostrar progreso
            if i % 50 == 0:
                print(f"   Procesados: {i}/{len(players)}")
        
        # COMMIT
        db.commit()
        
        # 5. ESTADISTICAS DESPUES
        print("\n" + "=" * 80)
        print("DESPUES DE CORRECCION:")
        print("=" * 80)
        
        result = db.execute(text("""
            SELECT 
                MIN(overall_rating) as min_ovr,
                MAX(overall_rating) as max_ovr,
                AVG(overall_rating) as avg_ovr
            FROM players
        """))
        stats = result.fetchone()
        print(f"OVR Range: {stats[0]} - {stats[1]} (avg: {stats[2]:.1f})")
        
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
            print(f"   {row[0]}: {row[1]} ({pct:.1f}%)")
        
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
        print("\nPosiciones:")
        for row in result:
            pct = (row[1] / len(players)) * 100
            print(f"   {row[0]}: {row[1]} ({pct:.1f}%)")
       
        result = db.execute(text("""
            SELECT nationality, COUNT(*) as count
            FROM players
            GROUP BY nationality
            ORDER BY count DESC
            LIMIT 10
        """))
        print("\nTop 10 nacionalidades:")
        for row in result:
            print(f"   {row[0]}: {row[1]}")
        
        # TOP 10 JUGADORES
        result = db.execute(text("""
            SELECT name, position, overall_rating, current_team, current_price
            FROM players
            ORDER BY overall_rating DESC
            LIMIT 10
        """))
        print("\nTop 10 jugadores (OVR):")
        for i, row in enumerate(result, 1):
            precio_millones = row[4] / 1000000
            print(f"   {i}. {row[0]} ({row[1]}) - OVR {row[2]} - {row[3]}")
            print(f"      Precio: {precio_millones:.1f}M EUR")
        
        # RESUMEN
        print("\n" + "=" * 80)
        print("RESUMEN DE CAMBIOS:")
        print("=" * 80)
        print(f"OVR transformados:         {ovr_transformados}")
        print(f"Posiciones corregidas:     {posiciones_corregidas}")
        print(f"Nacionalidades corregidas: {nacionalidades_corregidas}")
        print(f"Precios recalculados:      {precios_recalculados}")
        print(f"No encontrados en FIFA:    {no_encontrados}")
        print("\n" + "=" * 80)
        print("CORRECCION COMPLETADA EXITOSAMENTE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    corregir_todo()
