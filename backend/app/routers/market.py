"""
Router del Mercado de Subastas (Auction Market)
Sistema:
1. Subastas de 24h por liga.
2. 12 jugadores aleatorios (NO LEGENDS) cada día.
3. Usuarios pujan con monedas de la liga.
4. Al acabar, el ganador se lleva la carta.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.database import get_db
from app.models.models import (
    User, Player, UserCard, LeagueMember, League, Team,
    MarketAuction, AuctionSlot, AuctionBid,
    MarketListing, ListingBid, SystemOffer
)
from app.schemas.market import (
    AuctionResponse, AuctionSlotResponse, BidRequest, 
    BidResponse, SellResponse,
    ListCardRequest, ListingResponse, SystemOfferResponse
)
from app.routers.auth import get_current_user
from pydantic import BaseModel

class TrendingPlayer(BaseModel):
    id: int
    name: str
    overall_rating: int
    current_price: float
    image_url: Optional[str]
    base_rarity: str
    acquisitions_count: int

router = APIRouter()

AUCTION_DURATION_HOURS = 24
SLOTS_PER_AUCTION = 12

@router.get("/global-trends", response_model=List[TrendingPlayer])
async def get_global_trends(db: Session = Depends(get_db)):
    """
    Calcula los jugadores más fichados (en todas las ligas) en los últimos 7 días.
    """
    last_week = datetime.utcnow() - timedelta(days=7)
    
    # Consulta: Contar adquisiciones por player_id en la última semana
    # Excluimos leyendas del conteo para que no monopolicen siempre la tendencia
    trending_query = db.query(
        UserCard.player_id, 
        func.count(UserCard.id).label('count')
    ).join(Player).filter(
        UserCard.acquired_at >= last_week,
        Player.is_legend == False
    ).group_by(
        UserCard.player_id
    ).order_by(
        func.count(UserCard.id).desc()
    ).limit(5).all()
    
    results = []
    for player_id, count in trending_query:
        player = db.query(Player).filter(Player.id == player_id).first()
        if player:
            results.append(TrendingPlayer(
                id=player.id,
                name=player.name,
                overall_rating=player.overall_rating,
                current_price=player.current_price,
                image_url=player.image_url,
                base_rarity=player.base_rarity.value if hasattr(player.base_rarity, 'value') else str(player.base_rarity),
                acquisitions_count=count
            ))
            
    # Si no hay datos (liga vacía o nueva), devolvemos los 5 mejores jugadores por OVR como fallback
    if not results:
        top_players = db.query(Player).filter(Player.is_legend == False).order_by(Player.overall_rating.desc()).limit(5).all()
        for p in top_players:
            results.append(TrendingPlayer(
                id=p.id,
                name=p.name,
                overall_rating=p.overall_rating,
                current_price=p.current_price,
                image_url=p.image_url,
                base_rarity=p.base_rarity.value if hasattr(p.base_rarity, 'value') else str(p.base_rarity),
                acquisitions_count=0
            ))
            
    return results


def reconcile_locked_coins(db: Session, league_id: int = None):
    """
    Recalcula locked_coins para todos los miembros de liga comparando
    contra las pujas activas reales en subastas vigentes.
    Corrige silenciosamente cualquier desajuste (prevención de bugs históricos).
    """
    query = db.query(LeagueMember)
    if league_id:
        query = query.filter(LeagueMember.league_id == league_id)
    
    members = query.all()
    fixed = 0
    
    for member in members:
        # Pujas en subastas ACTIVAS + pujas en ventas entre usuarios ACTIVAS
        auction_locked = db.query(func.coalesce(func.sum(AuctionBid.amount), 0)).join(
            AuctionSlot, AuctionSlot.id == AuctionBid.slot_id
        ).join(
            MarketAuction, MarketAuction.id == AuctionSlot.auction_id
        ).filter(
            AuctionBid.user_id == member.user_id,
            MarketAuction.league_id == member.league_id,
            MarketAuction.is_active == True
        ).scalar() or 0

        listing_locked = db.query(func.coalesce(func.sum(ListingBid.amount), 0)).join(
            MarketListing, MarketListing.id == ListingBid.listing_id
        ).filter(
            ListingBid.user_id == member.user_id,
            MarketListing.league_id == member.league_id,
            MarketListing.is_active == True
        ).scalar() or 0

        real_locked = auction_locked + listing_locked
        
        if member.locked_coins != real_locked:
            # logs básicos para auditoría en el contenedor
            print(f"[reconcile] user {member.user_id} liga {member.league_id}: {member.locked_coins} -> {real_locked}")
            member.locked_coins = real_locked
            fixed += 1
    
    if fixed > 0:
        db.commit()
    
    return fixed


def reconcile_member_locked_coins(db: Session, member: LeagueMember):
    """
    Recalcula los locked_coins de UN miembro específico basándose en sus pujas reales.
    Usa esto después de cualquier operación de puja para garantizar consistencia.
    """
    from app.models.models import AuctionBid, AuctionSlot, MarketAuction, ListingBid, MarketListing

    auction_locked = db.query(func.coalesce(func.sum(AuctionBid.amount), 0)).join(
        AuctionSlot, AuctionSlot.id == AuctionBid.slot_id
    ).join(
        MarketAuction, MarketAuction.id == AuctionSlot.auction_id
    ).filter(
        AuctionBid.user_id == member.user_id,
        MarketAuction.league_id == member.league_id,
        MarketAuction.is_active == True
    ).scalar() or 0

    listing_locked = db.query(func.coalesce(func.sum(ListingBid.amount), 0)).join(
        MarketListing, MarketListing.id == ListingBid.listing_id
    ).filter(
        ListingBid.user_id == member.user_id,
        MarketListing.league_id == member.league_id,
        MarketListing.is_active == True
    ).scalar() or 0

    member.locked_coins = auction_locked + listing_locked


def _cleanup_listing_related_offers(db: Session, listing: MarketListing):
    """
    Limpieza total al cerrar un listado (venta o cancelación):
    1. Devuelve las monedas bloqueadas a todos los pujadores.
    2. Expira todas las ofertas del sistema asociadas.
    """
    from app.models.models import ListingBid, LeagueMember, SystemOffer
    
    # 1. Reembolsar pujas de usuarios
    for bid in db.query(ListingBid).filter(ListingBid.listing_id == listing.id).all():
        mem = db.query(LeagueMember).filter(
            LeagueMember.league_id == listing.league_id,
            LeagueMember.user_id == bid.user_id
        ).first()
        if mem:
            # Evitar negativos por si acaso
            mem.locked_coins = max(0, mem.locked_coins - bid.amount)
        db.delete(bid)
        
    # 2. FIX: Expirar ofertas del sistema buscando por listing_id, no por card_id
    db.query(SystemOffer).filter(
        SystemOffer.listing_id == listing.id,
        SystemOffer.is_accepted == False,
        SystemOffer.is_expired == False
    ).update({"is_expired": True}, synchronize_session=False)


def _resolve_auction(auction: MarketAuction, db: Session):
    """
    Cierra una subasta ciega:
    - Determina el ganador de cada slot (mayor puja en AuctionBid).
    - Descuenta monedas al ganador, libera retención a todos los perdedores.
    - Crea la carta del ganador.
    - Crea notificaciones de victoria/derrota.
    """
    # 1. Bloqueo pesimista para evitar resoluciones concurrentes
    locked_auction = db.query(MarketAuction).filter(
        MarketAuction.id == auction.id
    ).with_for_update().first()

    if not locked_auction or locked_auction.is_resolved:
        return

    from app.models.models import Notification

    for slot in locked_auction.slots:
        # Obtener todas las pujas del slot ordenadas de mayor a menor
        all_bids = db.query(AuctionBid).filter(
            AuctionBid.slot_id == slot.id
        ).order_by(AuctionBid.amount.desc()).all()

        if not all_bids:
            continue  # Nadie pujó por este jugador

        winning_bid = all_bids[0]
        losing_bids = all_bids[1:]

        winner_member = db.query(LeagueMember).filter(
            LeagueMember.league_id == locked_auction.league_id,
            LeagueMember.user_id == winning_bid.user_id
        ).first()

        if winner_member:
            # Descontar definitivamente al ganador
            winner_member.locked_coins -= winning_bid.amount
            winner_member.coins -= winning_bid.amount

        # Crear carta para el ganador
        player = slot.player
        
        winner_team = db.query(Team).filter(
            Team.user_id == winning_bid.user_id,
            Team.league_id == locked_auction.league_id
        ).first()

        # SEGURIDAD: Nunca crear cartas sin equipo — crear equipo fallback si no existe
        if not winner_team:
            print(f"[market] WARNING: No se encontró equipo para user {winning_bid.user_id} en liga {locked_auction.league_id}. Creando equipo fallback.")
            winner_team = Team(
                user_id=winning_bid.user_id,
                league_id=locked_auction.league_id,
                name=f"Equipo {winning_bid.user_id}"
            )
            db.add(winner_team)
            db.flush()

        card = UserCard(
            user_id=winning_bid.user_id,
            player_id=slot.player_id,
            league_id=locked_auction.league_id,
            team_id=winner_team.id,
            current_overall=player.overall_rating,
            is_tradeable=True,
            is_in_lineup=False
        )
        db.add(card)

        # Notificación al ganador
        db.add(Notification(
            user_id=winning_bid.user_id,
            league_id=locked_auction.league_id,
            type="auction_won",
            title="¡Subasta ganada! 🏆",
            message=f"Has ganado la puja por {player.name} con {winning_bid.amount:,} monedas. ¡La carta ya está en tu plantilla!"
        ))

        # Liberar retención y notificar a los perdedores
        for losing_bid in losing_bids:
            loser_member = db.query(LeagueMember).filter(
                LeagueMember.league_id == locked_auction.league_id,
                LeagueMember.user_id == losing_bid.user_id
            ).first()
            if loser_member:
                loser_member.locked_coins = max(0, loser_member.locked_coins - losing_bid.amount)

            db.add(Notification(
                user_id=losing_bid.user_id,
                league_id=locked_auction.league_id,
                type="auction_lost",
                title="Subasta perdida",
                message=f"No has ganado la puja por {player.name}. Tus monedas han sido devueltas."
            ))

    locked_auction.is_active = False
    locked_auction.is_resolved = True
    db.commit()


def _create_new_auction(league_id: int, db: Session) -> MarketAuction:
    """Genera una nueva subasta con 12 jugadores aleatorios (NO LEGENDS)"""
    
    now = datetime.utcnow()
    
    # Intentar mantener el ciclo diario original
    last_auction = db.query(MarketAuction).filter(
        MarketAuction.league_id == league_id
    ).order_by(MarketAuction.ends_at.desc()).first()
    
    if last_auction and last_auction.ends_at > (now - timedelta(days=3)):
        # Encadenar en bloques de 24h hasta que estemos en el futuro
        next_ends_at = last_auction.ends_at
        while next_ends_at <= now:
            next_ends_at += timedelta(hours=AUCTION_DURATION_HOURS)
        ends_at = next_ends_at
    else:
        # Si no hay previa o es muy antigua, resetear a 24h desde ahora
        ends_at = now + timedelta(hours=AUCTION_DURATION_HOURS)
    
    auction = MarketAuction(
        league_id=league_id,
        started_at=now,
        ends_at=ends_at,
        is_active=True
    )
    db.add(auction)
    db.flush() # ID necesario
    
    # 2. Seleccionar 12 jugadores aleatorios (NO LEGENDS) que NO estén ya en la liga
    # Subquery para IDs de jugadores ya poseídos
    owned_player_ids = db.query(UserCard.player_id).filter(UserCard.league_id == league_id).all()
    owned_player_ids = [r[0] for r in owned_player_ids]

    players = db.query(Player).filter(
        Player.is_legend == False,
        ~Player.id.in_(owned_player_ids)
    ).order_by(func.rand()).limit(SLOTS_PER_AUCTION).all()
    
    # 3. Crear los slots
    for p in players:
        # Precio base = valor de mercado actual
        base_price = int(p.current_price)
        
        slot = AuctionSlot(
            auction_id=auction.id,
            player_id=p.id,
            base_price=base_price,
            current_bid=0,
            highest_bidder_id=None
        )
        db.add(slot)
        
    db.commit()
    return auction


@router.get("/{league_id}/auction", response_model=AuctionResponse)
async def get_auction(
    league_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene la subasta activa de la liga.
    Si no existe o expiró, resuelve la anterior crea una nueva.
    """
    # Verificar pertenencia a la liga
    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")

    # Buscar subasta activa
    auction = db.query(MarketAuction).filter(
        MarketAuction.league_id == league_id,
        MarketAuction.is_active == True
    ).order_by(MarketAuction.created_at.desc() if hasattr(MarketAuction, 'created_at') else MarketAuction.started_at.desc()).first()
    
    # Verificar si expiró
    if auction and auction.ends_at < datetime.utcnow():
        _resolve_auction(auction, db)
        auction = None # Para crear una nueva
        
    if not auction:
        auction = _create_new_auction(league_id, db)
        
    # Construir respuesta (subasta ciega: no se expone quién va ganando ni cuánto)
    slots_resp = []
    for slot in auction.slots:
        # Número total de usuarios únicos que han pujado
        bid_count = db.query(func.count(func.distinct(AuctionBid.user_id))).filter(
            AuctionBid.slot_id == slot.id
        ).scalar() or 0

        # La puja propia del usuario (solo visible para él)
        my_bid = db.query(AuctionBid).filter(
            AuctionBid.slot_id == slot.id,
            AuctionBid.user_id == current_user.id
        ).order_by(AuctionBid.created_at.desc()).first()

        slots_resp.append(AuctionSlotResponse(
            id=slot.id,
            player_id=slot.player_id,
            player_name=slot.player.name,
            position=slot.player.position.value,
            overall_rating=slot.player.overall_rating,
            base_rarity=slot.player.base_rarity.value,
            image_url=slot.player.image_url,
            current_team=slot.player.current_team,
            nationality=slot.player.nationality,
            pace=slot.player.pace,
            shooting=slot.player.shooting,
            passing=slot.player.passing,
            dribbling=slot.player.dribbling,
            defending=slot.player.defending,
            physical=slot.player.physical,
            base_price=slot.base_price,
            bid_count=bid_count,
            user_has_bid=my_bid is not None,
            my_bid_amount=my_bid.amount if my_bid else None,
        ))

    return AuctionResponse(
        id=auction.id,
        league_id=auction.league_id,
        ends_at=auction.ends_at,
        is_active=auction.is_active,
        server_time=datetime.utcnow(),
        slots=slots_resp
    )


