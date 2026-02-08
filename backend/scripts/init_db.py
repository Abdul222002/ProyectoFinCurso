"""
Script para crear la base de datos y las tablas
"""

import sys
import os

# Ajuste de rutas
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base
from app.models import models  # Importar todos los modelos

def create_database():
    """
    Crea la base de datos si no existe
    """
    # Conexión sin especificar la base de datos
    engine_url = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}"
    engine = create_engine(engine_url)
    
    try:
        with engine.connect() as conn:
            # Crear base de datos si no existe
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.commit()
            print(f"✅ Base de datos '{settings.MYSQL_DATABASE}' creada/verificada")
    except Exception as e:
        print(f"❌ Error creando base de datos: {e}")
        return False
    finally:
        engine.dispose()
    
    return True


def create_tables():
    """
    Crea todas las tablas definidas en los modelos
    """
    try:
        # Conexión a la base de datos específica
        engine = create_engine(settings.database_url)
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        print("✅ Todas las tablas creadas correctamente")
        
        # Mostrar las tablas creadas
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            print(f"\n📋 Tablas en la base de datos ({len(tables)}):")
            for table in tables:
                print(f"   - {table}")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*60)
    print("🔧 INICIALIZACIÓN DE BASE DE DATOS")
    print("="*60 + "\n")
    
    print("1️⃣  Creando base de datos...")
    if not create_database():
        print("\n❌ Falló la creación de la base de datos")
        sys.exit(1)
    
    print("\n2️⃣  Creando tablas...")
    if not create_tables():
        print("\n❌ Falló la creación de las tablas")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ INICIALIZACIÓN COMPLETADA")
    print("="*60)
    print("\n💡 Ahora puedes ejecutar: py backend\\scripts\\seed_db.py")
