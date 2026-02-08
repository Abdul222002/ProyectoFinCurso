"""
Script DEFINITIVO para poblar la BD con datos de Sportmonks + FIFA
Usa el endpoint correcto que SÍ funciona: include=players
"""

import sys
import os
import requests
import pandas as pd
from fuzzywuzzy import fuzz
from sqlalchemy import text
from datetime import datetime
import random
import logging

# Desactivar logging verboso
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

# Ajuste de rutas
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Player, Position, CardRarity

# ==========================================
# CONFIGURACIÓN
# ==========================================
API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
SEASON_ID = 21787  # Scottish Premiership
CSV_PATH = os.path.join(os.path.dirname(__file__), '../data/EAFC26-Men.csv')

# Mapeo de posiciones
POSITION_MAP = {
    'GK': Position.GK, 'Goalkeeper': Position.GK,
    'CB': Position.DEF, 'LB': Position.DEF, 'RB': Position.DEF,
    'LWB': Position.DEF, 'RWB': Position.DEF, 'Defender': Position.DEF,
    'CDM': Position.MID, 'CM': Position.MID, 'CAM': Position.MID,
    'LM': Position.MID, 'RM': Position.MID, 'Midfielder': Position.MID,
    'LW': Position.FWD, 'RW': Position.FWD, 'CF': Position.FWD,
    'ST': Position.FWD, 'Attacker': Position.FWD, 'Forward': Position.FWD,
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


def mapear_posicion(pos_str: str) -> Position:
    """Mapea la posición a nuestro enum"""
    if not pos_str:
        return Position.MID
    
    # Buscar en el mapa
    for key, value in POSITION_MAP.items():
        if key.lower() in pos_str.lower():
            return value
    
    return Position.MID


def generar_stats_desde_overall(overall: int, posicion: Position) -> dict:
    """Genera stats realistas basadas en el overall y la posición"""
    base = overall - random.randint(5, 10)
    
    stats = {
        'pace': base,
        'shooting': base,
        'passing': base,
        'dribbling': base,
        'defending': base,
        'physical': base
    }
    
    # Ajustes por posición
    if posicion == Position.GK:
        stats['defending'] = overall - 5
        stats['shooting'] = overall - 30
        stats['dribbling'] = overall - 20
        stats['pace'] = overall - 15
    elif posicion == Position.DEF:
        stats['defending'] = overall + random.randint(0, 5)
        stats['physical'] = overall + random.randint(0, 3)
        stats['shooting'] = overall - random.randint(15, 25)
    elif posicion == Position.MID:
        stats['passing'] = overall + random.randint(0, 5)
        stats['dribbling'] = overall + random.randint(0, 3)
    elif posicion == Position.FWD:
        stats['shooting'] = overall + random.randint(0, 5)
        stats['pace'] = overall + random.randint(0, 5)
        stats['defending'] = overall - random.randint(20, 30)
    
    # Asegurar rango válido
    for key in stats:
        stats[key] = max(20, min(99, stats[key]))
    
    return stats


def obtener_jugadores_sportmonks():
    """Obtiene jugadores desde Sportmonks API"""
    print("📡 Conectando con Sportmonks API...")
    url = f"https://api.sportmonks.com/v3/football/teams/seasons/{SEASON_ID}"
    params = {
        "api_token": API_TOKEN,
        "include": "players"  # ¡Este es el correcto!
    }
    
    response = requests.get(url, params=params, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ Error API: {response.status_code}")
        return []
    
    teams_data = response.json().get('data', [])
    print(f"✅ {len(teams_data)} equipos encontrados\n")
    
    all_players = []
    for team in teams_data:
        team_name = team.get('name')
        players = team.get('players', [])
        
        print(f"   📋 {team_name}: {len(players)} jugadores")
        
        for player in players:
            all_players.append({
                'sportmonks_data': player,
                'team_name': team_name
            })
    
    print(f"\n✅ Total: {len(all_players)} jugadores de Sportmonks\n")
    return all_players


def run_seed():
    """Ejecuta el proceso de seed completo"""
    
    print("="*60)
    print("🌱 SEED DATABASE - SPORTMONKS + FIFA")
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
        
        # 2. CARGAR CSV FIFA
        print("📂 Cargando datos de FIFA...")
        df_fifa = None
        try:
            df_fifa = pd.read_csv(CSV_PATH)
            equipos_escoceses = [
                "Celtic", "Rangers", "Aberdeen", "Hearts",
                "Hibernian", "Livingston", "Motherwell",
                "St. Mirren", "Dundee FC", "Kilmarnock", "Dundee United"
            ]
            df_fifa = df_fifa[df_fifa['Team'].isin(equipos_escoceses)]
            print(f"✅ {len(df_fifa)} jugadores de FIFA\n")
        except Exception as e:
            print(f"⚠️  CSV no disponible: {e}")
            print("   Continuando solo con Sportmonks...\n")
        
        # 3. OBTENER JUGADORES DE SPORTMONKS
        sportmonks_players = obtener_jugadores_sportmonks()
        
        if not sportmonks_players:
            print("❌ No se pudieron obtener jugadores de Sportmonks")
            return
        
        # 4. PROCESAR Y FUSIONAR
        print("🔄 Fusionando datos Sportmonks + FIFA...")
        print("="*60 + "\n")
        
        total = 0
        con_fifa = 0
        sin_fifa = 0
        
        for sp_data in sportmonks_players:
            try:
                sp_player = sp_data['sportmonks_data']
                team_name = sp_data['team_name']
                
                # Datos de Sportmonks
                player_id = sp_player.get('id')
                player_name = sp_player.get('display_name') or sp_player.get('common_name') or sp_player.get('name', 'Unknown')
                
                # Posición
                position_data = sp_player.get('position', {})
                position_name = position_data.get('name', 'Midfielder') if isinstance(position_data, dict) else 'Midfielder'
                posicion = mapear_posicion(position_name)
                
                # Edad
                dob = sp_player.get('date_of_birth')
                edad = 25
                if dob:
                    try:
                        birth_year = int(dob.split('-')[0])
                        edad = datetime.now().year - birth_year
                    except:
                        pass
                
                # Nacionalidad
                nationality_data = sp_player.get('nationality', {})
                nacionalidad = nationality_data.get('name', 'Scotland') if isinstance(nationality_data, dict) else 'Scotland'
                
                # FUZZY MATCHING con FIFA
                fifa_match = None
                best_score = 0
                
                if df_fifa is not None:
                    for _, row in df_fifa.iterrows():
                        score = fuzz.token_sort_ratio(player_name, str(row.get('Name', '')))
                        if score > 85 and score > best_score:
                            best_score = score
                            fifa_match = row
                
                # CREAR JUGADOR
                if fifa_match is not None:
                    # CON DATOS FIFA
                    overall = int(fifa_match['OVR'])
                    
                    # Stats de FIFA
                    pace = int(fifa_match.get('PAC', overall - 5))
                    shooting = int(fifa_match.get('SHO', overall - 5))
                    passing = int(fifa_match.get('PAS', overall - 5))
                    dribbling = int(fifa_match.get('DRI', overall - 5))
                    defending = int(fifa_match.get('DEF', overall - 5))
                    physical = int(fifa_match.get('PHY', overall - 5))
                    potential = int(fifa_match.get('POT', overall + 3))
                    
                    # Foto
                    foto = fifa_match.get('Photo', '')
                    if not foto or pd.isna(foto):
                        foto = sp_player.get('image_path')
                    
                    con_fifa += 1
                    print(f"   ✅ {player_name} ({posicion.value}) - OVR {overall} [FIFA]")
                    
                else:
                    # SIN DATOS FIFA (usar estimación)
                    overall = random.randint(58, 68)
                    stats = generar_stats_desde_overall(overall, posicion)
                    pace = stats['pace']
                    shooting = stats['shooting']
                    passing = stats['passing']
                    dribbling = stats['dribbling']
                    defending = stats['defending']
                    physical = stats['physical']
                    potential = overall + random.randint(3, 10)
                    foto = sp_player.get('image_path')
                    
                    sin_fifa += 1
                    print(f"   👻 {player_name} ({posicion.value}) - OVR {overall} [Estimado]")
                
                precio = calcular_precio(overall)
                
                # Insertar en BD
                player = Player(
                    sportmonks_id=player_id,
                    name=player_name,
                    age=edad,
                    position=posicion,
                    nationality=nacionalidad,
                    overall_rating=overall,
                    potential=potential,
                    current_team=team_name,
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
                
                # Commit cada 20 jugadores
                if total % 20 == 0:
                    db.commit()
                
            except Exception as e:
                print(f"   ❌ Error con {sp_player.get('name', 'Unknown')}: {e}")
                continue
        
        # Commit final
        db.commit()
        
        # 5. RESUMEN
        print("\n" + "="*60)
        print("🏁 SEED COMPLETADO")
        print("="*60)
        print(f"📊 Total jugadores insertados: {total}")
        print(f"✅ Con datos FIFA:              {con_fifa}")
        print(f"👻 Sin datos FIFA (estimados):  {sin_fifa}")
        print("="*60)
        
        # Verificación
        result = db.execute(text("SELECT COUNT(*) FROM players"))
        count = result.fetchone()[0]
        print(f"\n✅ Jugadores en BD: {count}")
        
        # Top jugadores
        result = db.execute(text("""
            SELECT name, position, overall_rating, current_team 
            FROM players 
            ORDER BY overall_rating DESC 
            LIMIT 5
        """))
        
        print("\n⭐ Top 5 jugadores:")
        for row in result:
            print(f"   {row[0]} ({row[1]}) - OVR {row[2]} - {row[3]}")
        
        print("\n✅ ¡Base de datos lista!")
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()