@router.post("/{league_id}/bid/{slot_id}", response_model=BidResponse)
async def place_bid(
    league_id: int,
    slot_id: int,
    bid_data: BidRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Subasta ciega: coloca o actualiza la puja secreta del usuario.
    - Nadie puede ver la puja de otro usuario — solo el recuento total.
    - El usuario puede subir o bajar su propia puja.
    - El dinero queda retenido hasta la resolución de la subasta.
    """
    amount = bid_data.amount

    # [↓ SEGURIDAD] Bloqueo pesimista para pujas en subasta
    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).with_for_update().first()
    if not member:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")

    slot = db.query(AuctionSlot).join(MarketAuction).filter(
        AuctionSlot.id == slot_id,
        MarketAuction.league_id == league_id,
        MarketAuction.is_active == True
    ).with_for_update().first()
    if not slot:
        raise HTTPException(status_code=404, detail="Subasta no encontrada o finalizada")

    if slot.auction.ends_at < datetime.utcnow():
        _resolve_auction(slot.auction, db)
        raise HTTPException(status_code=400, detail="La subasta ha finalizado")

    if amount < slot.base_price:
        raise HTTPException(
            status_code=400,
            detail=f"La puja mínima es {slot.base_price:,} monedas (precio base)"
        )

    # ¿Ya tiene una puja activa en este slot?
    existing_bid = db.query(AuctionBid).filter(
        AuctionBid.slot_id == slot_id,
        AuctionBid.user_id == current_user.id
    ).first()

    if existing_bid:
        # Ajustar la retención: liberar la anterior y retener la nueva
        delta = amount - existing_bid.amount  # Puede ser positivo (sube) o negativo (baja)
        free_coins = member.coins - member.locked_coins
        if delta > 0 and free_coins < delta:
            raise HTTPException(
                status_code=400,
                detail=f"Solo dispones de {free_coins:,} monedas libres adicionales"
            )
        member.locked_coins += delta
        existing_bid.amount = amount
        existing_bid.created_at = datetime.utcnow()  # Actualizar timestamp
        message = "Puja actualizada con éxito"
    else:
        # Nueva puja — verificar fondos disponibles
        free_coins = member.coins - member.locked_coins
        if free_coins < amount:
            raise HTTPException(
                status_code=400,
                detail=f"Solo dispones de {free_coins:,} monedas libres"
            )
        member.locked_coins += amount
        new_bid = AuctionBid(
            slot_id=slot.id,
            user_id=current_user.id,
            amount=amount
        )
        db.add(new_bid)
        message = "Puja realizada con éxito"

    db.commit()
    # [AUTOCURACIÓN] Recalcular siempre el total retenido para evitar desajustes
    reconcile_member_locked_coins(db, member)
    db.commit()
    db.refresh(member)

    return BidResponse(
        message=message,
        slot_id=slot.id,
        new_bid=amount,
        remaining_coins=member.coins - member.locked_coins
    )

@router.delete("/{league_id}/bid/{slot_id}")
async def withdraw_bid(
    league_id: int,
    slot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retirar la puja propia de una subasta ciega.
    Libera inmediatamente las monedas retenidas.
    """
    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).with_for_update().first()
    if not member:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")

    slot = db.query(AuctionSlot).join(MarketAuction).filter(
        AuctionSlot.id == slot_id,
        MarketAuction.league_id == league_id,
        MarketAuction.is_active == True
    ).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Subasta no encontrada o finalizada")

    if slot.auction.ends_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="La subasta ha finalizado")

    user_bid = db.query(AuctionBid).filter(
        AuctionBid.slot_id == slot_id,
        AuctionBid.user_id == current_user.id
    ).with_for_update().first()

    if not user_bid:
        raise HTTPException(status_code=400, detail="No tienes ninguna puja activa en este jugador")

    # Liberar retención y borrar la puja
    member.locked_coins = max(0, member.locked_coins - user_bid.amount)
    db.delete(user_bid)
    db.commit()
    # [AUTOCURACIÓN] Recalcular siempre el total retenido
    reconcile_member_locked_coins(db, member)
    db.commit()

    return {"message": "Puja retirada. Monedas liberadas.", "remaining_coins": member.coins - member.locked_coins}
