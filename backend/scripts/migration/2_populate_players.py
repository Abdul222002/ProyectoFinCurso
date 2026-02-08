"""
POBLACIÓN COMPLETA DE JUGADORES
- Obtiene jugadores de Sportmonks API
- Cruza con FIFA CSV para medias reales
- Transforma medias al sistema ficticio (60-90)
- Incluye los 100 iconos
- Guarda todo en la base de datos
"""

import sys
import os
import csv
import requests
from datetime import datetime
from difflib import SequenceMatcher

# Ajuste de rutas
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.database import SessionLocal
from app.models.models import Player, Position, CardRarity

# ==========================================
# CONFIGURACIÓN
# ==========================================

API_TOKEN = "JElZH6J4bB7OSJyRDNsBtJUO1P2IzY2GVRBmak6falJgqa3dr6OGC6MasQwR"
SEASON_ID = 21787  # Scottish Premiership 2024/25

# Rutas a los CSVs
FIFA_CSV = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'EAFC26-Men.csv')
ICONS_CSV = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'football_icons.csv')

# Transformación de OVR
OVR_MIN_ACTUAL = 52
OVR_MAX_ACTUAL = 90
OVR_MIN_NUEVO = 60
OVR_MAX_NUEVO = 90


# ==========================================
# FUNCIONES DE TRANSFORMACIÓN
# ==========================================

def transformar_ovr(ovr_actual: int) -> int:
    """Transforma el OVR del FIFA al rango ficticio 60-90"""
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
        normalized = (ovr_actual - OVR_MIN_ACTUAL) / (OVR_MAX_ACTUAL - OVR_MIN_ACTUAL)
        transformed = normalized ** 0.8
        nuevo_ovr = int(OVR_MIN_NUEVO + transformed * (OVR_MAX_NUEVO - OVR_MIN_NUEVO))
        return min(max(nuevo_ovr, OVR_MIN_NUEVO), 74)


def determinar_rareza(ovr: int) -> CardRarity:
    """Determina la rareza basada en el OVR"""
    if ovr >= 85:
        return CardRarity.GOLD
    elif ovr >= 75:
        return CardRarity.SILVER
    else:
        return CardRarity.BRONZE


def calcular_precio(ovr: int, position: Position) -> int:
    """Calcula el precio basado en OVR y posición"""
    base_multiplier = {
        Position.GK: 0.8,
        Position.DEF: 0.9,
        Position.MID: 1.0,
        Position.FWD: 1.1
    }
    
    multiplier = base_multiplier.get(position, 1.0)
    
    if ovr >= 85:
        base = 13000000 + (ovr - 85) * 3000000
    elif ovr >= 80:
        base = 7000000 + (ovr - 80) * 1200000
    elif ovr >= 75:
        base = 4000000 + (ovr - 75) * 600000
    elif ovr >= 70:
        base = 2500000 + (ovr - 70) * 300000
    elif ovr >= 65:
        base = 1500000 + (ovr - 65) * 200000
    else:
        base = 800000 + (ovr - 60) * 80000
    
    return int(base * multiplier)


def mapear_posicion_fifa(position_str: str) -> Position:
    """Mapea la posición del FIFA al enum Position"""
    position_str = position_str.strip().upper()
    
    if position_str in ['GK']:
        return Position.GK
    elif position_str in ['CB', 'LB', 'RB', 'LWB', 'RWB']:
        return Position.DEF
    elif position_str in ['CDM', 'CM', 'CAM', 'LM', 'RM']:
        return Position.MID
    elif position_str in ['LW', 'RW', 'ST', 'CF']:
        return Position.FWD
    else:
        return Position.MID


