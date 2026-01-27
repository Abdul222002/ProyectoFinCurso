"""
Script de Seed - Llena la base de datos con datos iniciales
Este script se ejecutará para poblar la BD con jugadores de la Scottish Premiership
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path para poder importar app
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import init_db, test_connection, SessionLocal
from app.models.player import Player
from app.models.team import Team


def create_sample_players(db):
    """
    Crea jugadores de ejemplo para pruebas
    TODO: Reemplazar con datos reales de Sportmonks API
    """
    
    print("📦 Creando jugadores de ejemplo...")
    
    sample_players = [
        # Rangers FC
        Player(
            name="James Tavernier",
            age=32,
            position="DEF",
            nationality="England",
            overall_rating=78,
            potential=78,
            pace=75,
            shooting=70,
            passing=72,
            dribbling=68,
            defending=76,
            physical=74,
            is_legend=False,
            card_rarity="gold",
            current_team="Rangers FC",
            market_value=500000.0
        ),
        Player(
            name="Alfredo Morelos",
            age=27,
            position="FWD",
            nationality="Colombia",
            overall_rating=76,
            potential=80,
            pace=78,
            shooting=80,
            passing=65,
            dribbling=73,
            defending=40,
            physical=79,
            is_legend=False,
            card_rarity="gold",
            current_team="Rangers FC",
            market_value=750000.0
        ),
        
        # Celtic FC
        Player(
            name="Callum McGregor",
            age=30,
            position="MID",
            nationality="Scotland",
            overall_rating=77,
            potential=77,
            pace=70,
            shooting=72,
            passing=80,
            dribbling=76,
            defending=68,
            physical=70,
            is_legend=False,
            card_rarity="gold",
            current_team="Celtic FC",
            market_value=600000.0
        ),
        Player(
            name="Kyogo Furuhashi",
            age=28,
            position="FWD",
            nationality="Japan",
            overall_rating=79,
            potential=82,
            pace=86,
            shooting=81,
            passing=70,
            dribbling=80,
            defending=35,
            physical=65,
            is_legend=False,
            card_rarity="gold",
            current_team="Celtic FC",
            market_value=850000.0
        ),
        
        # LEYENDAS (para el modo Arena)
        Player(
            name="Henrik Larsson",
            age=52,
            position="FWD",
            nationality="Sweden",
            overall_rating=91,
            potential=91,
            pace=85,
            shooting=92,
            passing=80,
            dribbling=88,
            defending=40,
            physical=75,
            is_legend=True,
            card_rarity="legend",
            current_team=None,
            market_value=5000000.0
        ),
        Player(
            name="Paul Gascoigne",
            age=56,
            position="MID",
            nationality="England",
            overall_rating=90,
            potential=90,
            pace=78,
            shooting=85,
            passing=91,
            dribbling=92,
            defending=65,
            physical=80,
            is_legend=True,
            card_rarity="legend",
            current_team=None,
            market_value=4500000.0
        ),
    ]
    
    db.add_all(sample_players)
    db.commit()
    
    print(f"✅ {len(sample_players)} jugadores creados correctamente")


def create_sample_team(db):
    """
    Crea un equipo de ejemplo
    """
    
    print("🏟️ Creando equipo de ejemplo...")
    
    sample_team = Team(
        name="FC Ultimate Legends",
        shield_url="https://example.com/shield.png",
        kit_color_primary="#FF0000",
        kit_color_secondary="#FFFFFF",
        budget=1000000.0
    )
    
    db.add(sample_team)
    db.commit()
    
    # Asignar algunos jugadores al equipo
    players = db.query(Player).filter(Player.is_legend == False).limit(5).all()
    for player in players:
        player.team_id = sample_team.id
    
    db.commit()
    
    # Calcular media del equipo
    sample_team.calculate_overall_rating()
    db.commit()
    
    print(f"✅ Equipo '{sample_team.name}' creado (OVR: {sample_team.overall_rating})")


def main():
    """
    Función principal del seed
    """
    
    print("🚀 Iniciando seed de la base de datos...\n")
    
    # 1. Probar conexión
    if not test_connection():
        print("❌ No se pudo conectar a MySQL. Verifica tu .env")
        return
    
    # 2. Crear tablas
    print("\n📋 Creando tablas...")
    init_db()
    
    # 3. Crear datos de ejemplo
    db = SessionLocal()
    try:
        create_sample_players(db)
        create_sample_team(db)
        
        print("\n✅ ¡Seed completado con éxito!")
        print(f"📊 Total jugadores: {db.query(Player).count()}")
        print(f"🏟️ Total equipos: {db.query(Team).count()}")
        
    except Exception as e:
        print(f"\n❌ Error durante el seed: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
