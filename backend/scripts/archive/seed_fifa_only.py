"""
Script de Seed usando SOLO datos de FIFA
Más rápido y confiable para pruebas
"""

import sys
import os
import pandas as pd
from sqlalchemy import text
import random

# Ajuste de rutas
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Player, Position, CardRarity

# ==========================================
# CONFIGURACIÓN
# ==========================================
CSV_PATH = os.path.join(os.path.dirname(__file__), '../data/EAFC26-Men.csv')

# Equipos de la Scottish Premiership (nombres exactos del CSV EAFC26)
EQUIPOS_ESCOCESES = [
    "Celtic", "Rangers", "Aberdeen", "Hearts",
    "Hibernian", "Livingston", "Motherwell",
    "St. Mirren", "Dundee FC", "Kilmarnock", "Dundee United"
]

# Mapeo de posiciones FIFA a nuestro enum
POSITION_MAP = {
    'GK': Position.GK,
    'CB': Position.DEF,
    'LB': Position.DEF,
    'RB': Position.DEF,
    'LWB': Position.DEF,
    'RWB': Position.DEF,
    'CDM': Position.MID,
    'CM': Position.MID,
    'CAM': Position.MID,
    'LM': Position.MID,
    'RM': Position.MID,
    'LW': Position.FWD,
    'RW': Position.FWD,
    'CF': Position.FWD,
    'ST': Position.FWD,
}

# ==========================================
# FUNCIONES
# ==========================================

def calcular_precio(overall: int) -> float:
    """Calcula el precio basado en el overall"""
    if overall < 60:
        return random.uniform(800000, 1200000)
    elif overall < 65:
        return random.uniform(1500000, 2500000)
    elif overall < 68:
        return random.uniform(3000000, 4000000)
    elif overall < 71:
        return random.uniform(4500000, 5500000)
    elif overall < 74:
        return random.uniform(7000000, 8000000)
    elif overall < 77:
        return random.uniform(9000000, 11000000)
    elif overall < 80:
        return random.uniform(13000000, 15000000)
    elif overall < 83:
        return random.uniform(20000000, 24000000)
    else:
        return random.uniform(30000000, 50000000)


def determinar_rareza(overall: int) -> CardRarity:
    """Determina la rareza de la carta"""
    if overall >= 80:
        return CardRarity.GOLD
    elif overall >= 70:
        return CardRarity.SILVER
    else:
        return CardRarity.BRONZE


def mapear_posicion(pos_fifa: str) -> Position:
    """Mapea la posición de FIFA a nuestro enum"""
    return POSITION_MAP.get(pos_fifa, Position.MID)


def construir_foto_url(player_id: int, foto_csv: str) -> str:
    """Construye la URL de la foto del jugador"""
    if pd.notna(foto_csv) and foto_csv:
        return foto_csv
    
    # Construir URL desde el ID
    pid = str(player_id).zfill(6)
    return f"https://cdn.sofifa.net/players/{pid[:3]}/{pid[3:]}/24_120.png"


# ==========================================
# SCRIPT PRINCIPAL
# ==========================================

