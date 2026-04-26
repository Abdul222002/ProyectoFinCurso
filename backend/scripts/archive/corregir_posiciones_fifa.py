"""
Script FINAL para corregir posiciones usando datos de FIFA CSV
MatcheandoPositions de FIFA con los jugadores en la BD
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
from app.models.models import Player, Position

CSV_PATH = os.path.join(os.path.dirname(__file__), '../data/EAFC26-Men.csv')

# Mapeo de posiciones FIFA a nuestro enum
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
    """Mapea la posición de FIFA a nuestro enum"""
    if not pos_fifa or pd.isna(pos_fifa):
        return None
    
    # Si hay múltiples posiciones, tomar la primera
    if ',' in str(pos_fifa):
        pos_fifa = pos_fifa.split(',')[0].strip()
    
    return POSITION_MAP.get(pos_fifa, None)


def corregir_con_fifa():
    """Corrige las posiciones usando el CSV de FIFA"""
    
    print("="*60)
    print("🎯 CORRECCIÓN FINAL DE POSICIONES CON FIFA")
    print("="*60 + "\n")
    
    db = SessionLocal()
    
    try:
        # 1. Cargar CSV de FIFA
        print(f"📂 Cargando CSV de FIFA: {CSV_PATH}")
        df_fifa = pd.read_csv(CSV_PATH)
        
        # Filtrar equipos escoceses
        equipos_escoceses = [
            "Celtic", "Rangers", "Aberdeen", "Hearts",
            "Hibernian", "Livingston", "Motherwell",
            "St. Mirren", "Dundee FC", "Kilmarnock", "Dundee United"
        ]
        df_fifa = df_fifa[df_fifa['Team'].isin(equipos_escoceses)]
        print(f"✅ {len(df_fifa)} jugadores de equipos escoceses en FIFA\n")
        
        # 2. Obtener jugadores de la BD
        players = db.query(Player).all()
        print(f"📊 {len(players)} jugadores en la base de datos\n")
        
        # 3. Estadísticas antes
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
        print("🔄 Matcheando con FIFA y corrigiendo...")
        print("="*60 + "\n")
        
        corregidos = 0
        no_encontrados = 0
        
        for player in players:
            # Buscar match con FIFA por nombre
            best_score = 0
            fifa_match = None
            
            for _, row in df_fifa.iterrows():
                fifa_name = str(row.get('Name', ''))
                score = fuzz.token_sort_ratio(player.name, fifa_name)
                
                if score > 85 and score > best_score:
                    best_score = score
                    fifa_match = row
            
            if fifa_match is not None:
                # Obtener posición de FIFA
                pos_fifa = fifa_match.get('Position', fifa_match.get('Positions', None))
                nueva_posicion = mapear_posicion_fifa(pos_fifa)
                
                if nueva_posicion and nueva_posicion != player.position:
                    posicion_original = player.position
                    player.position = nueva_posicion
                    corregidos += 1
                    
                    if corregidos <= 30:
                        print(f"   ✅ {player.name}: {posicion_original.value} → {nueva_posicion.value} (FIFA: {pos_fifa})")
            else:
                no_encontrados += 1
                if no_encontrados <= 10:
                    print(f"   ⚠️  No encontrado en FIFA: {player.name}")
        
        # Commit
        db.commit()
        print(f"\n✅ Posiciones corregidas: {corregidos}")
        print(f"⚠️  No encontrados en FIFA: {no_encontrados}\n")
        
        # 4. Estadísticas después
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
        
        # 5. Mostrar ejemplos por posición
        print("\n📋 Top 5 por posición:\n")
        
        for pos in [Position.GK, Position.DEF, Position.MID, Position.FWD]:
            print(f"   {pos.value}:")
            result = db.execute(text(f"""
                SELECT name, overall_rating, current_team
                FROM players
                WHERE position = '{pos.value}'
                ORDER BY overall_rating DESC
                LIMIT 5
            """))
            for row in result:
                print(f"      {row[0]} (OVR {row[1]}) - {row[2]}")
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
    corregir_con_fifa()
