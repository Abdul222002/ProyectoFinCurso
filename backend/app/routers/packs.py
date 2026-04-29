"""
Router de Sobres (Packs) — Abrir sobres de iconos dentro de una liga
Los sobres de iconos son la ÚNICA forma de obtener jugadores legendarios (icons).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql.expression import func
from typing import List

from app.core.database import get_db
from app.models.models import User, Player, UserCard, LeagueMember, CardRarity, PackOpening, PackOpeningCard
from app.schemas.pack import PackOpenResponse, PackCardResult, PackHistoryItem
from app.routers.auth import get_current_user

router = APIRouter()

# Precio del sobre de iconos
ICON_PACK_COST = 150_000_000  # 150M monedas
ICON_PACK_CARDS = 1  # 1 carta por sobre


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
    - Se obtiene 1 carta legendaria ponderada por OVR (más media = más difícil)
    """
    # Verificar que el usuario pertenece a la liga
    # [↓ SEGURIDAD] Bloqueo pesimista para evitar gastar las mismas monedas dos veces
    membership = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).with_for_update().first()

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

    # Obtener los IDs de las leyendas que ya tienen dueño en esta liga
    owned_cards = db.query(UserCard.player_id).filter(
        UserCard.league_id == league_id
    ).all()
    owned_player_ids = {c[0] for c in owned_cards}

    # Filtrar leyendas disponibles
    legends = db.query(Player).filter(
        Player.is_legend == True
    ).all()
    
    available_legends = [p for p in legends if p.id not in owned_player_ids]

    # Find User's Team in this League (to auto-assign the card)
    from app.models.models import Team
    team = db.query(Team).filter(
        Team.user_id == current_user.id,
        Team.league_id == league_id
    ).first()

    if not available_legends:
        raise HTTPException(
            status_code=400,
            detail="No hay jugadores legendarios disponibles en esta liga."
        )

    # Lógica de probabilidad ponderada (Weighted randomness)
    # A mayor OVR, menor es el peso (probabilidad).
    # Hacemos una curva exponencial para que +95 sea súper raro.
    import random
    
    weights = []
    for p in available_legends:
        ovr = p.overall_rating
        if ovr >= 98:
            weight = 1      # Tier S++ (98-99): Míticos (Extremadamente raro)
        elif ovr >= 96:
            weight = 5      # Tier S+ (96-97): Súper leyendas (Muy raro)
        elif ovr >= 94:
            weight = 15     # Tier S (94-95): Leyendas top (Raro)
        elif ovr >= 92:
            weight = 40     # Tier A (92-93): Épico (Poco común)
        elif ovr >= 90:
            weight = 100    # Tier B (90-91): Destacado (Común)
        else:
            weight = 250    # Tier C (87-89): Base (Muy común)
        weights.append(weight)
        
    # Seleccionar 1 carta usando los pesos calculados
    [selected_player] = random.choices(available_legends, weights=weights, k=1)

    # Crear el registro del pack
    pack = PackOpening(
        user_id=current_user.id,
        league_id=league_id,
        pack_type="icon",
        cost=ICON_PACK_COST,
        cards_obtained=1
    )
    db.add(pack)

    # Restar monedas de la LIGA
    membership.coins -= ICON_PACK_COST

    # Dar XP por abrir sobre (al usuario global)
    current_user.experience += 100

    # Crear la carta para el usuario (Vinculada a la liga)
    card = UserCard(
        user_id=current_user.id,
        player_id=selected_player.id,
        league_id=league_id,  # Importante: carta de esta liga
        team_id=team.id if team else None,  # Adding to the team if exists
        current_overall=selected_player.overall_rating,
        is_tradeable=False  # Las cartas de sobre no son vendibles
    )
    db.add(card)
    db.flush()  # Para obtener el ID

    # NUEVO: Trazabilidad del sobre
    pack_trace = PackOpeningCard(
        pack_opening_id=pack.id,
        card_id=card.id
    )
    db.add(pack_trace)

    result_card = PackCardResult(
        card_id=card.id,
        player_id=selected_player.id,
        player_name=selected_player.name,
        position=selected_player.position.value,
        overall_rating=selected_player.overall_rating,
        base_rarity=selected_player.base_rarity.value,
        is_legend=selected_player.is_legend,
        image_url=selected_player.image_url
    )

    db.commit()

    return PackOpenResponse(
        message=f"¡Has abierto un Sobre de Iconos! Has obtenido a {selected_player.name} (OVR {selected_player.overall_rating}).",
        pack_type="icon",
        cards=[result_card], # Devuelve un array de 1
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
    packs = db.query(PackOpening).options(
        joinedload(PackOpening.cards).joinedload(PackOpeningCard.card).joinedload(UserCard.player)
    ).filter(
        PackOpening.user_id == current_user.id,
        PackOpening.league_id == league_id
    ).order_by(PackOpening.opened_at.desc()).limit(limit).all()

    result = []
    for p in packs:
        cards_data = []
        for poc in p.cards:
            c = poc.card
            pl = c.player
            cards_data.append(PackCardResult(
                card_id=c.id,
                player_id=pl.id,
                player_name=pl.name,
                position=pl.position.value,
                overall_rating=c.current_overall,
                base_rarity=pl.base_rarity.value,
                is_legend=pl.is_legend,
                image_url=pl.image_url
            ))
        
        result.append(PackHistoryItem(
            id=p.id,
            pack_type=p.pack_type,
            cost=p.cost,
            cards_obtained=p.cards_obtained,
            opened_at=p.opened_at,
            cards=cards_data
        ))

    return result
