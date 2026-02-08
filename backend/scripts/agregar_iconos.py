"""
Script para agregar los 100 iconos/leyendas del futbol a la base de datos
"""

import sys
import os
import csv
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.models import Player, Position, CardRarity

CSV_PATH = os.path.join(os.path.dirname(__file__), '../data/football_icons.csv')

# Mapeo de posiciones
POSITION_MAP = {
    'GK': Position.GK,
    'DEF': Position.DEF,
    'MID': Position.MID,
    'FWD': Position.FWD
}


def calcular_precio_icono(ovr: int, position: Position) -> float:
    """Calcula precio para iconos - son MUY caros"""
    # Multiplicador por posicion
    position_multiplier = {
        Position.GK: 0.85,
        Position.DEF: 0.90,
        Position.MID: 1.0,
        Position.FWD: 1.15
    }
    
    multiplier = position_multiplier.get(position, 1.0)
    
    # Iconos son GOLD y muy caros
    # OVR 99 (Pele, Maradona) = EUR 100M+
    # OVR 95-98 = EUR 80M-100M
    # OVR 90-94 = EUR 60M-80M
    
    if ovr >= 98:
        base = 100000000 + (ovr - 98) * 10000000  # 100M - 120M
    elif ovr >= 95:
        base = 80000000 + (ovr - 95) * 6666666    # 80M - 100M
    elif ovr >= 92:
        base = 70000000 + (ovr - 92) * 3333333    # 70M - 80M
    else:
        base = 60000000 + (ovr - 90) * 5000000    # 60M - 70M
    
    return base * multiplier


def agregar_iconos():
    """Agrega los 100 iconos a la base de datos"""
    
    print("=" * 80)
    print("AGREGAR ICONOS DEL FUTBOL")
    print("=" * 80 + "\n")
    
    db = SessionLocal()
    
    try:
        # Verificar si ya hay iconos
        iconos_existentes = db.query(Player).filter(Player.is_legend == True).count()
        
        if iconos_existentes > 0:
            print(f"Ya hay {iconos_existentes} iconos en la BD.")
            respuesta = input("Deseas reemplazarlos? (s/n): ")
            if respuesta.lower() != 's':
                print("Operacion cancelada.")
                return
            
            # Eliminar iconos existentes
            db.query(Player).filter(Player.is_legend == True).delete()
            db.commit()
            print(f"Eliminados {iconos_existentes} iconos existentes.\n")
        
        # Cargar CSV
        print(f"Cargando iconos desde: {CSV_PATH}")
        iconos_agregados = 0
        
        with open(CSV_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                nombre = row['name']
                posicion = POSITION_MAP.get(row['position'], Position.MID)
                nacionalidad = row['nationality']
                edad = int(row['age'])
                overall = int(row['overall'])
                
                # Stats
                pace = int(row['pace'])
                shooting = int(row['shooting'])
                passing = int(row['passing'])
                dribbling = int(row['dribbling'])
                defending = int(row['defending'])
                physical = int(row['physical'])
                
                # Calcular precio
                precio = calcular_precio_icono(overall, posicion)
                
                # Crear jugador
                player = Player(
                    sportmonks_id=None,  # Los iconos no tienen ID de Sportmonks
                    name=nombre,
                    age=edad,
                    position=posicion,
                    nationality=nacionalidad,
                    overall_rating=overall,
                    potential=overall,  # Los iconos ya estan en su maximo
                    current_team="Icons",
                    is_legend=True,  # IMPORTANTE
                    base_rarity=CardRarity.GOLD,  # Todos los iconos son GOLD
                    current_price=precio,
                    target_price=precio,
                    image_url=None,
                    pace=pace,
                    shooting=shooting,
                    passing=passing,
                    dribbling=dribbling,
                    defending=defending,
                    physical=physical
                )
                
                db.add(player)
                iconos_agregados += 1
                
                # Mostrar progreso
                if iconos_agregados <= 20:
                    print(f"  {iconos_agregados}. {nombre} ({posicion.value}) - OVR {overall} - EUR {precio/1000000:.1f}M")
        
        # Commit
        db.commit()
        
        print(f"\n...")
        print(f"OK {iconos_agregados} iconos agregados exitosamente!\n")
        
        # Estadisticas finales
        total_players = db.query(Player).count()
        total_legends = db.query(Player).filter(Player.is_legend == True).count()
        total_regular = db.query(Player).filter(Player.is_legend == False).count()
        
        print("=" * 80)
        print("RESUMEN:")
        print("=" * 80)
        print(f"Total jugadores en BD: {total_players}")
        print(f"  - Leyendas: {total_legends}")
        print(f"  - Jugadores regulares: {total_regular}")
        
        # Top 10 iconos
        result = db.execute(text("""
            SELECT name, position, overall_rating, current_price
            FROM players
            WHERE is_legend = TRUE
            ORDER BY overall_rating DESC, current_price DESC
            LIMIT 10
        """))
        
        print("\nTop 10 Iconos:")
        for i, row in enumerate(result, 1):
            print(f"  {i}. {row[0]} ({row[1]}) - OVR {row[2]} - EUR {row[3]/1000000:.1f}M")
        
        print("\n" + "=" * 80)
        print("ICONOS AGREGADOS EXITOSAMENTE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    agregar_iconos()