def similar(a: str, b: str) -> float:
    """Calcula similitud entre dos strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# ==========================================
# FUNCIONES DE OBTENCIÓN DE DATOS
# ==========================================

def cargar_fifa_data():
    """Carga todos los jugadores del CSV de FIFA"""
    print("Cargando datos de FIFA...")
    
    fifa_players = {}
    
    with open(FIFA_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['Name'].strip()
            
            # Crear entrada en diccionario
            fifa_players[name] = {
                'overall': int(row['OVR']),
                'position': row['Position'],
                'age': int(row['Age']) if row['Age'] else 25,
                'nationality': row['Nation'],
                'pace': int(row['PAC']) if row['PAC'] else 50,
                'shooting': int(row['SHO']) if row['SHO'] else 50,
                'passing': int(row['PAS']) if row['PAS'] else 50,
                'dribbling': int(row['DRI']) if row['DRI'] else 50,
                'defending': int(row['DEF']) if row['DEF'] else 50,
                'physical': int(row['PHY']) if row['PHY'] else 50,
            }
    
    print(f"{len(fifa_players)} jugadores cargados del FIFA\n")
    return fifa_players


def cargar_iconos():
    """Carga los iconos del CSV"""
    print("Cargando iconos...")
    
    iconos = []
    
    with open(ICONS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            iconos.append({
                'name': row['name'],
                'position': row['position'],
                'nationality': row['nationality'],
                'age': int(row['age']),
                'overall': int(row['overall']),
                'pace': int(row['pace']),
                'shooting': int(row['shooting']),
                'passing': int(row['passing']),
                'dribbling': int(row['dribbling']),
                'defending': int(row['defending']),
                'physical': int(row['physical']),
                'is_icon': True
            })
    
    print(f"{len(iconos)} iconos cargados\n")
    return iconos


def obtener_jugadores_sportmonks():
    """Obtiene todos los jugadores de la liga escocesa desde Sportmonks"""
    print("🌐 Obteniendo jugadores de Sportmonks API...")
    
    # Primero obtener todos los equipos de la temporada
    url_teams = f"https://api.sportmonks.com/v3/football/teams/seasons/{SEASON_ID}"
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(url_teams, params=params, timeout=15)
        response.raise_for_status()
        teams = response.json().get('data', [])
        print(f"   📋 Encontrados {len(teams)} equipos")
    except Exception as e:
        print(f"   ❌ Error obteniendo equipos: {e}")
        return []
    
    all_players = []
    
    # Para cada equipo, obtener sus jugadores
    for i, team in enumerate(teams, 1):
        team_id = team['id']
        team_name = team['name']
        
        print(f"   🔍 [{i}/{len(teams)}] {team_name}...", end=' ')
        
        url_players = f"https://api.sportmonks.com/v3/football/squads/seasons/{SEASON_ID}/teams/{team_id}"
        
        try:
            response = requests.get(url_players, params=params, timeout=15)
            response.raise_for_status()
            data = response.json().get('data', [])
            
            if data:
                squad_data = data[0] if isinstance(data, list) else data
                players = squad_data.get('players', [])
                
                for player in players:
                    all_players.append({
                        'sportmonks_id': player.get('player_id'),
                        'name': player.get('player', {}).get('display_name', 'Unknown'),
                        'team': team_name
                    })
                
                print(f"✅ {len(players)} jugadores")
            else:
                print("⚠️  Sin datos")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n✅ Total: {len(all_players)} jugadores obtenidos de Sportmonks\n")
    return all_players


def buscar_en_fifa(player_name: str, fifa_data: dict):
    """Busca un jugador en los datos de FIFA por nombre"""
    # Búsqueda exacta
    if player_name in fifa_data:
        return fifa_data[player_name]
    
    # Búsqueda por similitud
    best_match = None
    best_score = 0.0
    
    for fifa_name in fifa_data.keys():
        score = similar(player_name, fifa_name)
        if score > best_score and score >= 0.8:  # Umbral de 80% similitud
            best_score = score
            best_match = fifa_name
    
    if best_match:
        return fifa_data[best_match]
    
    return None


# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================

def populate_players():
    """Función principal que puebla la base de datos"""
    
    print("\n" + "="*100)
    print("POBLACION COMPLETA DE JUGADORES")
    print("="*100 + "\n")
    
    db = SessionLocal()
    
    try:
        # 1. Cargar datos de FIFA
        fifa_data = cargar_fifa_data()
        
        # 2. Cargar iconos
        iconos = cargar_iconos()
        
        # 3. Obtener jugadores de Sportmonks
        sportmonks_players = obtener_jugadores_sportmonks()
        
        # 4. Procesar y guardar en BD
        print("="*100)
        print("💾 GUARDANDO EN BASE DE DATOS")
        print("="*100 + "\n")
        
        jugadores_creados = 0
        jugadores_sin_fifa = 0
        
        # 4.1. Primero los iconos (siempre se crean)
        print("⭐ Creando iconos...")
        for icono in iconos:
            # Verificar si ya existe
            existing = db.query(Player).filter(
                Player.name == icono['name']
            ).first()
            
            if existing:
                continue
            
            # Transformar OVR
            ovr_ficticio = icono['overall']  # Los iconos ya tienen OVR alto
            position = mapear_posicion_fifa(icono['position'])
            
            player = Player(
                sportmonks_id=None,  # Los iconos no tienen ID de Sportmonks
                name=icono['name'],
                position=position,
                current_team="Legend",
                age=icono['age'],
                nationality=icono['nationality'],
                overall_rating=ovr_ficticio,
                potential=min(99, ovr_ficticio + 1),
                base_rarity=CardRarity.GOLD,  # Todos los iconos son GOLD
                pace=icono['pace'],
                shooting=icono['shooting'],
                passing=icono['passing'],
                dribbling=icono['dribbling'],
                defending=icono['defending'],
                physical=icono['physical'],
                current_price=calcular_precio(ovr_ficticio, position),
                target_price=calcular_precio(ovr_ficticio, position),
                total_matches_played=0,
                sum_match_ratings=0,
                sum_fantasy_points=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(player)
            jugadores_creados += 1
        
        db.commit()
        print(f"✅ {len(iconos)} iconos creados\n")
        
        # 4.2. Jugadores de Sportmonks cruzados con FIFA
        print("🔄 Procesando jugadores de Sportmonks...")
        for i, sp_player in enumerate(sportmonks_players, 1):
            # Verificar si ya existe
            existing = db.query(Player).filter(
                Player.sportmonks_id == sp_player['sportmonks_id']
            ).first()
            
            if existing:
                continue
            
            # Buscar en FIFA
            fifa_info = buscar_en_fifa(sp_player['name'], fifa_data)
            
            if fifa_info:
                # Jugador encontrado en FIFA
                ovr_real = fifa_info['overall']
                ovr_ficticio = transformar_ovr(ovr_real)
                position = mapear_posicion_fifa(fifa_info['position'])
                
                player = Player(
                    sportmonks_id=sp_player['sportmonks_id'],
                    name=sp_player['name'],
                    position=position,
                    current_team=sp_player['team'],
                    age=fifa_info['age'],
                    nationality=fifa_info['nationality'],
                    overall_rating=ovr_ficticio,
                    potential=min(99, ovr_ficticio + 3),
                    base_rarity=determinar_rareza(ovr_ficticio),
                    pace=fifa_info['pace'],
                    shooting=fifa_info['shooting'],
                    passing=fifa_info['passing'],
                    dribbling=fifa_info['dribbling'],
                    defending=fifa_info['defending'],
                    physical=fifa_info['physical'],
                    current_price=calcular_precio(ovr_ficticio, position),
                    target_price=calcular_precio(ovr_ficticio, position),
                    total_matches_played=0,
                    sum_match_ratings=0,
                    sum_fantasy_points=0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(player)
                jugadores_creados += 1
            else:
                # Jugador NO encontrado en FIFA - crear con stats por defecto
                jugadores_sin_fifa += 1
                
                # OVR por defecto bajo
                ovr_ficticio = 65
                position = Position.MID  # Por defecto
                
                player = Player(
                    sportmonks_id=sp_player['sportmonks_id'],
                    name=sp_player['name'],
                    position=position,
                    current_team=sp_player['team'],
                    age=25,
                    nationality="Scotland",
                    overall_rating=ovr_ficticio,
                    potential=70,
                    base_rarity=CardRarity.BRONZE,
                    pace=60,
                    shooting=60,
                    passing=60,
                    dribbling=60,
                    defending=60,
                    physical=60,
                    current_price=calcular_precio(ovr_ficticio, position),
                    target_price=calcular_precio(ovr_ficticio, position),
                    total_matches_played=0,
                    sum_match_ratings=0,
                    sum_fantasy_points=0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(player)
                jugadores_creados += 1
            
            # Commit cada 50 jugadores
            if i % 50 == 0:
                db.commit()
                print(f"   💾 {i}/{len(sportmonks_players)} procesados...")
        
        # Commit final
        db.commit()
        
        # 5. Resumen
        print("\n" + "="*100)
        print("📊 RESUMEN FINAL")
        print("="*100)
        
        total_players = db.query(Player).count()
        
        print(f"\n✅ Total jugadores en BD: {total_players}")
        print(f"   - Iconos: {len(iconos)}")
        print(f"   - Jugadores Sportmonks con FIFA: {jugadores_creados - len(iconos) - jugadores_sin_fifa}")
        print(f"   - Jugadores Sportmonks sin FIFA: {jugadores_sin_fifa}")
        
        # Distribución por rareza
        gold_count = db.query(Player).filter(Player.base_rarity == CardRarity.GOLD).count()
        silver_count = db.query(Player).filter(Player.base_rarity == CardRarity.SILVER).count()
        bronze_count = db.query(Player).filter(Player.base_rarity == CardRarity.BRONZE).count()
        
        print(f"\n📊 Distribución por rareza:")
        print(f"   - 🥇 GOLD: {gold_count}")
        print(f"   - 🥈 SILVER: {silver_count}")
        print(f"   - 🥉 BRONZE: {bronze_count}")
        
        # Top 10
        top_players = db.query(Player).order_by(Player.overall_rating.desc()).limit(10).all()
        print(f"\n⭐ Top 10 jugadores:")
        for player in top_players:
            print(f"   {player.name} ({player.position.name}) - OVR {player.overall_rating} - {player.current_team}")
        
        print("\n" + "="*100)
        print("✅ POBLACIÓN DE JUGADORES COMPLETADA")
        print("="*100 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    
    finally:
        db.close()


if __name__ == "__main__":
    populate_players()
