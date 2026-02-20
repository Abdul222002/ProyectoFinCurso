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
    MarketAuction, AuctionSlot, AuctionBid
)
from app.schemas.market import (
    AuctionResponse, AuctionSlotResponse, BidRequest, 
    BidResponse, SellResponse
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
        # Buscar nombre del pujador más alto si existe
        bidder_name = None
        if slot.highest_bidder_id:
            bidder = db.query(User).filter(User.id == slot.highest_bidder_id).first()
            if bidder:
                bidder_name = bidder.username
                
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
            highest_bidder_username=bidder_name
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
        UserCard.user_id == current_user.id,
        UserCard.league_id == league_id
    ).first()
    
    if not card:
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
