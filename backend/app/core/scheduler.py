"""
Scheduler — Cerebro del Ciclo Automático de Jornadas
Ejecuta 3 tareas cada minuto mientras el servidor está encendido:
  1. Lock:     Congela alineaciones al llegar start_date
  2. Calcular: Calcula puntos al llegar end_date
  3. Avanzar:  Activa la siguiente jornada tras finalizar la actual
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

logger = logging.getLogger("fantasy.scheduler")

scheduler = AsyncIOScheduler()


def gameweek_lifecycle_tick():
    """
    Se ejecuta cada minuto. Revisa el estado de la jornada activa
    y ejecuta la acción correspondiente según la hora actual.
    """
    from app.core.database import SessionLocal
    from app.models.models import Gameweek, GameweekLineup, Team, UserCard

    db = SessionLocal()
    try:
        ahora = datetime.utcnow()

        active_gw = db.query(Gameweek).filter_by(is_active=True).first()
        if not active_gw:
            return  # No hay jornada activa, nada que hacer

        # ─── FASE 1: LOCK ────────────────────────────────────────
        # Si ya pasó start_date, congelar las alineaciones que aún no se hayan guardado
        if ahora >= active_gw.start_date:
            teams = db.query(Team).all()
            locked = 0
            for team in teams:
                existing = db.query(GameweekLineup).filter_by(
                    team_id=team.id,
                    gameweek_id=active_gw.id
                ).first()
                if existing:
                    continue  # Ya congelado (guardado por el usuario o por un tick anterior)

                active_cards = db.query(UserCard).filter_by(
                    team_id=team.id,
                    is_in_lineup=True
                ).all()
                player_ids_str = ",".join(str(c.id) for c in active_cards)

                gw_lineup = GameweekLineup(
                    team_id=team.id,
                    gameweek_id=active_gw.id,
                    player_ids=player_ids_str,
                    active_formation=team.active_formation or "4-3-3"
                )
                db.add(gw_lineup)
                locked += 1

            if locked > 0:
                db.commit()
                logger.info(f"🔒 Jornada {active_gw.number}: {locked} alineaciones congeladas automáticamente.")

        # ─── FASE 2: CALCULAR PUNTOS ─────────────────────────────
        # Si ya pasó end_date Y la jornada no está marcada como finalizada
        if ahora >= active_gw.end_date and not active_gw.is_finished:
            from app.models.models import Match, PlayerMatchStats, Player, LeagueMember
            from app.services.calculator import calculator

            matches = db.query(Match).filter(Match.gameweek_id == active_gw.id).all()

            # Primero: calcular fantasy_points individuales de cada jugador
            for match in matches:
                stats_list = db.query(PlayerMatchStats).filter(
                    PlayerMatchStats.match_id == match.id
                ).all()
                for stats in stats_list:
                    player = db.query(Player).filter(Player.id == stats.player_id).first()
                    if player:
                        stats.fantasy_points = calculator.calculate_total_points(stats, player.position)

            db.flush()

            # Segundo: diccionario rápido player_id → puntos
            player_points = {}
            for match in matches:
                for stats in db.query(PlayerMatchStats).filter(
                    PlayerMatchStats.match_id == match.id
                ).all():
                    player_points[stats.player_id] = stats.fantasy_points or 0

            # Tercero: sumar puntos a cada equipo usando su 11 congelado
            teams = db.query(Team).all()
            for team in teams:
                gw_lineup = db.query(GameweekLineup).filter_by(
                    team_id=team.id,
                    gameweek_id=active_gw.id
                ).first()

                team_points = 0.0
                if gw_lineup:
                    card_ids = [int(pid) for pid in gw_lineup.player_ids.split(",") if pid.strip()]
                    for cid in card_ids:
                        card = db.query(UserCard).filter(UserCard.id == cid).first()
                        if card and card.player_id in player_points:
                            team_points += player_points[card.player_id]
                    gw_lineup.points_earned = team_points

                # Acumular al total histórico del equipo
                team.total_fantasy_points = (team.total_fantasy_points or 0) + team_points

                # Actualizar puntos en la clasificación de la liga
                lm = db.query(LeagueMember).filter_by(
                    user_id=team.user_id,
                    league_id=team.league_id
                ).first()
                if lm:
                    lm.league_points = (lm.league_points or 0) + team_points

            # Marcar jornada como finalizada
            active_gw.is_finished = True
            active_gw.is_active = False
            db.commit()
            logger.info(f"📊 Jornada {active_gw.number}: puntos calculados y jornada finalizada.")

            # ─── FASE 3: AVANZAR JORNADA ──────────────────────────
            next_gw = db.query(Gameweek).filter(
                Gameweek.number == active_gw.number + 1
            ).first()

            if next_gw:
                next_gw.is_active = True
                db.commit()
                logger.info(f"➡️  Jornada {next_gw.number} activada. Los usuarios pueden preparar su equipo.")
            else:
                logger.info("🏁 No hay más jornadas. ¡La temporada ha terminado!")

    except Exception as e:
        db.rollback()
        logger.error(f"Error en el ciclo de jornada: {e}")
    finally:
        db.close()


def generate_system_offers_tick():
    """
    Runs every hour. Generates system buy offers for
    market listings older than 24h with no buyer.
    Also expires old offers that have passed their deadline.
    """
    from app.core.database import SessionLocal
    from app.models.models import MarketListing, SystemOffer
    import random
    from datetime import timedelta

    db = SessionLocal()
    try:
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=24)

        # 1. Expire old system offers
        expired = db.query(SystemOffer).filter(
            SystemOffer.is_accepted == False,
            SystemOffer.is_expired == False,
            SystemOffer.expires_at < now
        ).all()
        for o in expired:
            o.is_expired = True
        if expired:
            db.commit()
            logger.info(f"⏰ {len(expired)} ofertas del sistema expiradas")

        # 2. Generate new offers for listings > 24h without an active offer
        listings = db.query(MarketListing).filter(
            MarketListing.is_active == True,
            MarketListing.listed_at < cutoff
        ).all()

        created = 0
        for listing in listings:
            existing = db.query(SystemOffer).filter(
                SystemOffer.listing_id == listing.id,
                SystemOffer.is_expired == False,
                SystemOffer.is_accepted == False
            ).first()
            if existing:
                continue

            discount = random.uniform(0.80, 0.95)
            offer_price = int(listing.asking_price * discount)

            offer = SystemOffer(
                listing_id=listing.id,
                card_id=listing.card_id,
                user_id=listing.seller_id,
                league_id=listing.league_id,
                offer_price=offer_price,
                offered_at=now,
                expires_at=now + timedelta(hours=48)
            )
            db.add(offer)
            created += 1

        if created:
            db.commit()
            logger.info(f"🤖 {created} ofertas del sistema generadas automáticamente")

    except Exception as e:
        db.rollback()
        logger.error(f"Error generando ofertas: {e}")
    finally:
        db.close()


def start_scheduler():
    """Inicia el scheduler con los trabajos principales"""
    scheduler.add_job(
        gameweek_lifecycle_tick,
        trigger=IntervalTrigger(minutes=1),
        id="gameweek_lifecycle",
        replace_existing=True
    )
    scheduler.add_job(
        generate_system_offers_tick,
        trigger=IntervalTrigger(hours=1),
        id="system_offers",
        replace_existing=True
    )
    scheduler.start()
    logger.info("✅ Scheduler iniciado: jornadas (1min) + ofertas (1h)")


def stop_scheduler():
    scheduler.shutdown()

