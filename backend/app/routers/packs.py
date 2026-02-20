"""
Router de Sobres (Packs) — Abrir sobres de iconos dentro de una liga
Los sobres de iconos son la ÚNICA forma de obtener jugadores legendarios (icons).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from typing import List

from app.core.database import get_db
from app.models.models import User, Player, UserCard, LeagueMember, CardRarity, PackOpening
from app.schemas.pack import PackOpenResponse, PackCardResult, PackHistoryItem
from app.routers.auth import get_current_user

router = APIRouter()

# Precio del sobre de iconos
ICON_PACK_COST = 150_000_000  # 150M monedas
ICON_PACK_CARDS = 3  # 3 cartas por sobre


@router.post("/open", response_model=PackOpenResponse)
async def open_icon_pack(
    league_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Abrir un sobre de iconos dentro de una liga.
    - Cuesta 150.000.000 monedas
    - Solo salen jugadores con is_legend=True
    - El usuario debe pertenecer a la liga
    - Se obtienen 3 cartas legendarias aleatorias
    """
    # Verificar que el usuario pertenece a la liga
    membership = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=403,
            detail="No perteneces a esta liga"
        )

    # Verificar que tiene suficientes monedas (DE LA LIGA)
    if membership.coins < ICON_PACK_COST:
        raise HTTPException(
            status_code=400,
            detail=f"No tienes suficientes monedas en esta liga. Necesitas {ICON_PACK_COST:,}, tienes {membership.coins:,}"
        )

    # Obtener jugadores legendarios disponibles
    legends = db.query(Player).filter(
        Player.is_legend == True
    ).all()

    if len(legends) < ICON_PACK_CARDS:
        raise HTTPException(
            status_code=500,
            detail="No hay suficientes jugadores legendarios en la base de datos"
        )

    # Seleccionar cartas aleatorias (pueden repetirse entre sobres, pero no dentro del mismo)
    import random
    selected_players = random.sample(legends, min(ICON_PACK_CARDS, len(legends)))

    # Crear el registro del pack
    pack = PackOpening(
        user_id=current_user.id,
        league_id=league_id,
        pack_type="icon",
        cost=ICON_PACK_COST,
        cards_obtained=len(selected_players)
    )
    db.add(pack)

    # Restar monedas de la LIGA
    membership.coins -= ICON_PACK_COST

    # Dar XP por abrir sobre (al usuario global)
    current_user.experience += 100

    # Crear las cartas para el usuario (Vinculadas a la liga)
    result_cards = []
    for player in selected_players:
        card = UserCard(
            user_id=current_user.id,
            player_id=player.id,
            league_id=league_id,  # Importante: carta de esta liga
            current_overall=player.overall_rating,
            is_tradeable=False  # Las cartas de sobre no son vendibles
        )
        db.add(card)
        db.flush()  # Para obtener el ID

        result_cards.append(PackCardResult(
            card_id=card.id,
            player_id=player.id,
            player_name=player.name,
            position=player.position.value,
            overall_rating=player.overall_rating,
            base_rarity=player.base_rarity.value,
            is_legend=player.is_legend,
            image_url=player.image_url
        ))

    db.commit()

    return PackOpenResponse(
        message=f"¡Has abierto un Sobre de Iconos! Has obtenido {len(result_cards)} leyendas",
        pack_type="icon",
        cards=result_cards,
        cost=ICON_PACK_COST,
        remaining_coins=membership.coins
    )


@router.get("/history", response_model=List[PackHistoryItem])
async def pack_history(
    league_id: int = Query(..., description="ID de la liga"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Historial de sobres abiertos por el usuario en una liga"""
    packs = db.query(PackOpening).filter(
        PackOpening.user_id == current_user.id,
        PackOpening.league_id == league_id
    ).order_by(PackOpening.opened_at.desc()).limit(limit).all()

    return [
        PackHistoryItem(
            id=p.id,
            pack_type=p.pack_type,
            cost=p.cost,
            cards_obtained=p.cards_obtained,
            opened_at=p.opened_at
        )
        for p in packs
    ]