def _delete_card_and_dependencies(db: Session, card: UserCard, exclude_offer_id: int = None):
    """
    Borra físicamente una carta y limpia todas sus dependencias obligatorias
    respetando la jerarquía de claves foráneas para evitar IntegrityErrors.
    Orden de borrado: Hijos (Offers) -> Padres intermedios (Listings) -> Padre raíz (Card)
    """
    from app.models.models import GameweekLineupPlayer, PackOpeningCard, MarketListing, SystemOffer
    
    # Dependencias directas de la carta sin hijos
    db.query(GameweekLineupPlayer).filter(GameweekLineupPlayer.card_id == card.id).delete(synchronize_session=False)
    db.query(PackOpeningCard).filter(PackOpeningCard.card_id == card.id).delete(synchronize_session=False)
    
    # 1º BORRAR HIJOS: Ofertas del sistema (Dependen de MarketListing y de UserCard)
    offer_query = db.query(SystemOffer).filter(SystemOffer.card_id == card.id)
    if exclude_offer_id:
        offer_query = offer_query.filter(SystemOffer.id != exclude_offer_id)
    offer_query.delete(synchronize_session=False)
    
    # 2º BORRAR PADRES INTERMEDIOS: Listados del mercado (Dependen de UserCard)
    db.query(MarketListing).filter(MarketListing.card_id == card.id).delete(synchronize_session=False)
    
    # 3º BORRAR PADRE RAÍZ: La carta
    db.delete(card)



