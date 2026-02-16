"""
Router de Equipos — Gestión de equipo por liga
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.models import User, Team, UserCard
from app.schemas.team import TeamResponse, TeamUpdate, SetLineupRequest
from app.routers.auth import get_current_user

router = APIRouter()


def _team_to_response(team: Team) -> dict:
    """Convierte un Team a dict de respuesta"""
    players_data = []
    for card in team.players:
        players_data.append({
            "id": card.id,
            "player_id": card.player_id,
            "player_name": card.player.name,
            "position": card.player.position.value,
            "current_overall": card.current_overall,
            "base_rarity": card.player.base_rarity.value,
            "is_in_lineup": card.is_in_lineup,
            "current_market_value": card.player.current_price
        })

    return {
        "id": team.id,
        "name": team.name,
        "league_id": team.league_id,
        "league_name": team.league.name if team.league else None,
        "overall_rating": team.overall_rating,
        "active_formation": team.active_formation,
        "arena_wins": team.arena_wins,
        "arena_losses": team.arena_losses,
        "arena_draws": team.arena_draws,
        "arena_rating": team.arena_rating,
        "players": players_data
    }


@router.get("/my")
async def get_my_team(
    league_id: Optional[int] = Query(None, description="ID de la liga (opcional)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener mi equipo. Si se pasa league_id, devuelve el equipo de esa liga.
    Si no, devuelve la lista de todos mis equipos.
    """
    if league_id:
        team = db.query(Team).filter(
            Team.user_id == current_user.id,
            Team.league_id == league_id
        ).first()
        if not team:
            raise HTTPException(status_code=404, detail="No tienes equipo en esta liga")
        return _team_to_response(team)
    else:
        # Devolver todos los equipos del usuario
        teams = db.query(Team).filter(Team.user_id == current_user.id).all()
        return [_team_to_response(t) for t in teams]


@router.put("/my")
async def update_my_team(
    data: TeamUpdate,
    league_id: int = Query(..., description="ID de la liga"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar nombre o formación del equipo en una liga"""
    team = db.query(Team).filter(
        Team.user_id == current_user.id,
        Team.league_id == league_id
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="No tienes equipo en esta liga")

    if data.name:
        team.name = data.name
    if data.formation:
        team.active_formation = data.formation

    db.commit()
    db.refresh(team)
    return _team_to_response(team)


@router.put("/my/lineup")
async def set_lineup(
    data: SetLineupRequest,
    league_id: int = Query(..., description="ID de la liga"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Establecer los 11 titulares de un equipo en una liga"""
    team = db.query(Team).filter(
        Team.user_id == current_user.id,
        Team.league_id == league_id
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="No tienes equipo en esta liga")

    if len(data.lineup_card_ids) > 11:
        raise HTTPException(status_code=400, detail="Máximo 11 titulares")

    # Verificar que las cartas pertenezcan al equipo
    team_card_ids = [c.id for c in team.players]
    for card_id in data.lineup_card_ids:
        if card_id not in team_card_ids:
            raise HTTPException(status_code=400, detail=f"La carta {card_id} no pertenece a tu equipo")

    # Resetear todos a suplentes
    for card in team.players:
        card.is_in_lineup = card.id in data.lineup_card_ids

    # Recalcular OVR
    lineup_cards = [c for c in team.players if c.is_in_lineup]
    if lineup_cards:
        team.overall_rating = sum(c.current_overall for c in lineup_cards) / len(lineup_cards)

    db.commit()
    db.refresh(team)
    return _team_to_response(team)
