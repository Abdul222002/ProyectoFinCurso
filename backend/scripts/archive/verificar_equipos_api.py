"""
Script para verificar nombres de equipos en la API de Sportmonks
y listar jugadores disponibles para cada equipo
"""

import sys
import os
from datetime import datetime

# Añadir paths necesarios
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from sqlalchemy.orm import Session
from app.core.database import engine, get_db, Base
from app.models.models import Player, Match, Gameweek

from scripts.sistema_puntos_oficial import (
    SportmonksAPIClient,
    API_TOKEN,
    logger
)

def verificar_equipos_api():
    """Verifica los nombres de equipos y lista jugadores de la API"""
    
    print("\n" + "="*130)
    print("🔍 VERIFICACIÓN DE EQUIPOS EN SPORTMONKS API")
    print("="*130 + "\n")
    
    if not API_TOKEN:
        logger.error("SPORTMONKS_API_KEY no está configurada")
        return
    
    db = next(get_db())
    api_client = SportmonksAPIClient(API_TOKEN)
    
    try:
        # Obtener un partido de muestra de cada equipo
        matches = db.query(Match).join(Gameweek).filter(
            Gameweek.number.in_([1, 2, 3])
        ).limit(5).all()
        
        equipos_verificados = set()
        
        for match in matches:
            print(f"\n{'='*130}")
            print(f"📋 Verificando partido: {match.home_team} vs {match.away_team}")
            print(f"   Sportmonks ID: {match.sportmonks_id}")
            print(f"{'='*130}\n")
            
            # Obtener datos del partido
            fixture_data = api_client.get_fixture(match.sportmonks_id)
            
            if not fixture_data:
                print(f"❌ No se pudo obtener datos del fixture {match.sportmonks_id}\n")
                continue
            
            participants = fixture_data.get('participants', [])
            
            for participant in participants:
                team_api_name = participant.get('name', 'UNKNOWN')
                team_id = participant.get('id')
                location = participant.get('meta', {}).get('location', 'unknown')
                
                team_bd_name = match.home_team if location == 'home' else match.away_team
                
                if team_api_name not in equipos_verificados:
                    equipos_verificados.add(team_api_name)
                    
                    print(f"🏟️  EQUIPO: {team_api_name}")
                    print(f"   API ID: {team_id}")
                    print(f"   Nombre en BD: {team_bd_name}")
                    print(f"   {'✅ COINCIDE' if team_api_name == team_bd_name else '⚠️ DIFERENTE'}")
                    
                    # Contar jugadores en BD
                    players_in_bd = db.query(Player).filter(
                        Player.current_team == team_bd_name,
                        Player.is_legend == 0
                    ).count()
                    
                    print(f"   Jugadores en BD: {players_in_bd}")
                    
                    # Obtener jugadores del equipo desde la API
                    lineups = fixture_data.get('lineups', [])
                    players_in_lineup = [
                        p for p in lineups 
                        if p.get('participant_id') == team_id
                    ]
                    
                    print(f"   Jugadores en este partido (API): {len(players_in_lineup)}")
                    
                    if players_in_bd < 10:
                        print(f"   ⚠️ ALERTA: Pocos jugadores en BD!")
                        print(f"\n   📋 Jugadores en lineup de este partido:")
                        for idx, player in enumerate(players_in_lineup[:10], 1):
                            player_name = player.get('player_name', 'Unknown')
                            player_id = player.get('player_id')
                            print(f"      {idx}. {player_name} (ID: {player_id})")
                    
                    print()
        
        # Resumen de equipos en BD
        print(f"\n{'='*130}")
        print("📊 RESUMEN DE EQUIPOS EN BASE DE DATOS")
        print(f"{'='*130}\n")
        
        from sqlalchemy import text
        
        teams_in_bd = db.execute(text("""
            SELECT 
                current_team, 
                COUNT(*) as num_jugadores
            FROM players 
            WHERE is_legend = 0
            GROUP BY current_team
            ORDER BY num_jugadores ASC
        """)).fetchall()
        
        print(f"{'Equipo':<20} {'Jugadores':>10}")
        print("-" * 32)
        for team, count in teams_in_bd:
            alert = " ⚠️" if count < 15 else ""
            print(f"{team:<20} {count:>10}{alert}")
        
        print(f"\n{'='*130}\n")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    verificar_equipos_api()