@router.post("/{league_id}/sell/{card_id}", response_model=SellResponse)
async def sell_card_league(
    league_id: int,
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Vender una carta al sistema (descarta la carta y da monedas de liga).
    Precio = 85% del valor actual de mercado.
    """
    # [↓ SEGURIDAD] Bloqueo pesimista: evita vender la misma carta dos veces con doble-click
    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).with_for_update().first()
    
    if not member:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")
        
    # [↓ SEGURIDAD] Bloquear la carta también para prevenir venta concurrente
    card = db.query(UserCard).filter(
        UserCard.id == card_id,
        UserCard.user_id == current_user.id
    ).with_for_update().first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Carta no encontrada en tu inventario de esta liga")
        
    if card.league_id != league_id:
        if card.team and card.team.league_id == league_id:
            # Corregir league_id en memoria — el commit final lo persiste de forma atómica
            card.league_id = league_id
        else:
            raise HTTPException(status_code=404, detail="Carta no encontrada en tu inventario de esta liga")

    if not card.is_tradeable:
        raise HTTPException(status_code=400, detail="Esta carta no se puede vender (intransferible)")

    if card.is_in_lineup:
        raise HTTPException(status_code=400, detail="Retira la carta de la alineación antes de venderla")

    player = card.player
    sell_price = int(player.current_price * 0.85)

    # Sumar monedas de liga
    member.coins += sell_price

    # [↓ LÓGICA] Cancelar listado activo si existe antes de borrar la carta
    active_listing = db.query(MarketListing).filter(
        MarketListing.card_id == card.id, 
        MarketListing.is_active == True
    ).with_for_update().first()
    if active_listing:
        _cleanup_listing_related_offers(db, active_listing)
        active_listing.is_active = False
        active_listing.sold_at = datetime.utcnow()
    
    # Eliminar carta y dependencias
    _delete_card_and_dependencies(db, card)
    db.commit()

    return SellResponse(
        message=f"Has vendido a {player.name} por {sell_price:,} monedas",
        player_name=player.name,
        price_received=sell_price,
        remaining_coins=member.coins
    )


# ==========================================
# LISTADOS DE USUARIO (Venta entre jugadores)
# ==========================================

@router.post("/{league_id}/list/{card_id}")
async def list_card_for_sale(
    league_id: int,
    card_id: int,
    data: ListCardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Poner una carta a la venta en el mercado de la liga."""
    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")

    card = db.query(UserCard).filter(
        UserCard.id == card_id,
        UserCard.user_id == current_user.id
    ).with_for_update().first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Carta no encontrada")
        
    if card.league_id != league_id:
        if card.team and card.team.league_id == league_id:
            card.league_id = league_id
            # Se omite el commit intermedio; se guardará al final junto con el listado
        else:
            raise HTTPException(status_code=404, detail="Carta no encontrada")
    if not card.is_tradeable:
        raise HTTPException(status_code=400, detail="Esta carta no se puede vender")
    if card.is_in_lineup:
        raise HTTPException(status_code=400, detail="Quita la carta del 11 antes de venderla")

    # Check not already listed
    existing = db.query(MarketListing).filter(
        MarketListing.card_id == card_id,
        MarketListing.is_active == True
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Esta carta ya está en venta")

    # Min price = player value
    min_price = int(card.player.current_price)
    if data.asking_price < min_price:
        raise HTTPException(
            status_code=400,
            detail=f"Precio mínimo: {min_price:,} (valor del jugador)"
        )

    listing = MarketListing(
        card_id=card_id,
        seller_id=current_user.id,
        league_id=league_id,
        asking_price=data.asking_price
    )
    db.add(listing)
    db.commit()

    return {
        "message": f"{card.player.name} puesto a la venta por {data.asking_price:,}",
        "listing_id": listing.id,
        "player_name": card.player.name,
        "asking_price": data.asking_price
    }


@router.delete("/{league_id}/list/{listing_id}")
async def cancel_listing(
    league_id: int,
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancelar un listado de venta."""
    listing = db.query(MarketListing).filter(
        MarketListing.id == listing_id,
        MarketListing.seller_id == current_user.id,
        MarketListing.league_id == league_id,
        MarketListing.is_active == True
    ).with_for_update().first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listado no encontrado")

    _cleanup_listing_related_offers(db, listing)
    listing.is_active = False
    db.commit()
    return {"message": "Listado cancelado"}


@router.get("/{league_id}/listings")
async def get_listings(
    league_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener todos los listados activos de la liga."""
    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")

    listings = db.query(MarketListing).filter(
        MarketListing.league_id == league_id,
        MarketListing.is_active == True
    ).all()

    result = []
    for l in listings:
        player = l.card.player
        seller = l.seller
        bids = db.query(ListingBid).filter(ListingBid.listing_id == l.id).order_by(ListingBid.amount.desc()).all()
        max_bid = max((b.amount for b in bids), default=0)
        my_bid = next((b for b in bids if b.user_id == current_user.id), None)

        row = {
            "id": l.id,
            "card_id": l.card_id,
            "player_id": player.id,
            "player_name": player.name,
            "position": player.position.value,
            "overall_rating": player.overall_rating,
            "base_rarity": player.base_rarity.value,
            "image_url": player.image_url,
            "current_team": player.current_team,
            "nationality": player.nationality,
            "pace": player.pace,
            "shooting": player.shooting,
            "passing": player.passing,
            "dribbling": player.dribbling,
            "defending": player.defending,
            "physical": player.physical,
            "asking_price": l.asking_price,
            "seller_username": seller.username,
            "is_mine": l.seller_id == current_user.id,
            "listed_at": l.listed_at.isoformat(),
            "highest_bid": max_bid,
            "bid_count": len(bids),
            "my_bid_amount": my_bid.amount if my_bid else None,
            "my_bid_id": my_bid.id if my_bid else None,
            "bids": None,
        }
        if l.seller_id == current_user.id:
            row["bids"] = [
                {
                    "id": b.id,
                    "user_id": b.user_id,
                    "username": b.user.username,
                    "amount": b.amount,
                    "created_at": b.created_at.isoformat() if b.created_at else None,
                }
                for b in sorted(bids, key=lambda x: x.amount, reverse=True)
            ]
        result.append(row)

    return result


@router.post("/{league_id}/listing-bid/{listing_id}", response_model=BidResponse)
async def place_listing_bid(
    league_id: int,
    listing_id: int,
    bid_data: BidRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pujar por un jugador en venta entre usuarios de la liga.
    El vendedor elige a qué postor venderle desde sus listados.
    """
    amount = bid_data.amount
    # [↓ SEGURIDAD] Bloqueo pesimista para pujas en listados entre usuarios
    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).with_for_update().first()
    if not member:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")

    listing = db.query(MarketListing).filter(
        MarketListing.id == listing_id,
        MarketListing.league_id == league_id,
        MarketListing.is_active == True
    ).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listado no encontrado o cerrado")
    if listing.seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes pujar por tu propia venta")

    max_other = db.query(func.coalesce(func.max(ListingBid.amount), 0)).filter(
        ListingBid.listing_id == listing.id,
        ListingBid.user_id != current_user.id
    ).scalar() or 0

    existing = db.query(ListingBid).filter(
        ListingBid.listing_id == listing.id,
        ListingBid.user_id == current_user.id
    ).first()

    # En subastas (tanto diarias como P2P), permitimos al usuario 
    # bajar su propia puja siempre que supere el mínimo del vendedor
    # y la puja más alta de otros usuarios.
    min_required = max(listing.asking_price, max_other + 1)

    if amount < min_required:
        raise HTTPException(
            status_code=400,
            detail=f"La puja debe ser al menos {min_required:,} monedas"
        )

    if existing:
        delta = amount - existing.amount
        if (member.coins - member.locked_coins) < delta:
            raise HTTPException(
                status_code=400,
                detail=f"Solo dispones de {(member.coins - member.locked_coins):,} monedas libres"
            )
        member.locked_coins += delta
        existing.amount = amount
        slot_id = existing.id
    else:
        if (member.coins - member.locked_coins) < amount:
            raise HTTPException(
                status_code=400,
                detail=f"Solo dispones de {(member.coins - member.locked_coins):,} monedas libres"
            )
        member.locked_coins += amount
        nb = ListingBid(listing_id=listing.id, user_id=current_user.id, amount=amount)
        db.add(nb)
        db.flush()
        slot_id = nb.id

    db.commit()
    # [AUTOCURACIÓN] Recalcular siempre el total retenido
    reconcile_member_locked_coins(db, member)
    db.commit()

    return BidResponse(
        message="Puja registrada",
        slot_id=slot_id,
        new_bid=amount,
        remaining_coins=member.coins - member.locked_coins
    )


@router.delete("/{league_id}/listing-bid/{listing_id}")
async def withdraw_listing_bid(
    league_id: int,
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retirar la puja propia sobre un listado activo."""
    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).with_for_update().first()
    if not member:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")

    listing = db.query(MarketListing).filter(
        MarketListing.id == listing_id,
        MarketListing.league_id == league_id,
        MarketListing.is_active == True
    ).with_for_update().first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listado no encontrado o cerrado")

    bid = db.query(ListingBid).filter(
        ListingBid.listing_id == listing.id,
        ListingBid.user_id == current_user.id
    ).with_for_update().first()
    if not bid:
        raise HTTPException(status_code=400, detail="No tienes ninguna puja en este listado")

    member.locked_coins -= bid.amount
    db.delete(bid)
    db.commit()
    # [AUTOCURACIÓN] Recalcular siempre el total retenido
    reconcile_member_locked_coins(db, member)
    db.commit()

    return {
        "message": "Puja retirada",
        "remaining_coins": member.coins - member.locked_coins
    }


@router.post("/{league_id}/listing-accept/{listing_id}/{bid_id}")
async def accept_listing_bid(
    league_id: int,
    listing_id: int,
    bid_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """El vendedor acepta una puja concreta y transfiere la carta al comprador."""
    listing = db.query(MarketListing).filter(
        MarketListing.id == listing_id,
        MarketListing.league_id == league_id
    ).with_for_update().first()
    if not listing or not listing.is_active:
        raise HTTPException(status_code=404, detail="Listado no encontrado o cerrado")
    if listing.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo el vendedor puede aceptar pujas")

    winning = db.query(ListingBid).filter(
        ListingBid.id == bid_id,
        ListingBid.listing_id == listing.id
    ).first()
    if not winning:
        raise HTTPException(status_code=404, detail="Puja no encontrada")
        
    card = db.query(UserCard).filter(
        UserCard.id == listing.card_id
    ).with_for_update().first()
    
    if not card or card.user_id != listing.seller_id:
        raise HTTPException(status_code=400, detail="La carta ya no pertenece al vendedor")

    # [↓ SEGURIDAD] Bloqueo pesimista en los balances de comprador y vendedor
    # Para evitar deadlocks, bloqueamos siempre en el mismo orden (por ID de usuario)
    ids = sorted([winning.user_id, listing.seller_id])
    
    # Bloquear primer miembro (ID menor)
    db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == ids[0]
    ).with_for_update().first()
    
    # Bloquear segundo miembro (ID mayor)
    db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == ids[1]
    ).with_for_update().first()

    # Obtener referencias locales después del bloqueo
    # [↓ FIX CRÍTICO] Bloqueo pesimista estricto para comprador y vendedor
    # Ordenamos los IDs para evitar Deadlocks en MySQL/PostgreSQL
    ids = sorted([winning.user_id, listing.seller_id])
    
    for user_id in ids:
        db.query(LeagueMember).filter(
            LeagueMember.league_id == league_id,
            LeagueMember.user_id == user_id
        ).with_for_update().first()

    # Recargar referencias frescas tras el bloqueo
    winner_member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == winning.user_id
    ).first()
    
    seller_member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == listing.seller_id
    ).first()

    if not winner_member:
        raise HTTPException(status_code=400, detail="El postor ya no es miembro de la liga")

    # Limpieza total: devolver pujas de otros y expirar ofertas del sistema
    _cleanup_listing_related_offers(db, listing)

    # FIX: Validar que el comprador no se quede en negativo por un descuadre previo
    if winner_member.coins < winning.amount:
        raise HTTPException(status_code=400, detail="El comprador no tiene fondos suficientes en este momento")

    # Cobrar al ganador con seguridad matemática
    winner_member.locked_coins = max(0, winner_member.locked_coins - winning.amount)
    winner_member.coins -= winning.amount
    
    # Pagar al vendedor
    if seller_member:
        seller_member.coins += winning.amount

    sale_amount = winning.amount
    buyer_username = winning.user.username
    buyer_id = winning.user_id
    pname = card.player.name

    buyer_team = db.query(Team).filter(
        Team.user_id == buyer_id,
        Team.league_id == league_id
    ).first()

    if not buyer_team:
        buyer_team = Team(
            user_id=buyer_id,
            league_id=league_id,
            name=f"Equipo {buyer_id}"
        )
        db.add(buyer_team)
        db.flush()

    card.user_id = buyer_id
    card.team_id = buyer_team.id
    card.is_in_lineup = False

    db.delete(winning)

    listing.is_active = False
    listing.sold_at = datetime.utcnow()
    listing.buyer_id = buyer_id

    db.commit()

    return {
        "message": f"Has vendido a {pname} a @{buyer_username} por {sale_amount:,}",
        "player_name": pname,
        "remaining_coins": seller_member.coins if seller_member else 0,
    }


