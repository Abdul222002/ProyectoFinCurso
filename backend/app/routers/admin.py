"""
Router de Administración — Solo accesible por usuarios con role = admin
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.core.database import get_db
from app.models.models import (
    User, Player, League, LeagueMember, UserCard, Team, UserRole,
    PackOpening, MarketAuction, AuctionSlot, AuctionBid,
    MarketListing, SystemOffer, LeagueInvitation, GameweekLineup
)
from app.routers.auth import get_current_user

router = APIRouter()


# ==========================================
# DEPENDENCY: Require Admin
# ==========================================

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Raises 403 if the current user is not an admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de administrador."
        )
    return current_user


# ==========================================
# STATS
# ==========================================

@router.get("/stats")
async def admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Global platform statistics."""
    total_users = db.query(func.count(User.id)).scalar()
    total_leagues = db.query(func.count(League.id)).scalar()
    total_players = db.query(func.count(Player.id)).scalar()
    total_cards = db.query(func.count(UserCard.id)).scalar()
    total_teams = db.query(func.count(Team.id)).scalar()
    total_coins = db.query(func.coalesce(func.sum(LeagueMember.coins), 0)).scalar()

    return {
        "total_users": total_users,
        "total_leagues": total_leagues,
        "total_players": total_players,
        "total_cards": total_cards,
        "total_teams": total_teams,
        "total_coins_global": total_coins,
    }


# ==========================================
# USERS
# ==========================================

@router.get("/users")
async def admin_list_users(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """List all users with their league memberships."""
    query = db.query(User)
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )
    users = query.order_by(User.id).all()

    result = []
    for u in users:
        league_count = db.query(func.count(LeagueMember.id)).filter(
            LeagueMember.user_id == u.id
        ).scalar()

        memberships = db.query(LeagueMember).filter(LeagueMember.user_id == u.id).all()
        league_names = []
        for m in memberships:
            league = db.query(League).filter(League.id == m.league_id).first()
            if league:
                league_names.append({"id": league.id, "name": league.name})

        result.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role.value if u.role else "free",
            "total_points": u.total_points,
            "level": u.level,
            "league_count": league_count,
            "leagues": league_names,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None,
        })

    return result


@router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Delete a user and cascade to their teams/cards."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta de admin.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    username = user.username
    
    # [↓ SEGURIDAD INTEGRIDAD] 
    # Para borrar un usuario, debemos sacarlo de cada liga en la que está.
    # Esto limpiará sus equipos, cartas, pujas, etc.
    from app.routers.leagues import _remove_user_from_league
    memberships = db.query(LeagueMember).filter(LeagueMember.user_id == user_id).all()
    for m in memberships:
        _remove_user_from_league(user_id, m.league_id, db)
    
    # Limpiar cualquier puja en subastas globales que no se haya limpiado
    db.query(AuctionBid).filter(AuctionBid.user_id == user_id).delete()
    
    db.delete(user)
    db.commit()

    return {"message": f"Usuario @{username} eliminado correctamente."}


# ==========================================
# LEAGUES
# ==========================================

