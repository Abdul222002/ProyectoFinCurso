"""
Scheduler — Cerebro del Ciclo Automático de Jornadas
Ejecuta tareas mientras el servidor está encendido:
  1. Lock:       Congela alineaciones al llegar start_date
  2. Fetch API:  Descarga stats de Sportmonks al llegar end_date
  3. Calcular:   Calcula puntos fantasy
  4. Distribuir:  Asigna puntos a equipos y ligas
  5. Avanzar:    Activa la siguiente jornada
"""

import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from sqlalchemy import func
from app.core.config import settings
logger = logging.getLogger("fantasy.scheduler")

scheduler = AsyncIOScheduler()
from app.routers.market import reconcile_locked_coins

# ──────────────────────────────────────────────────────────────────
# HELPER: Descargar stats de un partido desde Sportmonks API
# ──────────────────────────────────────────────────────────────────

def _fetch_gameweek_stats_from_api(gameweek, db):
    """
    Descarga las estadísticas de todos los partidos de la jornada
    desde la API de Sportmonks y los guarda como PlayerMatchStats.
    Solo procesa partidos que NO tengan stats registrados aún.
    """
    import requests
    from app.models.models import Match, Player, PlayerMatchStats
    from app.models.models import Position as DBPosition

    API_TOKEN = settings.SPORTMONKS_API_KEY
    if not API_TOKEN:
        logger.warning("⚠️ SPORTMONKS_API_KEY no configurada — no se pueden descargar stats automáticos.")
        return False

    matches = db.query(Match).filter(Match.gameweek_id == gameweek.id).all()
    if not matches:
        logger.info(f"  Sin partidos para la jornada {gameweek.number}")
        return False

    total_saved = 0

    for match in matches:
        # Comprobar si ya hay stats para este partido
        existing_count = db.query(PlayerMatchStats).filter(
            PlayerMatchStats.match_id == match.id
        ).count()
        if existing_count > 0:
            logger.info(f"  ✅ {match.home_team} vs {match.away_team}: ya tiene {existing_count} registros, saltando.")
            continue

        # Descargar de la API
        url = f"https://api.sportmonks.com/v3/football/fixtures/{match.sportmonks_id}"
        params = {
            "api_token": API_TOKEN,
            "include": "lineups.details.type;participants;scores"
        }

        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code != 200:
                logger.error(f"  ❌ Error API {resp.status_code} para fixture {match.sportmonks_id}")
                continue
            fixture_data = resp.json().get('data', {})
        except Exception as e:
            logger.error(f"  ❌ Error al conectar con Sportmonks: {e}")
            continue

        lineups = fixture_data.get('lineups', [])
        participants = fixture_data.get('participants', [])

        home_team_api = next((p for p in participants if p.get('meta', {}).get('location') == 'home'), {})
        away_team_api = next((p for p in participants if p.get('meta', {}).get('location') == 'away'), {})

        home_score = match.home_score or 0
        away_score = match.away_score or 0

        # Mapeo de posiciones del API
        POSITION_MAP = {24: 'GK', 25: 'DEF', 26: 'DEF', 27: 'DEF', 28: 'MID', 29: 'MID', 30: 'MID', 31: 'FWD', 32: 'FWD', 33: 'FWD'}

        # Mapeo de developer_name → campo DB
        STAT_MAP = {
            'MINUTES_PLAYED': 'minutes_played', 'RATING': 'rating',
            'GOALS': 'goals', 'ASSISTS': 'assists', 'BIG_CHANCES_CREATED': 'chances_created',
            'SAVES': 'saves', 'GOALKEEPER_GOALS_CONCEDED': 'goals_conceded',
            'GOALS_CONCEDED': 'goals_conceded_team',
            'PENALTY_MISS': 'penalty_miss', 'PENALTY_SAVE': 'penalty_save',
            'PENALTY_WON': 'penalty_won', 'PENALTY_COMMITTED': 'penalty_committed',
            'YELLOWCARDS': 'yellow_cards', 'REDCARDS': 'red_cards',
            'SHOTS_ON_TARGET': 'shots_on_target', 'SUCCESSFUL_DRIBBLES': 'dribbles',
            'ACCURATE_CROSSES': 'crosses', 'BALL_RECOVERY': 'ball_recoveries',
            'CLEARANCES': 'clearances', 'TACKLES': 'tackles', 'INTERCEPTIONS': 'interceptions',
            'DISPOSSESSED': 'dispossessed', 'POSSESSION_LOST': 'possession_lost',
            'TURN_OVER': 'turnovers', 'DUELS_WON': 'duels_won',
            'ACCURATE_PASSES': 'accurate_passes', 'PASSES': 'total_passes', 'FOULS': 'fouls',
            'SHOTS_TOTAL': 'shots_total',
        }

        played_player_ids = set()

        for entry in lineups:
            sportmonks_pid = entry.get('player_id')
            type_id = entry.get('type_id')
            participant_id = entry.get('participant_id')
            pos_str = POSITION_MAP.get(type_id, 'FWD')

            # Extraer stats del lineup entry
            stats_dict = {}
            for detail in entry.get('details', []):
                dev_name = detail.get('type', {}).get('developer_name', '')
                val = detail.get('data', {}).get('value')
                if dev_name in STAT_MAP:
                    field = STAT_MAP[dev_name]
                    try:
                        stats_dict[field] = float(val) if field == 'rating' else int(val or 0)
                    except (ValueError, TypeError):
                        stats_dict[field] = 0

            minutes = stats_dict.get('minutes_played', 0)
            if minutes == 0:
                continue  # No jugó

            # Clean sheet
            is_home = participant_id == home_team_api.get('id')
            clean_sheet = False
            if pos_str in ('GK', 'DEF') and minutes >= 60:
                clean_sheet = (away_score == 0) if is_home else (home_score == 0)

            # Buscar jugador en la BD
            player = db.query(Player).filter(Player.sportmonks_id == sportmonks_pid).first()
            if not player:
                # Crear placeholder si no existe
                player_team = match.home_team if is_home else match.away_team
                pos_enum = getattr(DBPosition, pos_str, DBPosition.FWD)
                player = Player(
                    name=entry.get('player_name', 'Desconocido'),
                    sportmonks_id=sportmonks_pid,
                    age=25, position=pos_enum, nationality="Scotland",
                    overall_rating=70, potential=75,
                    current_team=player_team
                )
                db.add(player)
                db.flush()

            played_player_ids.add(player.id)

            pms = PlayerMatchStats(
                player_id=player.id, match_id=match.id,
                minutes_played=minutes,
                rating=stats_dict.get('rating', 0.0),
                goals=stats_dict.get('goals', 0),
                assists=stats_dict.get('assists', 0),
                chances_created=stats_dict.get('chances_created', 0),
                clean_sheet=clean_sheet,
                goals_conceded=stats_dict.get('goals_conceded', 0),
                goals_conceded_team=stats_dict.get('goals_conceded_team', 0),
                saves=stats_dict.get('saves', 0),
                clearances=stats_dict.get('clearances', 0),
                yellow_cards=stats_dict.get('yellow_cards', 0),
                red_cards=stats_dict.get('red_cards', 0),
                shots_on_target=stats_dict.get('shots_on_target', 0),
                dribbles=stats_dict.get('dribbles', 0),
                crosses=stats_dict.get('crosses', 0),
                ball_recoveries=stats_dict.get('ball_recoveries', 0),
                dispossessed=stats_dict.get('dispossessed', 0),
                possession_lost=stats_dict.get('possession_lost', 0),
                turnovers=stats_dict.get('turnovers', 0),
                total_losses=(stats_dict.get('dispossessed', 0) + stats_dict.get('possession_lost', 0) + stats_dict.get('turnovers', 0)),
                shots_total=stats_dict.get('shots_total', 0),
                accurate_passes=stats_dict.get('accurate_passes', 0),
                total_passes=stats_dict.get('total_passes', 0),
                tackles=stats_dict.get('tackles', 0),
                interceptions=stats_dict.get('interceptions', 0),
                duels_won=stats_dict.get('duels_won', 0),
                fouls=stats_dict.get('fouls', 0),
                penalty_miss=stats_dict.get('penalty_miss', 0),
                penalty_save=stats_dict.get('penalty_save', 0),
                penalty_won=stats_dict.get('penalty_won', 0),
                penalty_committed=stats_dict.get('penalty_committed', 0),
                fantasy_points=0  # Se calculará después
            )
            db.add(pms)
            total_saved += 1

        # Crear registros 0 para jugadores que no jugaron
        for team_name in [match.home_team, match.away_team]:
            team_players = db.query(Player).filter(
                Player.current_team == team_name,
                Player.is_legend == False
            ).all()
            for p in team_players:
                if p.id not in played_player_ids:
                    pms = PlayerMatchStats(
                        player_id=p.id, match_id=match.id,
                        minutes_played=0, fantasy_points=0
                    )
                    db.add(pms)
                    total_saved += 1

        db.commit()
        logger.info(f"  📥 {match.home_team} vs {match.away_team}: stats descargados de Sportmonks")

    logger.info(f"📡 Jornada {gameweek.number}: {total_saved} registros de stats obtenidos de la API.")
    return True


