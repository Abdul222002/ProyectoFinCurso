"""
Script para bloquear (congelar) las alineaciones de TODOS los usuarios
para la jornada activa.
Debe ejecutarse justo al momento del 'Límite' (cuando empieza el primer partido de la jornada).
"""

import sys
import os
from datetime import datetime

# Fix for windows emoji output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Ajustar ruta para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.models import Gameweek, GameweekLineup, Team, UserCard

def lock_all_lineups(auto_mode=False):
    if not auto_mode:
        print("\n" + "="*50)
        print("🔒 INICIANDO BLOQUEO DE ALINEACIONES GLOBALES")
        print("="*50 + "\n")

    db = SessionLocal()
    locked_count = 0
    already_locked = 0
    
    try:
        # 1. Buscar la jornada activa actual
        active_gw = db.query(Gameweek).filter_by(is_active=True).first()
        if not active_gw:
            if not auto_mode:
                print("❌ No hay una jornada activa actualmente en la base de datos.")
            return locked_count
            
        if not auto_mode:
            print(f"📌 Jornada Activa: {active_gw.number}")
            print(f"⏳ Cierre Oficial: {active_gw.start_date}")
        
        # Opcional: Validar si de verdad ya pasó la fecha de inicio
        # En auto_mode, ESTO ES OBLIGATORIO para no bloquear antes de tiempo
        ahora = datetime.utcnow()
        if auto_mode and ahora < active_gw.start_date:
            return locked_count # Aún falta para el límite, no hacer nada
            
        if not auto_mode and ahora < active_gw.start_date:
            print("⚠️ AVISO: Aún no se ha alcanzado la fecha límite oficial de la jornada, pero ejecutando comando manual.")
        
        # 2. Obtener todos los equipos de la plataforma
        teams = db.query(Team).all()
        if not auto_mode:
            print(f"👥 Equipos totales: {len(teams)}")
        
        locked_count = 0
        already_locked = 0
        
        # 3. Guardar snapshot por cada equipo
        for team in teams:
            # Buscar si el usuario ya guardó/congeló su alineación (ej: modificó y guardó antes del límite)
            existing_lineup = db.query(GameweekLineup).filter_by(
                team_id=team.id,
                gameweek_id=active_gw.id
            ).first()
            
            if existing_lineup:
                already_locked += 1
                continue
                
            # Si no ha guardado, tomamos su 11 titular actual por defecto
            active_cards = db.query(UserCard).filter_by(
                team_id=team.id,
                is_in_lineup=True
            ).all()
            
            # Solo guardamos a los titulares (is_in_lineup=True)
            player_ids_str = ",".join(str(c.id) for c in active_cards)
            
            gw_lineup = GameweekLineup(
                team_id=team.id,
                gameweek_id=active_gw.id,
                player_ids=player_ids_str,
                active_formation=team.active_formation
                # points_earned=0.0 (default)
            )
            db.add(gw_lineup)
            locked_count += 1
            
        db.commit()
        
        if not auto_mode:
            print("\n✅ PROCESO COMPLETADO")
            print(f"   -> Alineaciones generadas/congeladas automáticamente: {locked_count}")
            print(f"   -> Alineaciones que ya habían sido confirmadas por el usuario: {already_locked}")
            print("\nYa puedes calcular los puntos del fin de semana de forma segura con update_weekend.py")
            
        return locked_count
        
    except Exception as e:
        db.rollback()
        if not auto_mode:
            print(f"\n❌ Error fatal: {e}")
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    lock_all_lineups(auto_mode=False)
