"""
Router de Jugadores — Listar, Detalle, Mis Cartas
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.models import User, Player, UserCard, PlayerMatchStats, Match, Gameweek, CardRarity
from pydantic import BaseModel
from app.schemas.market import UserCardResponse
from app.routers.auth import get_current_user
from fastapi import HTTPException

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
        # Convertir el string recibido al enum correcto (case-insensitive)
        try:
            rarity_enum = CardRarity[rarity.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Rareza inválida: '{rarity}'. Valores válidos: bronze, silver, gold, legend"
            )
        query = query.filter(Player.base_rarity == rarity_enum)

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
            acquired_at=c.acquired_at,
            league_id=c.league_id,
            scoring_profile=c.player.scoring_profile,
            min_fantasy=c.player.min_fantasy,
            max_fantasy=c.player.max_fantasy,
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
    """Obtiene el historial de puntos de un jugador partido a partido.
    Devuelve TODAS las jornadas, rellenando con 0 donde no haya datos."""
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    
    # Los iconos no tienen partidos reales — devolver lista vacía
    if player.is_legend:
        return []
    
    # Get all gameweeks ordered by number
    all_gameweeks = db.query(Gameweek).order_by(Gameweek.number.asc()).all()
    
    # Get all stats for this player, indexed by gameweek number
    stats = db.query(PlayerMatchStats).join(Match).join(Gameweek).filter(
        PlayerMatchStats.player_id == player_id
    ).all()
    
    # Build a lookup: gameweek_number -> list of stats
    stats_by_gw = {}
    for stat in stats:
        gw_num = stat.match.gameweek.number if stat.match.gameweek else 0
        if gw_num not in stats_by_gw:
            stats_by_gw[gw_num] = []
        stats_by_gw[gw_num].append(stat)
    
    player_team = player.current_team or "Equipo Desconocido"
    
    # 1. Build a robust map of Gameweek ID -> Number to avoid relationship loading issues
    gw_id_to_num = {gw.id: gw.number for gw in all_gameweeks}
    
    # 2. Get all matches for this player's specific team.
    # We NO LONGER use a shared search term to avoid mixing Dundee and Dundee United.
    team_filter = [Match.home_team == player_team, Match.away_team == player_team]
    
    # Only if the player is from Dundee United, we also look for "Dundee" as a potential fallback
    # to handle the data gap, but we will prioritize exact matches in the loop.
    if player_team == "Dundee United":
        team_filter.extend([Match.home_team == "Dundee", Match.away_team == "Dundee"])
        
    team_matches = db.query(Match).filter(or_(*team_filter)).all()
    
    # 3. Mapping by gameweek NUMBER
    matches_by_gw_num = {}
    for m in team_matches:
        num = gw_id_to_num.get(m.gameweek_id, 0)
        if num > 0:
            if num not in matches_by_gw_num:
                matches_by_gw_num[num] = []
            matches_by_gw_num[num].append(m)
    
    history = []
    for gw in all_gameweeks:
        # Priority 1: Real stats (Always use the match linked to the stats)
        if gw.number in stats_by_gw:
            for stat in stats_by_gw[gw.number]:
                match = stat.match
                history.append(PlayerMatchHistoryResponse(
                    match_id=match.id,
                    gameweek_number=gw.number,
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
        # Priority 2: Fallback to team matches (Only if player has no stats)
        elif gw.number in matches_by_gw_num:
            # Pick the best match: Exact team name match takes precedence
            potential_matches = matches_by_gw_num[gw.number]
            exact_matches = [m for m in potential_matches if m.home_team == player_team or m.away_team == player_team]
            
            # Use exact match if found, otherwise (only for Dundee United) use the Dundee fallback
            matches_to_show = exact_matches if exact_matches else potential_matches
            
            # If we still have multiple (shouldn't happen with exact names), take the first one
            if matches_to_show:
                match = matches_to_show[0]
                is_home = match.home_team == player_team
                history.append(PlayerMatchHistoryResponse(
                    match_id=match.id,
                    gameweek_number=gw.number,
                    home_team=match.home_team,
                    away_team=match.away_team,
                    home_score=match.home_score,
                    away_score=match.away_score,
                    status=match.status.value,
                    minutes_played=0,
                    rating=None,
                    goals=0,
                    assists=0,
                    fantasy_points=0.0,
                    clean_sheet=False,
                    goals_conceded=match.away_score if is_home else match.home_score,
                    yellow_cards=0,
                    red_cards=0,
                    saves=0
                ))
        # Priority 3: Last resort (ghost row)
        else:
            if gw.is_finished:
                history.append(PlayerMatchHistoryResponse(
                    match_id=0,
                    gameweek_number=gw.number,
                    home_team=player_team,
                    away_team="—",
                    home_score=None,
                    away_score=None,
                    status="FINISHED",
                    minutes_played=0,
                    rating=None,
                    goals=0,
                    assists=0,
                    fantasy_points=0.0,
                    clean_sheet=False,
                    goals_conceded=0,
                    yellow_cards=0,
                    red_cards=0,
                    saves=0
                ))
    # Sort by gameweek number descending (most recent first)
    history.sort(key=lambda h: h.gameweek_number, reverse=True)
    
    return history
