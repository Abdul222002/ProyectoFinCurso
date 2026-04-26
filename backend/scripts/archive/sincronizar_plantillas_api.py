"""
Script para sincronizar plantillas de equipos desde la API de Sportmonks
Obtiene todos los equipos de la temporada 25/26 y compara sus jugadores con la BD
"""

import sys
import os

# Añadir paths necesarios
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import requests
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Player, Position as DBPosition

from scripts.sistema_puntos_oficial import API_TOKEN, logger

# Constantes de la API
LEAGUE_ID = 501  # Scottish Premiership
SEASON_ID = 25598  # Temporada 25/26


def get_all_teams():
    """Obtiene todos los equipos de la temporada"""
    url = f"https://api.sportmonks.com/v3/football/seasons/{SEASON_ID}"
    params = {
        'api_token': API_TOKEN,
        'include': 'teams'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        teams = data.get('data', {}).get('teams', [])
        return sorted(teams, key=lambda x: x['name'])
    
    except Exception as e:
        logger.error(f"Error al obtener equipos: {e}")
        return []


def get_team_squad(team_id):
    """Obtiene la plantilla de un equipo específico"""
    url = f"https://api.sportmonks.com/v3/football/squads/seasons/{SEASON_ID}/teams/{team_id}"
    params = {
        'api_token': API_TOKEN,
        'include': 'player.position'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return data.get('data', [])
    
    except Exception as e:
        logger.error(f"Error al obtener plantilla del equipo {team_id}: {e}")
        return []


def map_position_name_to_db(position_name):
    """Mapea el nombre de posición de la API al enum de la BD"""
    if not position_name:
        return DBPosition.MID  # Default
    
    position_lower = position_name.lower()
    
    if 'goalkeeper' in position_lower or 'keeper' in position_lower:
        return DBPosition.GK
    elif 'defender' in position_lower or 'defence' in position_lower:
        return DBPosition.DEF
    elif 'midfielder' in position_lower or 'midfield' in position_lower:
        return DBPosition.MID
    elif 'attacker' in position_lower or 'forward' in position_lower or 'striker' in position_lower:
        return DBPosition.FWD
    else:
        return DBPosition.MID  # Default


def sincronizar_plantillas():
    """Sincroniza todas las plantillas de equipos con la BD"""
    
    print("\n" + "="*130)
    print("🔄 SINCRONIZACIÓN DE PLANTILLAS - TEMPORADA 25/26")
    print("="*130 + "\n")
    
    if not API_TOKEN:
        logger.error("SPORTMONKS_API_KEY no está configurada")
        return
    
    db = next(get_db())
    
    try:
        # 1. Obtener todos los equipos
        print("📋 Obteniendo equipos de la Scottish Premiership 25/26...\n")
        teams = get_all_teams()
        
        if not teams:
            print("❌ No se pudieron obtener los equipos")
            return
        
        print(f"✅ Encontrados {len(teams)} equipos\n")
        
        total_jugadores_api = 0
        total_jugadores_bd = 0
        total_nuevos = 0
        total_faltantes = 0
        
        resumen_equipos = []
        
        # 2. Procesar cada equipo
        for team in teams:
            team_id = team.get('id')
            team_name = team.get('name')
            
            print(f"\n{'='*130}")
            print(f"🏟️  {team_name} (ID: {team_id})")
            print(f"{'='*130}")
            
            # Obtener plantilla desde la API
            squad = get_team_squad(team_id)
            
            if not squad:
                print(f"⚠️  No se pudo obtener la plantilla")
                continue
            
            print(f"📊 Jugadores en API: {len(squad)}")
            total_jugadores_api += len(squad)
            
            # Obtener jugadores existentes en BD para este equipo
            existing_players = db.query(Player).filter(
                Player.current_team == team_name,
                Player.is_legend == 0
            ).all()
            
            # Obtener TODOS los sportmonks_ids que ya existen en la BD (globalmente)
            all_existing_sportmonks_ids = {
                p.sportmonks_id for p in db.query(Player.sportmonks_id).filter(
                    Player.sportmonks_id.isnot(None)
                ).all()
            }
            
            existing_sportmonks_ids = {p.sportmonks_id for p in existing_players}
            print(f"📊 Jugadores en BD: {len(existing_players)}")
            total_jugadores_bd += len(existing_players)
            
            # Comparar
            nuevos_jugadores = []
            
            for member in squad:
                player_info = member.get('player', {})
                sportmonks_id = player_info.get('id')
                display_name = player_info.get('display_name', 'Desconocido')
                
                # Verificar si el jugador ya existe GLOBALMENTE en la BD
                if sportmonks_id in all_existing_sportmonks_ids:
                    continue  # Ya existe, saltamos
                
                if sportmonks_id not in existing_sportmonks_ids:
                    # Obtener posición
                    position_info = player_info.get('position', {})
                    position_name = position_info.get('name', 'Midfielder')
                    db_position = map_position_name_to_db(position_name)
                    
                    nuevos_jugadores.append({
                        'name': display_name,
                        'sportmonks_id': sportmonks_id,
                        'position': db_position,
                        'team': team_name
                    })
            
            # Mostrar resumen del equipo
            if nuevos_jugadores:
                print(f"\n✨ Jugadores NUEVOS encontrados: {len(nuevos_jugadores)}")
                for idx, player_data in enumerate(nuevos_jugadores[:10], 1):
                    print(f"   {idx}. {player_data['name']} ({player_data['position'].name})")
                
                if len(nuevos_jugadores) > 10:
                    print(f"   ... y {len(nuevos_jugadores) - 10} más")
                
                total_nuevos += len(nuevos_jugadores)
                
                # Crear jugadores en la BD
                print(f"\n💾 Guardando {len(nuevos_jugadores)} jugadores nuevos...")
                for player_data in nuevos_jugadores:
                    new_player = Player(
                        name=player_data['name'],
                        sportmonks_id=player_data['sportmonks_id'],
                        age=25,  # Placeholder
                        position=player_data['position'],
                        nationality="Scotland",  # Placeholder
                        overall_rating=70,
                        potential=75,
                        current_team=player_data['team']
                    )
                    db.add(new_player)
                
                db.commit()
                print(f"✅ Jugadores guardados")
            else:
                print(f"✅ Equipo ya completo en BD")
            
            # Verificar jugadores que están en BD pero no en API
            api_sportmonks_ids = {member.get('player', {}).get('id') for member in squad}
            jugadores_obsoletos = [
                p for p in existing_players 
                if p.sportmonks_id not in api_sportmonks_ids
            ]
            
            if jugadores_obsoletos:
                print(f"\n⚠️  Jugadores en BD pero NO en API (posibles traspasos): {len(jugadores_obsoletos)}")
                for idx, player in enumerate(jugadores_obsoletos[:5], 1):
                    print(f"   {idx}. {player.name}")
                
                if len(jugadores_obsoletos) > 5:
                    print(f"   ... y {len(jugadores_obsoletos) - 5} más")
                
                total_faltantes += len(jugadores_obsoletos)
            
            # Guardar resumen
            resumen_equipos.append({
                'nombre': team_name,
                'api': len(squad),
                'bd_inicial': len(existing_players),
                'bd_final': len(existing_players) + len(nuevos_jugadores),
                'nuevos': len(nuevos_jugadores),
                'obsoletos': len(jugadores_obsoletos)
            })
        
        # Resumen final
        print(f"\n\n{'='*130}")
        print("📊 RESUMEN FINAL DE SINCRONIZACIÓN")
        print(f"{'='*130}\n")
        
        print(f"{'Equipo':<25} {'API':>6} {'BD Inicial':>11} {'BD Final':>11} {'Nuevos':>8} {'Obsoletos':>10}")
        print("-" * 78)
        
        for equipo in resumen_equipos:
            print(f"{equipo['nombre']:<25} {equipo['api']:>6} {equipo['bd_inicial']:>11} "
                  f"{equipo['bd_final']:>11} {equipo['nuevos']:>8} {equipo['obsoletos']:>10}")
        
        print("-" * 78)
        print(f"{'TOTAL':<25} {total_jugadores_api:>6} {total_jugadores_bd:>11} "
              f"{total_jugadores_bd + total_nuevos:>11} {total_nuevos:>8} {total_faltantes:>10}")
        
        print(f"\n✅ Sincronización completada")
        print(f"   - Jugadores añadidos: {total_nuevos}")
        print(f"   - Jugadores obsoletos detectados: {total_faltantes}")
        print(f"\n{'='*130}\n")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error durante la sincronización: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    sincronizar_plantillas()
