"""
Script para poblar jugadores faltantes de equipos incompletos
Se enfoca en Falkirk y Dundee United que tienen pocos jugadores
"""

import sys
import os

# Añadir paths necesarios
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from sqlalchemy.orm import Session
from app.core.database import engine, get_db
from app.models.models import Player, Match, Gameweek, Position as DBPosition

from scripts.sistema_puntos_oficial import (
    SportmonksAPIClient,
    API_TOKEN,
    logger,
    StatsExtractor
)

def poblar_equipos_faltantes():
    """Pobla jugadores faltantes de equipos con pocas plantillas"""
    
    print("\n" + "="*130)
    print("👥 POBLANDO JUGADORES FALTANTES")
    print("="*130 + "\n")
    
    if not API_TOKEN:
        logger.error("SPORTMONKS_API_KEY no está configurada")
        return
    
    db = next(get_db())
    api_client = SportmonksAPIClient(API_TOKEN)
    
    try:
        # Equipos a poblar y sus partidos de referencia
        equipos_a_poblar = {
            'Falkirk': [18, 24, 31],  # Falkirk vs Dundee United, Livingston vs Falkirk, Falkirk vs Hibernian
            'Dundee United': [18, 22, 30]  # Falkirk vs Dundee United, Dundee United vs Hearts, Dundee United vs Aberdeen
        }
        
        for team_name, match_ids in equipos_a_poblar.items():
            print(f"\n{'='*130}")
            print(f"🏟️  EQUIPO: {team_name}")
            print(f"{'='*130}\n")
            
            # Contar jugadores actuales
            current_players = db.query(Player).filter(
                Player.current_team == team_name,
                Player.is_legend == 0
            ).count()
            
            print(f"📊 Jugadores actuales en BD: {current_players}")
            
            # Obtener IDs de jugadores existentes para evitar duplicados
            existing_sportmonks_ids = set(
                p.sportmonks_id for p in db.query(Player.sportmonks_id).filter(
                    Player.current_team == team_name
                ).all()
            )
            
            # Procesar cada partido
            all_new_players = {}  # sportmonks_id -> player_data
            
            for match_id in match_ids:
                match = db.query(Match).filter(Match.id == match_id).first()
                if not match:
                    print(f"⚠️  Partido {match_id} no encontrado")
                    continue
                
                print(f"\n📋 Procesando partido {match.id}: {match.home_team} vs {match.away_team}")
                print(f"   Sportmonks ID: {match.sportmonks_id}")
                
                # Obtener datos del partido
                fixture_data = api_client.get_fixture(match.sportmonks_id)
                if not fixture_data:
                    print(f"   ❌ No se pudo obtener datos del fixture")
                    continue
                
                lineups = fixture_data.get('lineups', [])
                participants = fixture_data.get('participants', [])
                
                # Determinar el participant_id del equipo
                team_participant = None
                for p in participants:
                    if p.get('name') == team_name:
                        team_participant = p
                        break
                
                # Intentar buscar por si el nombre es diferente
                if not team_participant:
                    if team_name in match.home_team:
                        team_participant = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), None)
                    elif team_name in match.away_team:
                        team_participant = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), None)
                
                if not team_participant:
                    print(f"   ⚠️  No se encontró el equipo {team_name} en participants")
                    continue
                
                team_participant_id = team_participant.get('id')
                print(f"   ✅ Team Participant ID: {team_participant_id}")
                
                # Filtrar jugadores de este equipo
                team_lineups = [
                    p for p in lineups
                    if p.get('participant_id') == team_participant_id
                ]
                
                print(f"   📌 Jugadores encontrados en lineup: {len(team_lineups)}")
                
                for player_entry in team_lineups:
                    sportmonks_player_id = player_entry.get('player_id')
                    player_name = player_entry.get('player_name', 'Unknown')
                    
                    if sportmonks_player_id in existing_sportmonks_ids:
                        continue  # Ya existe
                    
                    if sportmonks_player_id in all_new_players:
                        continue  # Ya lo tenemos de otro partido
                    
                    # Determinar posición
                    position_type_id = player_entry.get('type_id')
                    position = StatsExtractor.map_position(position_type_id)
                    
                    if position.name == 'GK':
                        db_position = DBPosition.GK
                    elif position.name == 'DEF':
                        db_position = DBPosition.DEF
                    elif position.name == 'MID':
                        db_position = DBPosition.MID
                    else:
                        db_position = DBPosition.FWD
                    
                    all_new_players[sportmonks_player_id] = {
                        'name': player_name,
                        'sportmonks_id': sportmonks_player_id,
                        'position': db_position,
                        'team': team_name
                    }
            
            # Crear los jugadores nuevos en la BD
            if all_new_players:
                print(f"\n✨ Creando {len(all_new_players)} jugadores nuevos:")
                for idx, (sm_id, player_data) in enumerate(all_new_players.items(), 1):
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
                    print(f"   {idx}. {player_data['name']} ({player_data['position'].name})")
                
                db.commit()
                
                # Verificar
                final_count = db.query(Player).filter(
                    Player.current_team == team_name,
                    Player.is_legend == 0
                ).count()
                
                print(f"\n✅ Total jugadores en BD ahora: {final_count} (antes: {current_players})")
            else:
                print(f"\n⚠️  No se encontraron jugadores nuevos")
        
        print(f"\n{'='*130}")
        print("✅ PROCESO COMPLETADO")
        print(f"{'='*130}\n")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    poblar_equipos_faltantes()
