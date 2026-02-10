"""
Script para obtener los IDs reales de partidos desde la API de Sportmonks
y actualizar el Match 33 (St. Mirren vs Rangers) con su ID correcto
"""

import sys
import os

# Añadir paths necesarios
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import requests
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Match, Gameweek

from scripts.sistema_puntos_oficial import API_TOKEN, logger

# Equipos escoceses para filtrar
EQUIPOS_ESCOCESES = [
    "Celtic", "Rangers", "Aberdeen", "Hearts", "Hibernian", 
    "Dundee", "Motherwell", "St. Mirren", "Kilmarnock", 
    "Ross County", "St. Johnstone", "Livingston", "Falkirk",
    "Dundee United"
]


def es_equipo_escoces(nombre):
    """Verifica si un equipo es de Escocia"""
    for clave in EQUIPOS_ESCOCESES:
        if clave in nombre:
            return True
    return False


def obtener_partidos_por_fechas(fecha_inicio, fecha_fin):
    """Obtiene partidos de la API en un rango de fechas"""
    url = f"https://api.sportmonks.com/v3/football/fixtures/between/{fecha_inicio}/{fecha_fin}"
    params = {
        'api_token': API_TOKEN,
        'include': 'participants,scores'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json().get('data', [])
        
        partidos_escoceses = []
        
        for fix in data:
            participants = fix.get('participants', [])
            local = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
            visita = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})
            
            nombre_l = local.get('name', '')
            nombre_v = visita.get('name', '')
            
            # Filtrar solo partidos escoceses
            if es_equipo_escoces(nombre_l) and es_equipo_escoces(visita):
                # Obtener marcador
                scores = fix.get('scores', [])
                home_score = next((s['score']['goals'] for s in scores
                                 if s['description'] == 'CURRENT' 
                                 and s['participant_id'] == local.get('id')), 0)
                away_score = next((s['score']['goals'] for s in scores
                                 if s['description'] == 'CURRENT' 
                                 and s['participant_id'] == visita.get('id')), 0)
                
                partidos_escoceses.append({
                    'id': fix.get('id'),
                    'home_team': nombre_l,
                    'away_team': nombre_v,
                    'home_score': home_score,
                    'away_score': away_score,
                    'fecha': fix.get('starting_at', '').split(' ')[0] if fix.get('starting_at') else 'N/A'
                })
        
        return partidos_escoceses
    
    except Exception as e:
        logger.error(f"Error al obtener partidos: {e}")
        return []


def actualizar_ids_partidos():
    """Busca IDs reales de partidos y actualiza la BD"""
    
    print("\n" + "="*130)
    print("🔍 BÚSQUEDA DE IDs REALES DE PARTIDOS")
    print("="*130 + "\n")
    
    if not API_TOKEN:
        logger.error("SPORTMONKS_API_KEY no está configurada")
        return
    
    db = next(get_db())
    
    try:
        # Rangos de fechas para las 3 jornadas (TEMPORADA 2025-2026)
        # Basado en el script del usuario: agosto-septiembre 2025
        rangos_fechas = [
            ("2025-08-03", "2025-08-05", 1),  # Jornada 1
            ("2025-08-09", "2025-08-12", 2),  # Jornada 2  
            ("2025-08-22", "2025-08-25", 3),  # Jornada 3 parte 1
            ("2025-09-22", "2025-09-24", 3),  # Jornada 3 parte 2 (algunos partidos se reprogramaron)
        ]
        
        partidos_encontrados = []
        
        # Obtener partidos de cada jornada
        for fecha_inicio, fecha_fin, jornada_num in rangos_fechas:
            print(f"\n📅 Buscando partidos de Jornada {jornada_num} ({fecha_inicio} a {fecha_fin})...")
            
            partidos = obtener_partidos_por_fechas(fecha_inicio, fecha_fin)
            
            if partidos:
                print(f"✅ Encontrados {len(partidos)} partidos:")
                for p in partidos:
                    print(f"   - {p['home_team']} {p['home_score']}-{p['away_score']} {p['away_team']} "
                          f"(ID: {p['id']}, Fecha: {p['fecha']})")
                    partidos_encontrados.append({**p, 'jornada': jornada_num})
            else:
                print(f"⚠️  No se encontraron partidos")
        
        if not partidos_encontrados:
            print("\n❌ No se encontraron partidos en ninguna jornada")
            return
        
        # Comparar con la BD y actualizar
        print(f"\n\n{'='*130}")
        print("🔄 COMPARACIÓN Y ACTUALIZACIÓN CON LA BD")
        print(f"{'='*130}\n")
        
        actualizaciones = 0
        match_33_encontrado = False
        
        for partido_api in partidos_encontrados:
            # Buscar partido en BD por equipos
            match = db.query(Match).filter(
                Match.home_team.like(f"%{partido_api['home_team']}%"),
                Match.away_team.like(f"%{partido_api['away_team']}%")
            ).first()
            
            if match:
                gameweek = db.query(Gameweek).filter(Gameweek.id == match.gameweek_id).first()
                jornada_bd = gameweek.number if gameweek else 0
                
                # Verificar si el ID es diferente
                if match.sportmonks_id != partido_api['id']:
                    print(f"🔧 ACTUALIZACIÓN NECESARIA:")
                    print(f"   Partido: {partido_api['home_team']} vs {partido_api['away_team']}")
                    print(f"   Match ID BD: {match.id}")
                    print(f"   Jornada BD: {jornada_bd}")
                    print(f"   Sportmonks ID Actual: {match.sportmonks_id}")
                    print(f"   Sportmonks ID Correcto: {partido_api['id']}")
                    
                    # Actualizar
                    match.sportmonks_id = partido_api['id']
                    actualizaciones += 1
                    
                    # Si es el Match 33, marcarlo
                    if match.id == 33:
                        match_33_encontrado = True
                        print(f"   ✨ ¡MATCH 33 ENCONTRADO Y ACTUALIZADO!")
                    
                    print()
                else:
                    print(f"✅ OK: {partido_api['home_team']} vs {partido_api['away_team']} "
                          f"(ID: {partido_api['id']}) ya está correcto")
            else:
                print(f"⚠️  No encontrado en BD: {partido_api['home_team']} vs {partido_api['away_team']}")
        
        # Guardar cambios
        if actualizaciones > 0:
            db.commit()
            print(f"\n✅ {actualizaciones} partido(s) actualizado(s)")
            
            if match_33_encontrado:
                print(f"\n🎯 MATCH 33 CORREGIDO - Ahora puedes recargar sus estadísticas")
        else:
            print(f"\n✅ Todos los IDs ya están correctos")
        
        print(f"\n{'='*130}\n")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    actualizar_ids_partidos()
