"""
MIGRACIÓN MAESTRA - Ejecuta todo el proceso
Resetea BD, pobla jugadores, crea jornadas y migra todas las stats
"""

import sys
import os
from datetime import datetime

# Importar todos los scripts
import sys
import os

# Añadir path
current_dir = os.path.dirname(os.path.abspath(__file__))
migration_dir = os.path.join(current_dir, 'migration')
sys.path.insert(0, migration_dir)

# Importar módulos
import importlib.util

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Cargar módulos
reset_db_module = load_module('reset_database', os.path.join(migration_dir, '1_reset_database.py'))
populate_players_module = load_module('populate_players', os.path.join(migration_dir, '2_populate_players.py'))
populate_gw_module = load_module('populate_gameweeks', os.path.join(migration_dir, '3_populate_gameweeks.py'))
migrate_gw_module = load_module('migrate_all_gameweeks', os.path.join(migration_dir, '4_migrate_all_gameweeks.py'))

reset_database = reset_db_module.reset_database
populate_players = populate_players_module.populate_players
populate_gameweeks = populate_gw_module.populate_gameweeks
migrate_all_gameweeks = migrate_gw_module.migrate_all_gameweeks


def master_migration():
    """Ejecuta la migración completa"""
    
    print("\n" + "="*100)
    print("🚀 MIGRACIÓN COMPLETA DE BASE DE DATOS")
    print("="*100)
    print(f"\n⏰ Iniciada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    start_time = datetime.now()
    
    # PASO 1: Reset Base de Datos
    print("╔" + "="*98 + "╗")
    print("║" + " "*30 + "PASO 1: RESET BD" + " "*52 + "║")
    print("╚" + "="*98 + "╝")
    
    if not reset_database():
        print("\n❌ MIGRACIÓN ABORTADA: Falló el reset de BD\n")
        return False
    
    # PASO 2: Poblar Jugadores
    print("\n╔" + "="*98 + "╗")
    print("║" + " "*26 + "PASO 2: POBLAR JUGADORES" + " "*48 + "║")
    print("╚" + "="*98 + "╝")
    
    if not populate_players():
        print("\n❌ MIGRACIÓN ABORTADA: Falló la población de jugadores\n")
        return False
    
    # PASO 3: Crear Jornadas
    print("\n╔" + "="*98 + "╗")
    print("║" + " "*28 + "PASO 3: CREAR JORNADAS" + " "*48 + "║")
    print("╚" + "="*98 + "╝")
    
    if not populate_gameweeks():
        print("\n❌ MIGRACIÓN AABORTADA: Falló la creación de jornadas\n")
        return False
    
    # PASO 4: Migrar Todas las Jornadas
    print("\n╔" + "="*98 + "╗")
    print("║" + " "*22 + "PASO 4: MIGRAR TODAS LAS JORNADAS" + " "*42 + "║")
    print("╚" + "="*98 + "╝")
    
    if not migrate_all_gameweeks():
        print("\n⚠️  ADVERTENCIA: Algunas jornadas fallaron\n")
    
    # Resumen Final
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*100)
    print("✅ ¡MIGRACIÓN COMPLETA EXITOSA!")
    print("="*100)
    print(f"\n⏱️  Duración total: {duration:.1f} segundos ({duration/60:.1f} minutos)")
    print(f"⏰ Finalizada: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Estadísticas finales
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        from app.core.database import get_db
        from app.models.models import Player, Gameweek, Match, PlayerMatchStats
        from sqlalchemy import func
        
        db = next(get_db())
        
        total_players = db.query(Player).count()
        total_gameweeks = db.query(Gameweek).count()
        total_matches = db.query(Match).count()
        total_stats = db.query(PlayerMatchStats).count()
        
        avg_price = db.query(Player).with_entities(
            func.avg(Player.current_price)
        ).scalar() / 1000000 if total_players > 0 else 0
        
        print("📊 ESTADÍSTICAS FINALES:")
        print(f"   - Jugadores: {total_players}")
        print(f"   - Jornadas: {total_gameweeks}")
        print(f"   - Partidos: {total_matches}")
        print(f"   - Stats totales: {total_stats}")
        print(f"   - Precio promedio: €{avg_price:.2f}M")
        
        db.close()
        
    except Exception as e:
        print(f"\n⚠️  No se pudieron obtener estadísticas finales: {e}")
    
    print("\n" + "="*100)
    print("🎉 ¡BASE DE DATOS LISTA PARA USAR!")
    print("="*100 + "\n")
    
    return True


if __name__ == "__main__":
    success = master_migration()
    
    if not success:
        print("\n❌ La migración no se completó correctamente")
        sys.exit(1)
    else:
        print("✅ Todo listo. Puedes iniciar tu aplicación.")
        sys.exit(0)
