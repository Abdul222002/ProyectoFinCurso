"""
Router de Equipos — Gestión de equipo por liga
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.models.models import User, Team, UserCard, Gameweek, GameweekLineup, LeagueMember, GameweekLineupPlayer
from app.schemas.team import TeamResponse, TeamUpdate, SetLineupRequest, GameweekLineupResponse
from app.routers.auth import get_current_user

router = APIRouter()


def _team_to_response(team: Team) -> dict:
    players_data = []
    team_value = 0
    for card in team.players:
        team_value += card.current_market_value
        players_data.append({
            "id": card.id,
            "player_id": card.player_id,
            "player_name": card.player.name,
            "position": card.player.position.value,
            "current_overall": card.current_overall,
            "base_rarity": card.player.base_rarity.value,
            "is_in_lineup": card.is_in_lineup,
            "is_tradeable": card.is_tradeable,
            "current_market_value": card.current_market_value,
            "protected_value": card.protected_value or 0,
            "image_url": card.player.image_url,
            "current_team": card.player.current_team or "Sin equipo",
            "nationality": card.player.nationality,
            "pace": card.player.pace,
            "shooting": card.player.shooting,
            "passing": card.player.passing,
            "dribbling": card.player.dribbling,
            "defending": card.player.defending,
            "physical": card.player.physical,
            "is_legend": card.player.is_legend,
            "scoring_profile": card.player.scoring_profile,
            "min_fantasy": card.player.min_fantasy,
            "max_fantasy": card.player.max_fantasy,
        })

    return {
        "id": team.id,
        "name": team.name,
        "league_id": team.league_id,
        "league_name": team.league.name if team.league else None,
        "overall_rating": team.overall_rating,
        "active_formation": team.active_formation,
        "shield_url": team.shield_url,
        "kit_color_primary": team.kit_color_primary,
        "kit_color_secondary": team.kit_color_secondary,
        "arena_wins": team.arena_wins,
        "arena_losses": team.arena_losses,
        "arena_draws": team.arena_draws,
        "arena_rating": team.arena_rating,
        "team_value": int(team_value),
        "total_fantasy_points": team.total_fantasy_points,
        "created_at": team.created_at,
        "league_id": team.league_id,
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


@router.get("/{league_id}/user/{target_user_id}")
async def get_user_team(
    league_id: int,
    target_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener el equipo de cualquier usuario dentro de una liga (vista de solo lectura).
    El current_user debe pertenecer a la misma liga.
    """
    # Verify current user is in the league
    membership = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")

    team = db.query(Team).filter(
        Team.user_id == target_user_id,
        Team.league_id == league_id
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="El usuario no tiene equipo en esta liga")
        
    return _team_to_response(team)


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
    if hasattr(data, 'shield_url') and data.shield_url is not None:
        team.shield_url = data.shield_url
    if hasattr(data, 'kit_color_primary') and data.kit_color_primary is not None:
        team.kit_color_primary = data.kit_color_primary

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

    # ─── VALIDACIÓN DE POSICIONES ────────────────────────────────────────────
    # Contar posiciones en el lineup propuesto y rechazar combinaciones inválidas
    if data.lineup_card_ids:
        proposed_cards = [c for c in team.players if c.id in data.lineup_card_ids]
        position_counts: dict[str, int] = {}
        for card in proposed_cards:
            pos = card.player.position.value if card.player else None
            if pos:
                position_counts[pos] = position_counts.get(pos, 0) + 1

        # Nunca más de 1 portero
        if position_counts.get("GK", 0) > 1:
            raise HTTPException(
                status_code=400,
                detail="Solo puede haber 1 portero en la alineación"
            )
    # ────────────────────────────────────────────────────────────────────────

    # Resetear todos a suplentes
    for card in team.players:
        card.is_in_lineup = card.id in data.lineup_card_ids

    # Recalcular OVR
    lineup_cards = [c for c in team.players if c.is_in_lineup]
    if lineup_cards:
        team.overall_rating = sum(c.current_overall for c in lineup_cards) / len(lineup_cards)
    else:
        team.overall_rating = 0.0

    db.commit()
    
    # ---------------------------------------------------------
    # AUTOMÁTICO: Guardar Snapshot para la próxima jornada
    # ---------------------------------------------------------
    active_gw = db.query(Gameweek).filter(Gameweek.is_active == True).first()
    if active_gw:
        # Solo guardamos si no ha empezado la jornada (o primer partido)
        # Usamos start_date como límite
        if datetime.utcnow() < active_gw.start_date:
            gw_lineup = db.query(GameweekLineup).filter(
                GameweekLineup.team_id == team.id,
                GameweekLineup.gameweek_id == active_gw.id
            ).first()
            
            if gw_lineup:
                gw_lineup.active_formation = team.active_formation
                # 🔵 RELACIONAL: Actualizar tabla intermedia
                gw_lineup.players = [GameweekLineupPlayer(card_id=pid) for pid in data.lineup_card_ids]
            else:
                # 🔵 RELACIONAL: Crear con relación directa
                gw_lineup = GameweekLineup(
                    team_id=team.id,
                    gameweek_id=active_gw.id,
                    active_formation=team.active_formation
                )
                gw_lineup.players = [GameweekLineupPlayer(card_id=pid) for pid in data.lineup_card_ids]
                db.add(gw_lineup)
            
            db.commit()

    db.refresh(team)
    return _team_to_response(team)