# ──────────────────────────────────────────────────────────────────
# PRINCIPAL: Ciclo de vida de la jornada
# ──────────────────────────────────────────────────────────────────

def gameweek_lifecycle_tick():
    """
    Se ejecuta cada minuto. Revisa el estado de la jornada activa
    y ejecuta la acción correspondiente según la hora actual.
    """
    from app.core.database import SessionLocal
    from app.models.models import Gameweek, GameweekLineup, Team, UserCard, GameweekLineupPlayer

    db = SessionLocal()
    try:
        ahora = datetime.utcnow()

        active_gw = db.query(Gameweek).filter_by(is_active=True).first()
        if not active_gw:
            return  # No hay jornada activa, nada que hacer

        # ─── FASE 1: LOCK ────────────────────────────────────────
        if ahora >= active_gw.start_date:
            teams = db.query(Team).all()
            locked = 0
            for team in teams:
                existing = db.query(GameweekLineup).filter_by(
                    team_id=team.id,
                    gameweek_id=active_gw.id
                ).first()
                if existing:
                    continue

                active_cards = db.query(UserCard).filter_by(
                    team_id=team.id,
                    is_in_lineup=True
                ).all()
                gw_lineup = GameweekLineup(
                    team_id=team.id,
                    gameweek_id=active_gw.id,
                    active_formation=team.active_formation or "4-3-3"
                )
                # RELACIONAL:
                gw_lineup.players = [GameweekLineupPlayer(card_id=c.id) for c in active_cards]
                db.add(gw_lineup)
                locked += 1

            if locked > 0:
                db.commit()
                logger.info(f"🔒 Jornada {active_gw.number}: {locked} alineaciones congeladas automáticamente.")

        # ─── FASE 2: FETCH + CALCULAR + DISTRIBUIR ────────────────
        if ahora >= active_gw.end_date and not active_gw.is_finished:
            from app.models.models import Match, PlayerMatchStats, Player, LeagueMember
            from app.services.calculator import calculator
            from sqlalchemy.exc import OperationalError

            try:
                # Bloqueo pesimista inmediato. Si otro proceso lo tiene, lanza excepción y salimos.
                locked_gw = db.query(Gameweek).filter_by(id=active_gw.id).with_for_update(nowait=True).first()
                if not locked_gw or locked_gw.is_finished:
                    return
            except OperationalError:
                logger.info(f"⏳ Jornada {active_gw.number} ya está siendo procesada por otro worker.")
                return

            # 2a. Descargar stats de Sportmonks si no los hay
            logger.info(f"📡 Jornada {active_gw.number}: descargando stats de la API...")
            _fetch_gameweek_stats_from_api(active_gw, db)

            # 2b. Calcular fantasy_points individuales
            matches = db.query(Match).filter(Match.gameweek_id == active_gw.id).all()

            for match in matches:
                stats_list = db.query(PlayerMatchStats).filter(
                    PlayerMatchStats.match_id == match.id
                ).all()
                for stats in stats_list:
                    player = db.query(Player).filter(Player.id == stats.player_id).first()
                    if player:
                        stats.fantasy_points = calculator.calculate_total_points(stats, player.position)

            db.flush()

            # 2c. Diccionario rápido player_id → puntos (jugadores reales de Sportmonks)
            player_points = {}
            for match in matches:
                for stats in db.query(PlayerMatchStats).filter(
                    PlayerMatchStats.match_id == match.id
                ).all():
                    player_points[stats.player_id] = stats.fantasy_points or 0

            # 2d. Sumar puntos a cada equipo usando su 11 congelado
            from app.services.icon_scoring import calculate_icon_points
            teams = db.query(Team).all()
            for team in teams:
                gw_lineup = db.query(GameweekLineup).filter_by(
                    team_id=team.id,
                    gameweek_id=active_gw.id
                ).first()

                team_points = 0.0
                if gw_lineup:
                    for lp in gw_lineup.players:
                        card = lp.card
                        if not card:
                            continue
                        player = db.query(Player).filter(Player.id == card.player_id).first()
                        if not player:
                            continue

                        if player.is_legend:
                            # 🏆 ICONO: puntos calculados por el sistema de arquetipos
                            pts = calculate_icon_points(player)
                            logger.info(f"   🌟 {player.name} ({player.scoring_profile}): {pts} pts")
                        else:
                            # Jugador real: puntos de Sportmonks
                            pts = player_points.get(card.player_id, 0)

                        lp.points_earned = pts
                        team_points += pts
                    gw_lineup.points_earned = team_points

                # Recalcular total histórico (Idempotencia absoluta: suma de todas las jornadas finalizadas + la actual)
                past_points = db.query(func.sum(GameweekLineup.points_earned)).join(Gameweek).filter(
                    GameweekLineup.team_id == team.id,
                    Gameweek.is_finished == True
                ).scalar() or 0
                
                team.total_fantasy_points = past_points + team_points

                # Actualizar clasificación de la liga y recompensar con monedas (1 punto = 1,000,000 monedas)
                lm = db.query(LeagueMember).filter_by(
                    user_id=team.user_id,
                    league_id=team.league_id
                ).first()
                if lm:
                    lm.league_points = team.total_fantasy_points
                    # Recompensa económica de la jornada
                    coins_to_add = int(team_points * 100000)
                    lm.coins += coins_to_add
                    logger.info(f"   💰 Recompensa para {team.name}: {coins_to_add:,} monedas por {team_points} puntos.")

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


