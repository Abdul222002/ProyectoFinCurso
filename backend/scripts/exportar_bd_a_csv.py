"""
Script para exportar jugadores desde la BASE DE DATOS a CSV
Ya que las posiciones en la BD están correctas (corregidas con FIFA)
"""

import sys
import os
import csv
import logging

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Player

def exportar_desde_bd():
    """Exporta jugadores desde la BD a CSV"""
    
    print("="*60)
    print("📤 EXPORTAR JUGADORES DESDE BASE DE DATOS")
    print("="*60 + "\n")
    
    db = SessionLocal()
    
    try:
        # Obtener todos los jugadores
        players = db.query(Player).all()
        print(f"📊 Total jugadores en BD: {len(players)}\n")
        
        # Preparar datos para CSV
        jugadores_export = []
        
        for player in players:
            jugadores_export.append({
                'sportmonks_id': player.sportmonks_id or '',
                'name': player.name,
                'position': player.position.value,
                'team': player.current_team,
                'age': player.age,
                'nationality': player.nationality,
                'overall': player.overall_rating,
                'rarity': player.base_rarity.value,
                'price': int(player.current_price)
            })
        
        # Guardar a CSV
        csv_filename = 'jugadores_bd_export.csv'
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['sportmonks_id', 'name', 'position', 'team', 'age', 'nationality', 'overall', 'rarity', 'price']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for jugador in jugadores_export:
                writer.writerow(jugador)
        
        print(f"✅ CSV guardado: {csv_filename}\n")
        
        # Estadísticas
        from collections import Counter
        
        pos_count = Counter([j['position'] for j in jugadores_export])
        rarity_count = Counter([j['rarity'] for j in jugadores_export])
        team_count = Counter([j['team'] for j in jugadores_export])
        
        print("="*60)
        print("📊 RESUMEN DEL EXPORT")
        print("="*60)
        print(f"Total jugadores: {len(jugadores_export)}")
        print(f"Archivo: {csv_filename}")
        
        print(f"\n📋 Por posición:")
        for pos, count in pos_count.most_common():
            porcentaje = (count / len(jugadores_export)) * 100
            print(f"   {pos}: {count} ({porcentaje:.1f}%)")
        
        print(f"\n🎴 Por rareza:")
        for rarity, count in rarity_count.most_common():
            porcentaje = (count / len(jugadores_export)) * 100
            print(f"   {rarity}: {count} ({porcentaje:.1f}%)")
        
        print(f"\n🏆 Por equipo:")
        for team, count in team_count.most_common():
            print(f"   {team}: {count}")
        
        # Top jugadores
        jugadores_export_sorted = sorted(jugadores_export, key=lambda x: x['overall'], reverse=True)
        
        print(f"\n⭐ Top 10 jugadores (OVR):")
        for i, j in enumerate(jugadores_export_sorted[:10], 1):
            print(f"   {i}. {j['name']} ({j['position']}) - OVR {j['overall']} - {j['team']}")
            print(f"      Precio: €{j['price']:,}")
        
        print("\n" + "="*60)
        print("✅ EXPORTACIÓN COMPLETADA")
        print("="*60)
        print(f"\n💡 Este CSV tiene las posiciones CORRECTAS de la base de datos")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    exportar_desde_bd()