@router.get("/my/gameweek-lineup", response_model=GameweekLineupResponse)
async def get_gameweek_lineup(
    gameweek_id: int = Query(..., description="ID de la jornada"),
    league_id: int = Query(..., description="ID de la liga"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener el equipo congelado/guardado para una jornada específica"""
    team = db.query(Team).filter(
        Team.user_id == current_user.id,
        Team.league_id == league_id
    ).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="No tienes equipo en esta liga")
        
    gw_lineup = db.query(GameweekLineup).filter(
        GameweekLineup.team_id == team.id,
        GameweekLineup.gameweek_id == gameweek_id
    ).first()
    
    if not gw_lineup:
        raise HTTPException(status_code=404, detail="No hay alineación guardada para esta jornada")
        
    return gw_lineup


from pydantic import BaseModel

class GameweekInfo(BaseModel):
    id: int
    number: int
    start_date: datetime
    end_date: datetime
    is_active: bool
    is_finished: bool

@router.get("/active-gameweek", response_model=GameweekInfo)
async def get_active_gameweek(db: Session = Depends(get_db)):
    """Obtener la jornada actualmente activa o la próxima"""
    gw = db.query(Gameweek).filter(Gameweek.is_active == True).first()
    if not gw:
        gw = db.query(Gameweek).filter(Gameweek.is_finished == False).order_by(Gameweek.number).first()
        if not gw:
            raise HTTPException(status_code=404, detail="No hay jornadas configuradas")
    return gw


class GameweekPointsItem(BaseModel):
    gameweek_number: int
    points_earned: float

class GameweekPointsResponse(BaseModel):
    gameweek_points: List[GameweekPointsItem]
    total_points: float


def _get_team_gameweek_points(team_id: int, db: Session) -> dict:
    """Get points per gameweek for a team"""
    lineups = db.query(GameweekLineup).filter(
        GameweekLineup.team_id == team_id
    ).all()
    
    items = []
    total = 0.0
    for lineup in lineups:
        gw = lineup.gameweek
        if gw:
            items.append(GameweekPointsItem(
                gameweek_number=gw.number,
                points_earned=lineup.points_earned or 0.0
            ))
            total += (lineup.points_earned or 0.0)
    
    # Sort by gameweek number
    items.sort(key=lambda x: x.gameweek_number)
    
    return GameweekPointsResponse(
        gameweek_points=items,
        total_points=total
    )


@router.get("/my/gameweek-points", response_model=GameweekPointsResponse)
async def get_my_gameweek_points(
    league_id: int = Query(..., description="ID de la liga"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener los puntos por jornada de mi equipo"""
    team = db.query(Team).filter(
        Team.user_id == current_user.id,
        Team.league_id == league_id
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="No tienes equipo en esta liga")
    
    return _get_team_gameweek_points(team.id, db)


@router.get("/{league_id}/user/{target_user_id}/gameweek-points", response_model=GameweekPointsResponse)
async def get_user_gameweek_points(
    league_id: int,
    target_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener los puntos por jornada del equipo de otro usuario"""
    membership = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")
    
    team = db.query(Team).filter(
        Team.user_id == target_user_id,
        Team.league_id == league_id
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="El usuario no tiene equipo en esta liga")
    
    return _get_team_gameweek_points(team.id, db)


@router.get("/{league_id}/gameweek/{gameweek_number}/breakdown")
async def get_gameweek_lineup_breakdown(
    league_id: int,
    gameweek_number: int,
    user_id: int = Query(None, description="ID del usuario (opcional, por defecto tú)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener el listado exacto de los 11 jugadores y sus puntos en una jornada pasada"""
    target_id = user_id if user_id else current_user.id
    
    # Check league membership
    membership = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")
        
    team = db.query(Team).filter(
        Team.user_id == target_id,
        Team.league_id == league_id
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    gameweek = db.query(Gameweek).filter(Gameweek.number == gameweek_number).first()
    if not gameweek:
        raise HTTPException(status_code=404, detail="Jornada no encontrada")

    gw_lineup = db.query(GameweekLineup).filter(
        GameweekLineup.team_id == team.id,
        GameweekLineup.gameweek_id == gameweek.id
    ).first()

    if not gw_lineup:
        return {"lineup_players": [], "total_points": 0.0, "formation": team.active_formation}

    players_data = []
    for lp in gw_lineup.players:
        if lp.card and lp.card.player:
            player = lp.card.player
            players_data.append({
                "id": lp.card.id,
                "player_id": player.id,
                "player_name": player.name,
                "image_url": player.image_url,
                "position": player.position.value if hasattr(player.position, "value") else player.position,
                "is_legend": player.is_legend,
                "points_earned": lp.points_earned or 0.0
            })

    return {
        "lineup_players": players_data,
        "total_points": sum(p["points_earned"] for p in players_data),
        "formation": gw_lineup.active_formation or team.active_formation
    }


@router.post("/my/release/{card_id}")
async def release_player(
    card_id: int,
    league_id: int = Query(..., description="ID de la liga"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Liberar un jugador — venta instantánea al sistema por el 50% de su valor de mercado.
    La carta se elimina y las monedas se acreditan inmediatamente.
    """
    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="No perteneces a esta liga")

    team = db.query(Team).filter(
        Team.user_id == current_user.id,
        Team.league_id == league_id
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="No tienes equipo en esta liga")

    card = db.query(UserCard).filter(
        UserCard.id == card_id,
        UserCard.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Carta no encontrada en tu inventario")
        
    if card.league_id != league_id:
        if card.team and card.team.league_id == league_id:
            card.league_id = league_id
            db.commit()
        else:
            raise HTTPException(status_code=404, detail="Carta no encontrada en inventario de esta liga")
            
    if not card.is_tradeable:
        raise HTTPException(status_code=400, detail="Esta carta no se puede liberar (intransferible)")
    if card.is_in_lineup:
        raise HTTPException(status_code=400, detail="Retira la carta de la alineación antes de liberarla")

    player = card.player
    release_price = int(player.current_price * 0.50)  # 50% del valor

    # Acreditar monedas
    member.coins += release_price

    # Eliminar carta
    db.delete(card)
    db.commit()

    return {
        "message": f"Has liberado a {player.name} por {release_price:,} monedas",
        "player_name": player.name,
        "price_received": release_price,
        "remaining_coins": member.coins
    }
