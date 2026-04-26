"""
Script DEFINITIVO - Seed completo con Sportmonks + FIFA
Obtiene los 338 jugadores con datos completos mediante llamadas individuales
"""

import sys
import os
import requests
import pandas as pd
from fuzzywuzzy import fuzz
from sqlalchemy import text
from datetime import datetime
import random
import time
import logging

# Desactivar logging verboso
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

# Ajuste de rutas
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Player, Position, CardRarity

# ==========================================
# CONFIGURACIN
# ==========================================
API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
SEASON_ID = 21787
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
# FUNCIONES AUXILIARES
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
    """Mapea la posicin a nuestro enum"""
    if not pos_str:
        return Position.MID
    
    for key, value in POSITION_MAP.items():
        if key.lower() in pos_str.lower():
            return value
    
    return Position.MID


def generar_stats_desde_overall(overall: int, posicion: Position) -> dict:
    """Genera stats realistas basadas en el overall y la posicin"""
    base = overall - random.randint(5, 10)
    
    stats = {
        'pace': base,
        'shooting': base,
        'passing': base,
        'dribbling': base,
        'defending': base,
        'physical': base
    }
    
    # Ajustes por posicin
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
    
    # Asegurar rango vlido
    for key in stats:
        stats[key] = max(20, min(99, stats[key]))
    
    return stats


# ==========================================
# FUNCIONES DE API
# ==========================================

def obtener_player_ids():
    """Obtiene todos los player_ids de la temporada"""
    print(" Obteniendo player_ids de Sportmonks...")
    
    url = f"https://api.sportmonks.com/v3/football/teams/seasons/{SEASON_ID}"
    params = {
        "api_token": API_TOKEN,
        "include": "players"
    }
    
    response = requests.get(url, params=params, timeout=30)
    
    if response.status_code != 200:
        print(f" Error API: {response.status_code}")
        return []
    
    teams_data = response.json().get('data', [])
    print(f" {len(teams_data)} equipos encontrados")
    
    player_ids = []
    team_mapping = {}
    
    for team in teams_data:
        team_name = team.get('name')
        players = team.get('players', [])
        
        print(f"   {team_name}: {len(players)} jugadores")
        
        for player_data in players:
            player_id = player_data.get('player_id')
            position_id = player_data.get('position_id')
            
            if player_id:
                player_ids.append(player_id)
                team_mapping[player_id] = {
                    'team': team_name,
                    'position_id': position_id
                }
    
    print(f"\n Total: {len(player_ids)} player_ids\n")
    return player_ids, team_mapping


def obtener_datos_jugador(player_id):
    """Obtiene los datos completos de un jugador"""
    url = f"https://api.sportmonks.com/v3/football/players/{player_id}"
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get('data', {})
    except:
        pass
    
    return None


# ==========================================
# SCRIPT PRINCIPAL
# ==========================================

