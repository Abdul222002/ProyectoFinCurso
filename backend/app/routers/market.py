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
    User, Player, UserCard, LeagueMember, 
    MarketAuction, AuctionSlot, AuctionBid,
    MarketListing, SystemOffer
)
from app.schemas.market import (
    AuctionResponse, AuctionSlotResponse, BidRequest, 
    BidResponse, SellResponse,
    ListCardRequest, ListingResponse, SystemOfferResponse
)
from app.routers.auth import get_current_user

router = APIRouter()

AUCTION_DURATION_HOURS = 24
SLOTS_PER_AUCTION = 12

def _resolve_auction(auction: MarketAuction, db: Session):
    """
    Cierra una subasta, genera las cartas para los ganadores
    y marca la subasta como resuelta.
    """
    if auction.is_resolved:
        return

    # Procesar cada slot
    for slot in auction.slots:
        if slot.highest_bidder_id:
            # Crear la carta para el ganador
            # (El dinero ya se descontó al pujar)
            
            # Obtener overall actual del jugador
            player = slot.player
            
            card = UserCard(
                user_id=slot.highest_bidder_id,
                player_id=slot.player_id,
                league_id=auction.league_id,
                current_overall=player.overall_rating,
                is_tradeable=True
            )
            db.add(card)
    
    auction.is_active = False
    auction.is_resolved = True
    db.commit()