# ──────────────────────────────────────────────────────────────────
# OFERTAS DEL SISTEMA
# ──────────────────────────────────────────────────────────────────

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


def resolve_expired_auctions_tick():
    """
    Runs every 5 minutes. Resolves any expired market auctions
    that haven't been resolved yet (lazy resolution fallback).
    """
    from app.core.database import SessionLocal
    from app.models.models import MarketAuction

    db = SessionLocal()
    try:
        now = datetime.utcnow()
        expired_auctions = db.query(MarketAuction).filter(
            MarketAuction.is_active == True,
            MarketAuction.ends_at < now,
            MarketAuction.is_resolved == False
        ).all()

        resolved_count = 0
        for auction in expired_auctions:
            try:
                from app.routers.market import _resolve_auction
                _resolve_auction(auction, db)
                resolved_count += 1
            except Exception as e:
                logger.error(f"Error resolving auction {auction.id}: {e}")
                db.rollback()

        if resolved_count > 0:
            logger.info(f"🏁 {resolved_count} subastas expiradas resueltas automáticamente")

    except Exception as e:
        logger.error(f"Error en resolución de subastas: {e}")
    finally:
        db.close()


def economy_reconciliation_tick():
    """
    Ejecuta la reconciliación de locked_coins para todas las ligas
    cada hora, para corregir posibles desajustes de integridad.
    """
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        logger.info("⚖️ Iniciando reconciliación económica global de locked_coins...")
        from app.routers.market import reconcile_locked_coins
        fixed = reconcile_locked_coins(db)
        if fixed > 0:
            logger.info(f"✅ Reconciliación completada: {fixed} desajustes corregidos.")
        else:
            logger.info("✅ Reconciliación completada: integridad OK.")
    except Exception as e:
        logger.error(f"❌ Error en reconciliación económica: {e}")
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────────
# SUBASTAS AUTOMÁTICAS
# ──────────────────────────────────────────────────────────────────

