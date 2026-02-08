"""
PASO 3: Crear Jornadas
Pobla la tabla gameweeks con todas las jornadas de la temporada
"""

import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.database import get_db
from app.models.models import Gameweek

# Jornadas Scottish Premiership 2024-25
GAMEWEEKS_DATA = [
    {'number': 1, 'start': '2024-08-04 12:00:00', 'end': '2024-08-04 23:59:59'},
    {'number': 2, 'start': '2024-08-10 12:00:00', 'end': '2024-08-11 23:59:59'},
    {'number': 3, 'start': '2024-08-24 12:00:00', 'end': '2024-08-25 23:59:59'},
    # Añadir más según disponibilidad
]

def populate_gameweeks():
    """Crea todas las jornadas en la BD"""
    
    print("\n" + "="*100)
    print("📅 PASO 3: CREAR JORNADAS")
    print("="*100 + "\n")
    
    db = next(get_db())
    
    try:
        created_count = 0
        
        for gw_data in GAMEWEEKS_DATA:
            # Verificar si ya existe
            existing = db.query(Gameweek).filter(
                Gameweek.number == gw_data['number']
            ).first()
            
            if existing:
                print(f"  Jornada {gw_data['number']}: Ya existe, omitiendo")
                continue
            
            # Crear nueva jornada
            gameweek = Gameweek(
                number=gw_data['number'],
                start_date=datetime.strptime(gw_data['start'], '%Y-%m-%d %H:%M:%S'),
                end_date=datetime.strptime(gw_data['end'], '%Y-%m-%d %H:%M:%S'),
                is_active=False,
                is_finished=True
            )
            
            db.add(gameweek)
            created_count += 1
            print(f"  Jornada {gw_data['number']}: ✅ Creada")
        
        db.commit()
        
        print(f"\n✅ JORNADAS CREADAS: {created_count}")
        print(f"   Total en BD: {db.query(Gameweek).count()}")
        
        print("\n✅ PASO 3 COMPLETADO\n")
        print("="*100 + "\n")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__== "__main__":
    populate_gameweeks()