def _create_new_auction(league_id: int, db: Session) -> MarketAuction:
    """Genera una nueva subasta con 12 jugadores aleatorios (NO LEGENDS)"""
    
    # 1. Crear la subasta
    now = datetime.utcnow()
    ends_at = now + timedelta(hours=AUCTION_DURATION_HOURS)
    
    auction = MarketAuction(
        league_id=league_id,
        started_at=now,
        ends_at=ends_at,
        is_active=True
    )
    db.add(auction)
    db.flush() # ID necesario
    
    # 2. Seleccionar 12 jugadores aleatorios (NO LEGENDS)
    # Podríamos filtrar por rareza para asegurar variedad
    players = db.query(Player).filter(
        Player.is_legend == False
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
        
    # Construir respuesta
    slots_resp = []
    for slot in auction.slots:
        slots_resp.append(AuctionSlotResponse(
            id=slot.id,
            player_id=slot.player_id,
            player_name=slot.player.name,
            position=slot.player.position.value,
            overall_rating=slot.player.overall_rating,
            base_rarity=slot.player.base_rarity.value,
            image_url=slot.player.image_url,
            base_price=slot.base_price,
            current_bid=slot.current_bid,
            highest_bidder_id=slot.highest_bidder_id,
            highest_bidder_username=None
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
    Pujar por un jugador en la subasta.
    - Se descuentan las monedas de la liga inmediatamente.
    - Si alguien supera tu puja, se te devuelven las monedas.
    """
    amount = bid_data.amount
    
    # 1. Validaciones
    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()
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
        # Auto resolver si intentan pujar fuera de tiempo
        _resolve_auction(slot.auction, db)
        raise HTTPException(status_code=400, detail="La subasta ha finalizado")

    # Validar montos
    min_bid = max(slot.base_price, slot.current_bid + 1_000_000) # Mínimo incremento 1M? O solo superar?
    # Vamos a decir que hay que superar al mayor postor. Si no hay pujas, base_price.
    # Si hay puja, superar.
    
    required_bid = slot.base_price
    if slot.current_bid > 0:
        required_bid = slot.current_bid + 1 # Al menos 1 moneda más
        
    if amount < required_bid:
        raise HTTPException(status_code=400, detail=f"La puja debe ser al menos {required_bid:,}")
        
    if member.coins < amount:
        raise HTTPException(status_code=400, detail=f"No tienes suficientes monedas ({member.coins:,})")

    # 2. Gestión de economía
    
    # Devolver monedas al anterior ganador (si existe y no es el mismo usuario)
    if slot.highest_bidder_id:
        prev_bidder_member = db.query(LeagueMember).filter(
            LeagueMember.league_id == league_id,
            LeagueMember.user_id == slot.highest_bidder_id
        ).first()
        if prev_bidder_member:
            prev_bidder_member.coins += slot.current_bid
    
    # Restar monedas al nuevo pujador
    member.coins -= amount
    
    # 3. Actualizar Slot
    slot.current_bid = amount
    slot.highest_bidder_id = current_user.id
    
    # 4. Registrar historial
    bid = AuctionBid(
        slot_id=slot.id,
        user_id=current_user.id,
        amount=amount
    )
    db.add(bid)
    
    db.commit()
    
    return BidResponse(
        message="Puja realizada con éxito",
        slot_id=slot.id,
        new_bid=amount,
        remaining_coins=member.coins
    )


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
    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")
        
    card = db.query(UserCard).filter(
        UserCard.id == card_id,
        UserCard.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Carta no encontrada en tu inventario de esta liga")
        
    if card.league_id != league_id:
        if card.team and card.team.league_id == league_id:
            card.league_id = league_id
            db.commit()
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
    
    # Eliminar carta
    db.delete(card)
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
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Carta no encontrada")
        
    if card.league_id != league_id:
        if card.team and card.team.league_id == league_id:
            card.league_id = league_id
            db.commit()
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
    ).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listado no encontrado")

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
        result.append({
            "id": l.id,
            "card_id": l.card_id,
            "player_name": player.name,
            "position": player.position.value,
            "overall_rating": player.overall_rating,
            "base_rarity": player.base_rarity.value,
            "image_url": player.image_url,
            "asking_price": l.asking_price,
            "seller_username": seller.username,
            "is_mine": l.seller_id == current_user.id,
            "listed_at": l.listed_at.isoformat()
        })

    return result


@router.post("/{league_id}/buy-listing/{listing_id}")
async def buy_listing(
    league_id: int,
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Comprar una carta de otro usuario."""
    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")

    listing = db.query(MarketListing).filter(
        MarketListing.id == listing_id,
        MarketListing.league_id == league_id,
        MarketListing.is_active == True
    ).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listado no encontrado o ya vendido")
    if listing.seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes comprar tu propia carta")
    if member.coins < listing.asking_price:
        raise HTTPException(status_code=400, detail="No tienes suficientes monedas")

    # Transfer money
    member.coins -= listing.asking_price
    seller_member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == listing.seller_id
    ).first()
    if seller_member:
        seller_member.coins += listing.asking_price

    # Transfer card
    card = listing.card
    card.user_id = current_user.id
    card.team_id = None  # Remove from seller's team, buyer assigns manually

    # Close listing
    listing.is_active = False
    listing.sold_at = datetime.utcnow()
    listing.buyer_id = current_user.id

    db.commit()

    return {
        "message": f"Has comprado a {card.player.name} por {listing.asking_price:,}",
        "player_name": card.player.name,
        "remaining_coins": member.coins
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
    offers = db.query(SystemOffer).filter(
        SystemOffer.league_id == league_id,
        SystemOffer.user_id == current_user.id,
        SystemOffer.is_accepted == False,
        SystemOffer.is_expired == False,
        SystemOffer.expires_at > datetime.utcnow()
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
    """Aceptar una oferta del sistema — vende la carta al precio ofrecido."""
    offer = db.query(SystemOffer).filter(
        SystemOffer.id == offer_id,
        SystemOffer.user_id == current_user.id,
        SystemOffer.league_id == league_id,
        SystemOffer.is_accepted == False,
        SystemOffer.is_expired == False
    ).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Oferta no encontrada o expirada")
    if offer.expires_at < datetime.utcnow():
        offer.is_expired = True
        db.commit()
        raise HTTPException(status_code=400, detail="La oferta ha expirado")

    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()

    # Give coins
    member.coins += offer.offer_price

    # Delete card
    card = offer.card
    player_name = card.player.name
    db.delete(card)

    # Close offer and listing
    offer.is_accepted = True
    offer.listing.is_active = False
    offer.listing.sold_at = datetime.utcnow()

    db.commit()

    return {
        "message": f"Has vendido a {player_name} al sistema por {offer.offer_price:,}",
        "player_name": player_name,
        "price_received": offer.offer_price,
        "remaining_coins": member.coins
    }