@router.get("/leagues")
async def admin_list_leagues(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """List all leagues."""
    query = db.query(League)
    if search:
        query = query.filter(League.name.ilike(f"%{search}%"))
    leagues = query.order_by(League.id).all()

    result = []
    for lg in leagues:
        owner = db.query(User).filter(User.id == lg.owner_id).first()
        result.append({
            "id": lg.id,
            "name": lg.name,
            "description": lg.description,
            "owner_id": lg.owner_id,
            "owner_username": owner.username if owner else "???",
            "member_count": lg.member_count,
            "max_members": lg.max_members,
            "invite_code": lg.invite_code,
            "created_at": lg.created_at.isoformat() if lg.created_at else None,
        })

    return result


@router.delete("/leagues/{league_id}")
async def admin_delete_league(
    league_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Delete a league and ALL related data (auctions, listings, teams, cards, etc.)."""
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise HTTPException(status_code=404, detail="Liga no encontrada")

    name = league.name

    from app.routers.leagues import _delete_league_completely
    _delete_league_completely(league, db)

    return {"message": f"Liga '{name}' y todos sus datos eliminados correctamente."}


# ==========================================
# PLAYERS (list + edit)
# ==========================================

@router.get("/players")
async def admin_list_players(
    search: Optional[str] = Query(None),
    position: Optional[str] = Query(None, description="GK, DEF, MID, FWD"),
    rarity: Optional[str] = Query(None, description="bronze, silver, gold, legend"),
    team: Optional[str] = Query(None, description="Filter by team name"),
    is_legend: Optional[bool] = Query(None),
    sort_by: Optional[str] = Query("overall_rating", description="overall_rating, name, current_price"),
    sort_dir: Optional[str] = Query("desc", description="asc or desc"),
    limit: int = Query(600, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """List all base players with filters."""
    query = db.query(Player)

    # Filters
    if search:
        query = query.filter(Player.name.ilike(f"%{search}%"))
    if position:
        from app.models.models import Position as PosEnum
        try:
            query = query.filter(Player.position == PosEnum(position))
        except ValueError:
            pass
    if rarity:
        from app.models.models import CardRarity
        try:
            query = query.filter(Player.base_rarity == CardRarity(rarity))
        except ValueError:
            pass
    if team:
        query = query.filter(Player.current_team.ilike(f"%{team}%"))
    if is_legend is not None:
        query = query.filter(Player.is_legend == is_legend)

    total = query.count()

    # Sorting
    sort_col = getattr(Player, sort_by, Player.overall_rating)
    if sort_dir == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    players = query.offset(offset).limit(limit).all()

    # Get unique team names for filter dropdown
    all_teams = db.query(Player.current_team).filter(
        Player.current_team.isnot(None)
    ).distinct().all()
    team_names = sorted([t[0] for t in all_teams if t[0]])

    result = []
    for p in players:
        card_count = db.query(func.count(UserCard.id)).filter(UserCard.player_id == p.id).scalar()
        result.append({
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "position": p.position.value if p.position else "???",
            "nationality": p.nationality,
            "overall_rating": p.overall_rating,
            "potential": p.potential,
            "pace": p.pace,
            "shooting": p.shooting,
            "passing": p.passing,
            "dribbling": p.dribbling,
            "defending": p.defending,
            "physical": p.physical,
            "base_rarity": p.base_rarity.value if p.base_rarity else "bronze",
            "team_name": p.current_team,
            "current_price": p.current_price,
            "target_price": p.target_price,
            "image_url": p.image_url,
            "is_legend": p.is_legend,
            "cards_in_circulation": card_count,
        })

    return {"total": total, "players": result, "available_teams": team_names}


@router.put("/players/{player_id}")
async def admin_update_player(
    player_id: int,
    data: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Update a player's data (name, stats, image, etc.)."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # Updatable fields
    allowed_fields = [
        "name", "age", "nationality", "overall_rating", "potential",
        "pace", "shooting", "passing", "dribbling", "defending", "physical",
        "image_url", "current_price", "target_price", "is_legend", "current_team"
    ]

    for field in allowed_fields:
        if field in data:
            setattr(player, field, data[field])

    # Handle position enum
    if "position" in data:
        from app.models.models import Position
        try:
            player.position = Position(data["position"])
        except ValueError:
            pass

    # Handle rarity enum
    if "base_rarity" in data:
        from app.models.models import CardRarity
        try:
            player.base_rarity = CardRarity(data["base_rarity"])
        except ValueError:
            pass

    db.commit()
    db.refresh(player)

    return {
        "message": f"Jugador '{player.name}' actualizado correctamente.",
        "player": {
            "id": player.id,
            "name": player.name,
            "overall_rating": player.overall_rating,
            "image_url": player.image_url,
        }
    }


# ==========================================
# TEAMS
# ==========================================

@router.get("/teams")
async def admin_list_teams(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """List all teams."""
    query = db.query(Team)
    if search:
        query = query.filter(Team.name.ilike(f"%{search}%"))

    teams = query.order_by(Team.id).all()
    result = []
    for t in teams:
        owner = db.query(User).filter(User.id == t.user_id).first()
        league = db.query(League).filter(League.id == t.league_id).first()
        card_count = db.query(func.count(UserCard.id)).filter(UserCard.team_id == t.id).scalar()

        result.append({
            "id": t.id,
            "name": t.name,
            "owner_username": owner.username if owner else "???",
            "league_name": league.name if league else "???",
            "league_id": t.league_id,
            "overall_rating": round(t.overall_rating, 1) if t.overall_rating else 0,
            "formation": t.active_formation,
            "player_count": card_count,
            "arena_rating": t.arena_rating,
            "arena_record": f"{t.arena_wins}W-{t.arena_draws}D-{t.arena_losses}L",
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })

    return result


# ==========================================
# USER COINS PER LEAGUE
# ==========================================

@router.get("/users/{user_id}/league-coins")
async def admin_get_user_league_coins(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get a user's coin balance in each league they belong to."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    memberships = db.query(LeagueMember).filter(LeagueMember.user_id == user_id).all()
    result = []
    for m in memberships:
        league = db.query(League).filter(League.id == m.league_id).first()
        result.append({
            "league_id": m.league_id,
            "league_name": league.name if league else "???",
            "coins": m.coins or 0,
            "locked_coins": m.locked_coins or 0,
            "free_coins": (m.coins or 0) - (m.locked_coins or 0),
            "league_points": m.league_points or 0,
        })

    return {
        "user_id": user_id,
        "username": user.username,
        "leagues": result,
    }


@router.put("/users/{user_id}/league-coins")
async def admin_update_user_league_coins(
    user_id: int,
    data: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Update a user's coins. Accepts:
      - league_id + coins : update coins in that specific league
      - global_coins      : update the user's global coin balance
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Update per-league coins
    league_id = data.get("league_id")
    new_coins = data.get("coins")
    new_locked = data.get("locked_coins")
    reconcile = data.get("reconcile", False)

    if league_id is not None:
        membership = db.query(LeagueMember).filter(
            LeagueMember.user_id == user_id,
            LeagueMember.league_id == league_id
        ).first()
        if not membership:
            raise HTTPException(status_code=404, detail="El usuario no pertenece a esa liga")
        
        if new_coins is not None:
            membership.coins = int(new_coins)
        
        if new_locked is not None:
            membership.locked_coins = int(new_locked)

        if reconcile:
            from app.routers.market import reconcile_member_locked_coins
            reconcile_member_locked_coins(db, membership)

    db.commit()

    return {"message": f"Economía de @{user.username} sincronizada correctamente."}

