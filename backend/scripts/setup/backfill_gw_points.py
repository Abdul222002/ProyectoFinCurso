import sys
import os

# Añadir el directorio raíz al path para poder importar módulos de la app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.database import SessionLocal
from app.models.models import GameweekLineup, GameweekLineupPlayer, PlayerMatchStats, Match, Player
from app.services.icon_scoring import calculate_icon_points
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill")

def backfill():
    db = SessionLocal()
    try:
        lineups = db.query(GameweekLineup).all()
        logger.info(f"Encontradas {len(lineups)} alineaciones guardadas.")

        updated_count = 0

        for lineup in lineups:
            # Diccionario para buscar rápidamente los stats del jugador en esa jornada
            matches = db.query(Match).filter(Match.gameweek_id == lineup.gameweek_id).all()
            match_ids = [m.id for m in matches]
            
            # Obtener todos los stats de esa jornada
            stats = db.query(PlayerMatchStats).filter(PlayerMatchStats.match_id.in_(match_ids)).all()
            player_pts_dict = {s.player_id: s.fantasy_points for s in stats}

            team_points = 0.0

            for lp in lineup.players:
                if lp.points_earned > 0:
                    team_points += lp.points_earned
                    continue # Ya tiene puntos, no lo sobreescribimos (a menos que quieras forzar el recalculo)
                
                card = lp.card
                if not card:
                    continue
                
                player = db.query(Player).filter(Player.id == card.player_id).first()
                if not player:
                    continue
                
                pts = 0.0
                if player.is_legend:
                    # Como no se guardaban históricamente, generamos uno nuevo acorde a su perfil
                    pts = calculate_icon_points(player)
                    logger.info(f"   Recalculado Icono {player.name} -> {pts} pts")
                else:
                    pts = player_pts_dict.get(player.id, 0.0)
                
                lp.points_earned = pts
                team_points += pts
                updated_count += 1
            
            # Actualizamos el total del lineup también por seguridad
            if lineup.points_earned == 0.0 and team_points > 0:
                lineup.points_earned = team_points

        db.commit()
        logger.info(f"✅ Se han rellenado los puntos de {updated_count} jugadores en alineaciones pasadas.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    backfill()
