"""
MIGRACIÓN MANUAL - Agregar campos de penaltis
Ejecuta este script directamente si no tienes Alembic configurado
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from app.core.database import engine

def upgrade():
    """Agrega campos de penaltis a player_match_stats"""
    
    print("\n🔄 Aplicando migración: Agregar campos de penaltis\n")
    
    with engine.connect() as conn:
        # Verificar si las columnas ya existen
        try:
            conn.execute(text("SELECT penalty_miss FROM player_match_stats LIMIT 1"))
            print("✅ Los campos de penaltis ya existen")
            return
        except:
            pass  # Las columnas no existen, continuar con la migración
        
        # Agregar columnas
        queries = [
            "ALTER TABLE player_match_stats ADD COLUMN penalty_miss INTEGER DEFAULT 0",
            "ALTER TABLE player_match_stats ADD COLUMN penalty_save INTEGER DEFAULT 0",
            "ALTER TABLE player_match_stats ADD COLUMN penalty_won INTEGER DEFAULT 0",
            "ALTER TABLE player_match_stats ADD COLUMN penalty_committed INTEGER DEFAULT 0",
        ]
        
        for query in queries:
            try:
                conn.execute(text(query))
                col_name = query.split("ADD COLUMN ")[1].split(" ")[0]
                print(f"✅ Agregada columna: {col_name}")
            except Exception as e:
                print(f"⚠️  Error al agregar columna: {e}")
        
        conn.commit()
    
    print("\n✅ Migración completada\n")

def downgrade():
    """Elimina campos de penaltis"""
    
    print("\n🔄 Revirtiendo migración: Eliminar campos de penaltis\n")
    
    with engine.connect() as conn:
        queries = [
            "ALTER TABLE player_match_stats DROP COLUMN penalty_miss",
            "ALTER TABLE player_match_stats DROP COLUMN penalty_save",
            "ALTER TABLE player_match_stats DROP COLUMN penalty_won",
            "ALTER TABLE player_match_stats DROP COLUMN penalty_committed",
        ]
        
        for query in queries:
            try:
                conn.execute(text(query))
                col_name = query.split("DROP COLUMN ")[1]
                print(f"✅ Eliminada columna: {col_name}")
            except Exception as e:
                print(f"⚠️  Error al eliminar columna: {e}")
        
        conn.commit()
    
    print("\n✅ Reversión completada\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