def run_seed():
    """Ejecuta el proceso de seed con datos FIFA"""
    
    print("="*60)
    print("🌱 SEED DATABASE - SOLO FIFA DATA")
    print("="*60 + "\n")
    
    db = SessionLocal()
    
    try:
        # 1. LIMPIAR BASE DE DATOS
        print("🧹 Limpiando base de datos...")
        try:
            db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            db.execute(text("TRUNCATE TABLE players;"))
            db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            db.commit()
            print("✅ Base de datos limpia\n")
        except Exception as e:
            print(f"⚠️  Error limpiando: {e}\n")
            db.rollback()
        
        # 2. CARGAR CSV
        print(f"📂 Cargando CSV desde: {CSV_PATH}")
        
        try:
            # Leer CSV
            df = pd.read_csv(CSV_PATH)
            print(f"✅ CSV cargado: {len(df)} jugadores totales\n")
            
            # Filtrar solo equipos escoceses
            print("🔍 Filtrando jugadores de Escocia...")
            df_scotland = df[df['Team'].isin(EQUIPOS_ESCOCESES)]
            print(f"✅ Encontrados {len(df_scotland)} jugadores escoceses\n")
            
            if len(df_scotland) == 0:
                print("❌ No se encontraron jugadores. Verifica los nombres de equipos.")
                print(f"📋 Equipos únicos en el CSV: {df['Team'].unique()[:20]}")
                return
            
        except FileNotFoundError:
            print(f"❌ No se encontró el archivo CSV en: {CSV_PATH}")
            return
        except Exception as e:
            print(f"❌ Error leyendo CSV: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 3. PROCESAR JUGADORES
        print("🚀 Insertando jugadores en la base de datos...")
        print("="*60 + "\n")
        
        total = 0
        errores = 0
        por_equipo = {}
        
        for idx, row in df_scotland.iterrows():
            try:
                # Datos básicos
                nombre = row.get('Name', 'Unknown')
                overall = int(row.get('OVR', 65))
                edad = int(row.get('Age', 25))
                equipo = row.get('Team', 'Unknown')
                
                # Posición - EAFC26 usa "Position" o "Positions"
                pos_fifa = row.get('Position', row.get('Positions', 'CM'))
                if isinstance(pos_fifa, str) and ',' in pos_fifa:
                    pos_fifa = pos_fifa.split(',')[0].strip()
                posicion = mapear_posicion(pos_fifa)
                
                # Nacionalidad
                nacionalidad = row.get('Nation', 'Scotland')
                
                # Stats - EAFC26 usa PAC, SHO, PAS, DRI, DEF, PHY
                pace = int(row.get('PAC', overall - 5))
                shooting = int(row.get('SHO', overall - 5))
                passing = int(row.get('PAS', overall - 5))
                dribbling = int(row.get('DRI', overall - 5))
                defending = int(row.get('DEF', overall - 5))
                physical = int(row.get('PHY', overall - 5))
                
                # Potencial - si no existe, usar overall + 3
                potential = int(row.get('POT', overall + 3))
                
                # Foto - EAFC26 puede tener "Photo" o construir desde ID
                player_id = int(row.get('ID', 0))
                foto = row.get('Photo', '')
                if not foto or pd.isna(foto):
                    foto = construir_foto_url(player_id, '')
                
                # Precio
                precio = calcular_precio(overall)
                
                # Crear jugador
                player = Player(
                    sportmonks_id=None,  # No tenemos ID de Sportmonks
                    name=nombre,
                    age=edad,
                    position=posicion,
                    nationality=nacionalidad,
                    overall_rating=overall,
                    potential=potential,
                    current_team=equipo,
                    is_legend=False,
                    base_rarity=determinar_rareza(overall),
                    current_price=precio,
                    target_price=precio,
                    image_url=foto,
                    pace=pace,
                    shooting=shooting,
                    passing=passing,
                    dribbling=dribbling,
                    defending=defending,
                    physical=physical
                )
                
                db.add(player)
                total += 1
                
                # Contador por equipo
                por_equipo[equipo] = por_equipo.get(equipo, 0) + 1
                
                # Log cada 10 jugadores
                if total % 10 == 0:
                    print(f"   ✓ {total} jugadores procesados...")
                
            except Exception as e:
                errores += 1
                print(f"   ❌ Error con {row.get('short_name', 'Unknown')}: {e}")
                continue
        
        # Commit final
        db.commit()
        
        # 4. RESUMEN
        print("\n" + "="*60)
        print("🏁 SEED COMPLETADO")
        print("="*60)
        print(f"📊 Total jugadores insertados: {total}")
        print(f"❌ Errores: {errores}")
        print("\n🏆 Jugadores por equipo:")
        for equipo, count in sorted(por_equipo.items(), key=lambda x: x[1], reverse=True):
            print(f"   {equipo}: {count}")
        
        print("\n" + "="*60)
        
        # Verificación en BD
        print("\n🔍 Verificando base de datos...")
        result = db.execute(text("SELECT COUNT(*) as total FROM players"))
        count = result.fetchone()[0]
        print(f"✅ Jugadores en BD: {count}")
        
        # Mostrar algunos ejemplos
        result = db.execute(text("""
            SELECT name, position, overall_rating, current_team, current_price 
            FROM players 
            ORDER BY overall_rating DESC 
            LIMIT 5
        """))
        
        print("\n⭐ Top 5 jugadores:")
        for row in result:
            print(f"   {row[0]} ({row[1]}) - OVR {row[2]} - {row[3]} - €{row[4]:,.0f}")
        
        print("\n✅ ¡Base de datos lista para usar!")
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