# ==========================================
# OFERTAS DEL SISTEMA
# ==========================================

@router.get("/{league_id}/my-offers")
async def get_my_offers(
    league_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener ofertas del sistema pendientes para el usuario."""
    from app.models.models import MarketListing
    
    offers = db.query(SystemOffer).join(MarketListing).filter(
        SystemOffer.league_id == league_id,
        SystemOffer.user_id == current_user.id,
        SystemOffer.is_accepted == False,
        SystemOffer.is_expired == False,
        SystemOffer.expires_at > datetime.utcnow(),
        MarketListing.is_active == True  # Solo mostrar si la venta sigue activa
    ).all()

    result = []
    for o in offers:
        result.append({
            "id": o.id,
            "listing_id": o.listing_id,
            "player_name": o.card.player.name,
            "offer_price": o.offer_price,
            "asking_price": o.listing.asking_price,
            "offered_at": o.offered_at.isoformat(),
            "expires_at": o.expires_at.isoformat()
        })

    return result


@router.post("/{league_id}/accept-offer/{offer_id}")
async def accept_offer(
    league_id: int,
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aceptar una oferta del sistema — vende la carta al precio ofrecido y la elimina."""
    offer = db.query(SystemOffer).filter(
        SystemOffer.id == offer_id,
        SystemOffer.user_id == current_user.id,
        SystemOffer.league_id == league_id,
        SystemOffer.is_accepted == False,
        SystemOffer.is_expired == False
    ).with_for_update().first()
    
    if not offer:
        raise HTTPException(status_code=404, detail="Oferta no encontrada o expirada")
        
    if offer.expires_at < datetime.utcnow():
        offer.is_expired = True
        db.commit()
        raise HTTPException(status_code=400, detail="La oferta ha expirado")

    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).with_for_update().first()
    
    if not member:
        raise HTTPException(status_code=404, detail="No eres miembro de esta liga")

    card = offer.card
    if not card:
        raise HTTPException(status_code=404, detail="La carta ya no existe o ya fue vendida")

    # 1. Guardamos en memoria lo que necesitamos para la respuesta antes de borrar
    player_name = card.player.name if card.player else "Jugador desconocido"
    offer_price = offer.offer_price
    
    # 2. Pagamos al usuario
    member.coins += offer_price

    # 3. Limpieza de listados si existen
    if offer.listing and offer.listing.is_active:
        _cleanup_listing_related_offers(db, offer.listing)

    # 4. Aniquilamos todo: Carta, Listado y Ofertas (incluyendo esta misma)
    # Al no pasar exclude_offer_id, se borra la propia oferta evitando el IntegrityError
    _delete_card_and_dependencies(db, card)

    db.commit()

    return {
        "message": f"Has vendido a {player_name} al sistema por {offer_price:,} monedas",
        "player_name": player_name,
        "price_received": offer_price,
        "remaining_coins": member.coins
    }



