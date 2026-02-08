"""
PASO 1: Reset de Base de Datos
Elimina todas las tablas y las vuelve a crear
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.database import engine, Base
from app.models.models import *
from sqlalchemy import text

def reset_database():
    """Elimina y recrea todas las tablas"""
    
    print("\n" + "="*100)
    print("🔄 PASO 1: RESET DE BASE DE DATOS")
    print("="*100 + "\n")
    
    try:
        print("🗑️  Eliminando tablas existentes...")
        
        # Drop todas las tablas
        Base.metadata.drop_all(bind=engine)
        print("✅ Tablas eliminadas\n")
        
        print("🔨 Creando nuevas tablas...")
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas\n")
        
        # Verificar
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            
            print(f"📊 Tablas creadas ({len(tables)}):")
            for table in sorted(tables):
                print(f"   - {table}")
        
        print("\n✅ RESET COMPLETADO CON ÉXITO\n")
        print("="*100 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante el reset: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    reset_database()
