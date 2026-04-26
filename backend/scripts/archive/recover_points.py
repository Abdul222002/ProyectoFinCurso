"""
Script de recuperación para calcular y distribuir los puntos de la jornada 33.
Se ejecuta una sola vez cuando el scheduler no pudo hacerlo automáticamente.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.models import Gameweek, Match, PlayerMatchStats, Player, Team, GameweekLineup, LeagueMember
from app.services.calculator import calculator
from app.services.icon_scoring import calculate_icon_points
from app.core.scheduler import _fetch_gameweek_stats_from_api

def recover_gameweek_points(gw_number: int):
    db = SessionLocal()
    try:
        gw = db.query(Gameweek).filter(Gameweek.number == gw_number).first()
        if not gw:
            print(f"❌ Jornada {gw_number} no encontrada.")
            return

        print(f"🔄 Recuperando puntos para Jornada {gw.number} (id={gw.id})...")
        print(f"   Estado actual: is_finished={gw.is_finished}, is_active={gw.is_active}")

        # 1. Descargar stats de la API si no existen
        matches = db.query(Match).filter(Match.gameweek_id == gw.id).all()
        stats_count = db.query(PlayerMatchStats).filter(
            PlayerMatchStats.match_id.in_([m.id for m in matches])
        ).count()

        print(f"   Partidos en jornada: {len(matches)}")
        print(f"   Stats ya registrados: {stats_count}")

        if stats_count == 0:
            print("   📡 Descargando stats desde Sportmonks API...")
            _fetch_gameweek_stats_from_api(gw, db)
            stats_count = db.query(PlayerMatchStats).filter(
                PlayerMatchStats.match_id.in_([m.id for m in matches])
            ).count()
            print(f"   ✅ Stats descargados: {stats_count} registros")
        else:
            print(f"   ✅ Stats ya existentes, recalculando puntos fantasy...")

        # 2. Calcular/recalcular fantasy_points para cada stat
        for match in matches:
            stats_list = db.query(PlayerMatchStats).filter(
                PlayerMatchStats.match_id == match.id
            ).all()
            for stats in stats_list:
                player = db.query(Player).filter(Player.id == stats.player_id).first()
                if player:
                    pts = calculator.calculate_total_points(stats, player.position)
                    stats.fantasy_points = pts

        db.flush()
        print("   ✅ fantasy_points calculados para todos los jugadores.")

        # 3. Construir diccionario player_id → puntos
        player_points = {}
        for match in matches:
            for stats in db.query(PlayerMatchStats).filter(
                PlayerMatchStats.match_id == match.id
            ).all():
                player_points[stats.player_id] = stats.fantasy_points or 0

        total_distributed = 0
        teams_updated = 0

        # 4. Distribuir puntos a equipos con alineación bloqueada
        teams = db.query(Team).all()
        for team in teams:
            gw_lineup = db.query(GameweekLineup).filter_by(
                team_id=team.id,
                gameweek_id=gw.id
            ).first()

            if not gw_lineup:
                print(f"   ⚠️ Equipo '{team.name}' no tiene alineación bloqueada para GW{gw.number}")
                continue

            # Evitar doble distribución: si ya tiene puntos asignados en este lineup, saltar
            if gw_lineup.points_earned and gw_lineup.points_earned > 0:
                print(f"   ⚠️ Equipo '{team.name}' ya tiene {gw_lineup.points_earned} pts en GW{gw.number}, saltando.")
                continue

            team_points = 0.0
            for lp in gw_lineup.players:
                card = lp.card
                if not card:
                    continue
                player = db.query(Player).filter(Player.id == card.player_id).first()
                if not player:
                    continue

                if player.is_legend:
                    pts = calculate_icon_points(player)
                else:
                    pts = player_points.get(card.player_id, 0)

                team_points += pts

            gw_lineup.points_earned = team_points
            team.total_fantasy_points = (team.total_fantasy_points or 0) + team_points

            lm = db.query(LeagueMember).filter_by(
                user_id=team.user_id,
                league_id=team.league_id
            ).first()
            if lm:
                lm.league_points = (lm.league_points or 0) + team_points

            total_distributed += team_points
            teams_updated += 1
            print(f"   📊 {team.name}: +{team_points:.1f} pts")

        # 5. Asegurar que la jornada está marcada como finalizada
        gw.is_finished = True
        gw.is_active = False
        db.commit()

        print(f"\n✅ Recuperación completada:")
        print(f"   Equipos actualizados: {teams_updated}")
        print(f"   Total puntos distribuidos: {total_distributed:.1f}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error durante la recuperación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    gw_num = int(sys.argv[1]) if len(sys.argv) > 1 else 33
    recover_gameweek_points(gw_num)
