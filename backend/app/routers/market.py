"""
Router del Mercado — Comprar y Vender jugadores
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.models import User, Player, UserCard
from app.schemas.market import MarketPlayerResponse, BuyResponse, SellResponse
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[MarketPlayerResponse])
async def market_listings(
    position: Optional[str] = Query(None),
    sort_by: str = Query("current_price", description="current_price, overall_rating"),
    order: str = Query("desc"),
    search: Optional[str] = Query(None, description="Buscar por nombre"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Listar jugadores disponibles en el mercado con precios (sin legends)"""
    query = db.query(Player)

    # EXCLUIR legends del mercado — solo obtenerlos en sobres
    query = query.filter(Player.is_legend == False)

    if position:
        query = query.filter(Player.position == position)

    if search:
        query = query.filter(Player.name.ilike(f"%{search}%"))

    sort_column = getattr(Player, sort_by, Player.current_price)
    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    players = query.offset(offset).limit(limit).all()

    return [
        MarketPlayerResponse(
            id=p.id,
            name=p.name,
            position=p.position.value,
            overall_rating=p.overall_rating,
            current_team=p.current_team,
            current_price=p.current_price,
            target_price=p.target_price,
            base_rarity=p.base_rarity.value,
            is_legend=p.is_legend,
            image_url=p.image_url,
            price_change_pct=p.price_gap_percentage
        )
        for p in players
    ]


@router.post("/buy/{player_id}", response_model=BuyResponse)
async def buy_player(
    player_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Comprar un jugador — crea una UserCard y resta coins"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    price = int(player.current_price)

    if current_user.coins < price:
        raise HTTPException(
            status_code=400,
            detail=f"No tienes suficientes monedas. Necesitas {price:,}, tienes {current_user.coins:,}"
        )

    # Crear carta
    card = UserCard(
        user_id=current_user.id,
        player_id=player.id,
        current_overall=player.overall_rating,
        is_tradeable=True
    )
    db.add(card)

    # Restar monedas
    current_user.coins -= price
    # Dar XP por la compra
    current_user.experience += 10

    db.commit()
    db.refresh(card)

    return BuyResponse(
        message=f"¡Has comprado a {player.name}!",
        card_id=card.id,
        player_name=player.name,
        price_paid=price,
        remaining_coins=current_user.coins
    )


@router.post("/sell/{card_id}", response_model=SellResponse)
async def sell_card(
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Vender una carta — elimina UserCard y suma coins (85% del precio)"""
    card = db.query(UserCard).filter(
        UserCard.id == card_id,
        UserCard.user_id == current_user.id
    ).first()

    if not card:
        raise HTTPException(status_code=404, detail="Carta no encontrada en tu inventario")

    if not card.is_tradeable:
        raise HTTPException(status_code=400, detail="Esta carta no se puede vender")

    if card.is_in_lineup:
        raise HTTPException(status_code=400, detail="Retira la carta de la alineación antes de venderla")

    player = card.player
    # El usuario recibe el 85% del precio actual (comisión del mercado)
    sell_price = int(player.current_price * 0.85)

    player_name = player.name

    # Sumar monedas
    current_user.coins += sell_price
    current_user.experience += 5

    # Eliminar carta
    db.delete(card)
    db.commit()

    return SellResponse(
        message=f"Has vendido a {player_name} por {sell_price:,} monedas",
        player_name=player_name,
        price_received=sell_price,
        remaining_coins=current_user.coins
    )
