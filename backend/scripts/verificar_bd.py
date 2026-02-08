"""
Script para verificar los datos en la base de datos
"""

import sys
import os
import logging

# Desactivar logging de SQLAlchemy
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from sqlalchemy import text

def verificar_bd():
    db = SessionLocal()
    
    try:
        print("="*60)
        print("🔍 VERIFICACIÓN DE BASE DE DATOS")
        print("="*60 + "\n")
        
        # Total de jugadores
        result = db.execute(text("SELECT COUNT(*) FROM players"))
        total = result.fetchone()[0]
        print(f"📊 Total de jugadores: {total}\n")
        
        # Por equipo
        result = db.execute(text("""
            SELECT current_team, COUNT(*) as count 
            FROM players 
            GROUP BY current_team 
            ORDER BY count DESC
        """))
        
        print("🏆 Jugadores por equipo:")
        for row in result:
            print(f"   {row[0]}: {row[1]}")
        
        # Por posición
        result = db.execute(text("""
            SELECT position, COUNT(*) as count 
            FROM players 
            GROUP BY position 
            ORDER BY count DESC
        """))
        
        print("\n⚽ Jugadores por posición:")
        for row in result:
            print(f"   {row[0]}: {row[1]}")
        
        # Top 10 jugadores
        result = db.execute(text("""
            SELECT name, position, overall_rating, current_team, current_price 
            FROM players 
            ORDER BY overall_rating DESC, name 
            LIMIT 10
        """))
        
        print("\n⭐ Top 10 jugadores:")
        for i, row in enumerate(result, 1):
            print(f"   {i}. {row[0]} ({row[1]}) - OVR {row[2]} - {row[3]} - €{row[4]:,.0f}")
        
        # Estadísticas de overall
        result = db.execute(text("""
            SELECT 
                MIN(overall_rating) as min_ovr,
                MAX(overall_rating) as max_ovr,
                AVG(overall_rating) as avg_ovr
            FROM players
        """))
        
        row = result.fetchone()
        print(f"\n📈 Estadísticas de Overall:")
        print(f"   Mínimo: {row[0]}")
        print(f"   Máximo: {row[1]}")
        print(f"   Promedio: {row[2]:.1f}")
        
        # Valor total del mercado
        result = db.execute(text("SELECT SUM(current_price) FROM players"))
        total_value = result.fetchone()[0]
        print(f"\n💰 Valor total del mercado: €{total_value:,.0f}")
        
        print("\n" + "="*60)
        print("✅ Verificación completada")
        print("="*60)
        
    finally:
        db.close()

if __name__ == "__main__":
    verificar_bd()