def run_seed():
    """Ejecuta el proceso de seed completo"""
    
    print("="*60)
    print(" SEED DEFINITIVO - SPORTMONKS + FIFA")
    print("="*60 + "\n")
    
    db = SessionLocal()
    
    try:
        # 1. LIMPIAR BASE DE DATOS
        print(" Limpiando base de datos...")
        try:
            db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            db.execute(text("TRUNCATE TABLE players;"))
            db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            db.commit()
            print(" Base de datos limpia\n")
        except Exception as e:
            print(f"  Error limpiando: {e}\n")
            db.rollback()
        
        # 2. CARGAR CSV FIFA
        print(" Cargando datos de FIFA...")
        df_fifa = None
        try:
            df_fifa = pd.read_csv(CSV_PATH)
            equipos_escoceses = [
                "Celtic", "Rangers", "Aberdeen", "Hearts",
                "Hibernian", "Livingston", "Motherwell",
                "St. Mirren", "Dundee FC", "Kilmarnock", "Dundee United"
            ]
            df_fifa = df_fifa[df_fifa['Team'].isin(equipos_escoceses)]
            print(f" {len(df_fifa)} jugadores de FIFA\n")
        except Exception as e:
            print(f"  CSV no disponible: {e}\n")
        
        # 3. OBTENER PLAYER_IDS DE SPORTMONKS
        player_ids, team_mapping = obtener_player_ids()
        
        if not player_ids:
            print(" No se pudieron obtener player_ids")
            return
        
        # 4. OBTENER DATOS COMPLETOS Y PROCESAR
        print(" Obteniendo datos completos de cada jugador...")
        print(f"  Esto tomar aproximadamente {len(player_ids) * 0.3 / 60:.1f} minutos")
        print("="*60 + "\n")
        
        total = 0
        con_fifa = 0
        sin_fifa = 0
        errores = 0
        
        for i, player_id in enumerate(player_ids, 1):
            try:
                # Obtener datos completos del jugador
                sp_player = obtener_datos_jugador(player_id)
                
                if not sp_player:
                    errores += 1
                    print(f"    {i}/{len(player_ids)}: Error obteniendo player_id {player_id}")
                    continue
                
                # Datos bsicos
                player_name = sp_player.get('display_name') or sp_player.get('common_name') or sp_player.get('name', 'Unknown')
                team_info = team_mapping.get(player_id, {})
                team_name = team_info.get('team', 'Unknown')
                
                # Posicin
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
                    pace = int(fifa_match.get('PAC', overall - 5))
                    shooting = int(fifa_match.get('SHO', overall - 5))
                    passing = int(fifa_match.get('PAS', overall - 5))
                    dribbling = int(fifa_match.get('DRI', overall - 5))
                    defending = int(fifa_match.get('DEF', overall - 5))
                    physical = int(fifa_match.get('PHY', overall - 5))
                    potential = int(fifa_match.get('POT', overall + 3))
                    
                    foto = fifa_match.get('Photo', '')
                    if not foto or pd.isna(foto):
                        foto = sp_player.get('image_path')
                    
                    con_fifa += 1
                    print(f"    {i}/{len(player_ids)}: {player_name} ({posicion.value}) - OVR {overall} [FIFA]")
                    
                else:
                    # SIN DATOS FIFA
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
                    if i % 20 == 0:  # Mostrar solo cada 20 para no saturar
                        print(f"    {i}/{len(player_ids)}: {player_name} ({posicion.value}) - OVR {overall} [Estimado]")
                
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
                
                # Commit cada 50 jugadores
                if total % 50 == 0:
                    db.commit()
                    print(f"\n    Guardados {total} jugadores...\n")
                
                # Respetar rate limit
                time.sleep(0.3)
                
            except Exception as e:
                errores += 1
                print(f"    {i}/{len(player_ids)}: Error - {e}")
                continue
        
        # Commit final
        db.commit()
        
        # 5. RESUMEN
        print("\n" + "="*60)
        print(" SEED COMPLETADO")
        print("="*60)
        print(f" Total jugadores insertados: {total}")
        print(f" Con datos FIFA:              {con_fifa}")
        print(f" Sin datos FIFA (estimados):  {sin_fifa}")
        print(f" Errores:                     {errores}")
        print("="*60)
        
        # Verificacin
        result = db.execute(text("SELECT COUNT(*) FROM players"))
        count = result.fetchone()[0]
        print(f"\n Jugadores en BD: {count}")
        
        # Top jugadores
        result = db.execute(text("""
            SELECT name, position, overall_rating, current_team 
            FROM players 
            ORDER BY overall_rating DESC 
            LIMIT 10
        """))
        
        print("\n Top 10 jugadores:")
        for row in result:
            print(f"   {row[0]} ({row[1]}) - OVR {row[2]} - {row[3]}")
        
        # Por equipo
        result = db.execute(text("""
            SELECT current_team, COUNT(*) as count 
            FROM players 
            GROUP BY current_team 
            ORDER BY count DESC
        """))
        
        print("\n Jugadores por equipo:")
        for row in result:
            print(f"   {row[0]}: {row[1]}")
        
        print("\n Base de datos completamente poblada!")
        
    except Exception as e:
        print(f"\n ERROR CRTICO: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()