def create_missing_auctions_tick():
    """
    Runs every 5 minutes. For every league that has at least one member
    but does NOT have an active auction, creates one automatically.
    Also resolves any expired-but-unresolved auctions first so the
    creation logic finds a clean state.
    """
    from app.core.database import SessionLocal
    from app.models.models import MarketAuction, League, LeagueMember

    db = SessionLocal()
    try:
        now = datetime.utcnow()

        # 1. Resolve expired auctions first (same logic as resolve_expired_auctions_tick)
        expired_auctions = db.query(MarketAuction).filter(
            MarketAuction.is_active == True,
            MarketAuction.ends_at < now,
            MarketAuction.is_resolved == False
        ).all()

        for auction in expired_auctions:
            try:
                from app.routers.market import _resolve_auction
                _resolve_auction(auction, db)
                logger.info(f"🏁 Subasta {auction.id} (liga {auction.league_id}) resuelta automáticamente")
            except Exception as e:
                logger.error(f"Error resolviendo subasta {auction.id}: {e}")
                db.rollback()

        # 2. Get all league IDs that have at least one member
        league_ids = [
            lid for (lid,) in
            db.query(LeagueMember.league_id).distinct().all()
        ]

        created_count = 0
        for league_id in league_ids:
            # Check if there's already an active auction
            active = db.query(MarketAuction).filter(
                MarketAuction.league_id == league_id,
                MarketAuction.is_active == True
            ).first()

            if not active:
                try:
                    from app.routers.market import _create_new_auction
                    _create_new_auction(league_id, db)
                    created_count += 1
                except Exception as e:
                    logger.error(f"Error creando subasta para liga {league_id}: {e}")
                    db.rollback()

        if created_count > 0:
            logger.info(f"🆕 {created_count} subastas creadas automáticamente para ligas sin subasta activa")

    except Exception as e:
        db.rollback()
        logger.error(f"Error en create_missing_auctions_tick: {e}")
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────────
# START / STOP
# ──────────────────────────────────────────────────────────────────

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
    scheduler.add_job(
        economy_reconciliation_tick,
        trigger=IntervalTrigger(hours=1),
        id="economy_reconciliation",
        replace_existing=True
    )
    scheduler.add_job(
        resolve_expired_auctions_tick,
        trigger=IntervalTrigger(minutes=5),
        id="resolve_expired_auctions",
        replace_existing=True
    )
    scheduler.add_job(
        create_missing_auctions_tick,
        trigger=IntervalTrigger(minutes=5),
        id="create_missing_auctions",
        replace_existing=True
    )
    scheduler.start()
    print("✅ Scheduler iniciado: jornadas (1min) + ofertas (1h) + reconciliación (1h) + subastas (5min) + auto-crear subastas (5min)", flush=True)

    # Ejecución inmediata al arrancar (catch-up)
    try:
        print("🚀 Ejecutando tareas de mantenimiento inicial (catch-up)...", flush=True)
        gameweek_lifecycle_tick()
        generate_system_offers_tick()
        economy_reconciliation_tick()
        resolve_expired_auctions_tick()
        create_missing_auctions_tick()
        print("✅ Tareas iniciales completadas.", flush=True)
    except Exception as e:
        logger.error(f"❌ Error en tareas iniciales del scheduler: {e}")


def stop_scheduler():
    scheduler.shutdown()