# ==========================================
# CLAUSULAZOS Y BLINDAJES
# ==========================================

@router.post("/{league_id}/clause/{card_id}")
async def pay_release_clause(
    league_id: int,
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pagar la cláusula de rescisión de un jugador de otro usuario.
    El precio es el valor de mercado actual + el valor protegido (blindaje).
    """
    # Try to find the card — handle cards whose league_id may be NULL
    card = db.query(UserCard).filter(UserCard.id == card_id, UserCard.league_id == league_id).first()
    if not card:
        # Fallback: find card by id and verify it belongs to this league via its team
        card = db.query(UserCard).filter(UserCard.id == card_id).first()
        if card:
            if card.team and card.team.league_id == league_id:
                # Fix the league_id while we're at it
                card.league_id = league_id
                db.flush()
            else:
                card = None
    if not card:
        raise HTTPException(status_code=404, detail="Carta no encontrada en esta liga")

    if card.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes pagar la cláusula de tu propio jugador")

    # [NUEVO] Las leyendas siempre son clausulables aunque no sean transferibles al mercado
    if not card.is_tradeable and not card.player.is_legend:
        raise HTTPException(status_code=400, detail="Este jugador no es transferible")

    # [↓ SEGURIDAD] Bloqueos pesimistas para evitar doble clausulazo
    # Para evitar deadlocks, bloqueamos siempre en el mismo orden (por ID de usuario)
    ids = sorted([current_user.id, card.user_id])

    # Primero bloquear el miembro con ID menor
    db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == ids[0]
    ).with_for_update().first()

    # Luego bloquear el miembro con ID mayor
    db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == ids[1]
    ).with_for_update().first()

    # Obtener referencias locales
    buyer_membership = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()

    if not buyer_membership:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")

    seller_membership = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == card.user_id
    ).first()

    # Luego bloquear la carta en sí para evitar dos compradores simultáneos
    original_owner_id = card.user_id  # guardar antes de sobreescribir la variable
    card = db.query(UserCard).filter(
        UserCard.id == card_id,
        UserCard.user_id == original_owner_id
    ).with_for_update().first()
    if not card:
        raise HTTPException(status_code=404, detail="La carta ya no está disponible (vendida o transferida)")

    clause_price = int(card.current_market_value)
    if buyer_membership.coins < clause_price:
        raise HTTPException(status_code=400, detail=f"No tienes suficientes monedas ({clause_price:,})")

    # Transfer money
    buyer_membership.coins -= clause_price
    if seller_membership:
        seller_membership.coins += clause_price

    # Remove actively listed card if any
    active_listing = db.query(MarketListing).filter(MarketListing.card_id == card.id, MarketListing.is_active == True).first()
    if active_listing:
        _cleanup_listing_related_offers(db, active_listing)
        active_listing.is_active = False
        active_listing.sold_at = datetime.utcnow()
        active_listing.buyer_id = current_user.id

    # Find buyer team
    buyer_team = db.query(Team).filter(Team.league_id == league_id, Team.user_id == current_user.id).first()

    if not buyer_team:
        buyer_team = Team(
            user_id=current_user.id,
            league_id=league_id,
            name=f"Equipo {current_user.id}"
        )
        db.add(buyer_team)
        db.flush()

    # Transfer Card
    card.user_id = current_user.id
    card.team_id = buyer_team.id
    card.is_in_lineup = False
    card.protected_value = 0 # Reset blindaje

    db.commit()

    return {
        "message": f"Has fichado a {card.player.name} pagando su cláusula por {clause_price:,}"
    }


from app.schemas.market import ProtectCardRequest

@router.post("/{league_id}/protect/{card_id}")
async def protect_player(
    league_id: int,
    card_id: int,
    data: ProtectCardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Blindar a un jugador: "quemar" monedas para subir su cláusula de rescisión permanentemente.
    """
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="La cantidad a blindar debe ser mayor que cero")

    card = db.query(UserCard).filter(UserCard.id == card_id, UserCard.league_id == league_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Carta no encontrada en esta liga")

    if card.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo puedes blindar a tus propios jugadores")

    # [↓ SEGURIDAD] Bloqueo pesimista en blindaje para evitar gastar las mismas monedas dos veces
    my_membership = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).with_for_update().first()
    if not my_membership:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")

    if my_membership.coins < data.amount:
        raise HTTPException(status_code=400, detail="No tienes suficientes monedas para este blindaje")

    # Burn money
    my_membership.coins -= data.amount

    # Increase protected value
    card.protected_value = (card.protected_value or 0) + data.amount

    db.commit()

    return {
        "message": f"Has aumentado la cláusula de {card.player.name} en {data.amount:,} monedas",
        "new_value": card.current_market_value
    }
