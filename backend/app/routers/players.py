"""
Router de Jugadores — Listar, Detalle, Mis Cartas
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.models import User, Player, UserCard, PlayerMatchStats, Match, Gameweek
from pydantic import BaseModel
from app.schemas.market import UserCardResponse
from app.routers.auth import get_current_user

router = APIRouter()


class PlayerListResponse(BaseModel):
    """Respuesta de listado de jugadores"""
    id: int
    name: str
    position: str
    overall_rating: int
    current_team: Optional[str]
    current_price: float
    target_price: float
    base_rarity: str
    is_legend: bool
    image_url: Optional[str]
    price_change_pct: float

    class Config:
        from_attributes = True


@router.get("/", response_model=List[PlayerListResponse])
async def list_players(
    position: Optional[str] = Query(None, description="Filtrar por posición: GK, DEF, MID, FWD"),
    team: Optional[str] = Query(None, description="Filtrar por equipo"),
    min_ovr: Optional[int] = Query(None, ge=50, le=99),
    max_ovr: Optional[int] = Query(None, ge=50, le=99),
    rarity: Optional[str] = Query(None, description="bronze, silver, gold, legend"),
    sort_by: str = Query("overall_rating", description="overall_rating, current_price, name"),
    order: str = Query("desc", description="asc o desc"),
    limit: int = Query(600, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Listar todos los jugadores con filtros"""
    query = db.query(Player)

    if position:
        query = query.filter(Player.position == position)
    if team:
        query = query.filter(Player.current_team.ilike(f"%{team}%"))
    if min_ovr:
        query = query.filter(Player.overall_rating >= min_ovr)
    if max_ovr:
        query = query.filter(Player.overall_rating <= max_ovr)
    if rarity:
        query = query.filter(Player.base_rarity == rarity)

    # Ordenar
    sort_column = getattr(Player, sort_by, Player.overall_rating)
    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    players = query.offset(offset).limit(limit).all()

    return [
        PlayerListResponse(
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


@router.get("/{player_id}", response_model=PlayerListResponse)
async def get_player_detail(
    player_id: int,
    db: Session = Depends(get_db)
):
    """Detalle de un jugador específico"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    return PlayerListResponse(
        id=player.id,
        name=player.name,
        position=player.position.value,
        overall_rating=player.overall_rating,
        current_team=player.current_team,
        current_price=player.current_price,
        target_price=player.target_price,
        base_rarity=player.base_rarity.value,
        is_legend=player.is_legend,
        image_url=player.image_url,
        price_change_pct=player.price_gap_percentage
    )


@router.get("/my-cards/all", response_model=List[UserCardResponse])
async def my_cards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener todas mis cartas (inventario)"""
    cards = db.query(UserCard).filter(
        UserCard.user_id == current_user.id
    ).all()

    return [
        UserCardResponse(
            id=c.id,
            player_id=c.player_id,
            player_name=c.player.name,
            position=c.player.position.value,
            overall_rating=c.player.overall_rating,
            current_overall=c.current_overall,
            current_price=c.player.current_price,
            base_rarity=c.player.base_rarity.value,
            is_legend=c.player.is_legend,
            is_tradeable=c.is_tradeable,
            is_in_lineup=c.is_in_lineup,
            image_url=c.player.image_url,
            current_team=c.player.current_team,
            nationality=c.player.nationality,
            pace=c.player.pace,
            shooting=c.player.shooting,
            passing=c.player.passing,
            dribbling=c.player.dribbling,
            defending=c.player.defending,
            physical=c.player.physical,
            acquired_at=c.acquired_at
        )
        for c in cards
    ]


class PlayerMatchHistoryResponse(BaseModel):
    match_id: int
    gameweek_number: int
    home_team: str
    away_team: str
    home_score: Optional[int]
    away_score: Optional[int]
    status: str
    minutes_played: int
    rating: Optional[float]
    goals: int
    assists: int
    fantasy_points: float
    clean_sheet: bool
    goals_conceded: int
    yellow_cards: int
    red_cards: int
    saves: int

    class Config:
        from_attributes = True

@router.get("/{player_id}/history", response_model=List[PlayerMatchHistoryResponse])
async def get_player_history(
    player_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene el historial de puntos de un jugador partido a partido"""
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
        
    stats = db.query(PlayerMatchStats).join(Match).join(Gameweek).filter(
        PlayerMatchStats.player_id == player_id
    ).order_by(Match.kickoff_time.desc()).all()
    
    history = []
    for stat in stats:
        match = stat.match
        history.append(PlayerMatchHistoryResponse(
            match_id=match.id,
            gameweek_number=match.gameweek.number if match.gameweek else 0,
            home_team=match.home_team,
            away_team=match.away_team,
            home_score=match.home_score,
            away_score=match.away_score,
            status=match.status.value,
            minutes_played=stat.minutes_played,
            rating=stat.rating,
            goals=stat.goals,
            assists=stat.assists,
            fantasy_points=stat.fantasy_points,
            clean_sheet=stat.clean_sheet,
            goals_conceded=stat.goals_conceded_team,
            yellow_cards=stat.yellow_cards,
            red_cards=stat.red_cards,
            saves=stat.saves
        ))
        
    return history
