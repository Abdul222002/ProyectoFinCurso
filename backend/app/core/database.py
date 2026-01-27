"""
Configuración de la base de datos MySQL con SQLAlchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Motor de base de datos
# echo=True muestra las queries SQL en consola (útil para desarrollo)
engine = create_engine(
    settings.database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Verifica la conexión antes de usarla
    pool_recycle=3600,   # Recicla conexiones cada hora
)

# Sesión de base de datos
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para los modelos
Base = declarative_base()


def get_db():
    """
    Dependency para FastAPI - Crea una sesión de BD para cada request
    Uso:
        @app.get("/players")
        def get_players(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicializa la base de datos - Crea todas las tablas
    Se ejecutará desde seed_db.py
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos inicializada correctamente")


def test_connection():
    """
    Prueba la conexión a la base de datos
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✅ Conexión a MySQL exitosa")
        return True
    except Exception as e:
        print(f"❌ Error al conectar con MySQL: {e}")
        return False
