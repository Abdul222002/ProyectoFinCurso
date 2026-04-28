"""
Router de la Arena PvP — Simular, Historial, Leaderboard
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import random

from app.core.database import get_db
from app.models.models import User, Team, ArenaBattle, LeagueMember
from app.schemas.arena import ArenaMatchResponse, LeaderboardEntry, BattleHistoryResponse, ArenaStatusResponse
from app.routers.auth import get_current_user
from datetime import datetime, timedelta

router = APIRouter()


def _simulate_match(team1_ovr: float, team2_ovr: float) -> tuple:
    """
    Simular un partido basado en OVR.
    Equipos con mayor OVR tienen más probabilidad de ganar.
    """
    diff = team1_ovr - team2_ovr
    team1_win_prob = 0.5 + (diff / 100)
    team1_win_prob = max(0.15, min(0.85, team1_win_prob))

    avg_goals = 2.5
    team1_goals = 0
    team2_goals = 0

    for _ in range(int(avg_goals * 2)):
        if random.random() < (team1_win_prob * 0.6):
            team1_goals += 1
        if random.random() < ((1 - team1_win_prob) * 0.6):
            team2_goals += 1

    team1_goals = min(team1_goals, 5)
    team2_goals = min(team2_goals, 5)

    return team1_goals, team2_goals


def _calculate_elo_change(my_elo: int, opp_elo: int, won: bool, draw: bool) -> int:
    """ELO dinámico con K escalable según diferencia de nivel"""
    expected = 1 / (1 + 10 ** ((opp_elo - my_elo) / 400))
    if won:
        actual = 1
    elif draw:
        actual = 0.5
    else:
        actual = 0

    k = 40
    if won and my_elo < opp_elo:
        k += 15
    elif won and my_elo > (opp_elo + 100):
        k -= 10

    return int(k * (actual - expected))


def _reset_tickets_if_needed(user: User, db: Session):
    """Resetea los tickets diarios si es un nuevo día"""
    now = datetime.utcnow()
    if not user.last_tickets_reset or user.last_tickets_reset.date() < now.date():
        user.arena_tickets = 5
        user.last_tickets_reset = now
        db.commit()


@router.get("/status", response_model=ArenaStatusResponse)
async def get_arena_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Devuelve el estado de la Arena (ELO global, tickets)"""
    _reset_tickets_if_needed(current_user, db)
    return ArenaStatusResponse(
        global_elo=current_user.global_elo,
        arena_tickets=current_user.arena_tickets,
        last_tickets_reset=current_user.last_tickets_reset
    )


class SimulateRequest(__import__('pydantic').BaseModel):
    team_id: int


@router.post("/simulate", response_model=ArenaMatchResponse)
async def simulate_pvp(
    req: SimulateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Simular un partido PvP. ELO siempre del usuario (global_elo), no del equipo."""
    _reset_tickets_if_needed(current_user, db)

    if current_user.arena_tickets <= 0:
        raise HTTPException(status_code=400, detail="No te quedan tickets de arena hoy")

    my_team = db.query(Team).filter(Team.id == req.team_id, Team.user_id == current_user.id).first()
    if not my_team:
        raise HTTPException(status_code=400, detail="Necesitas crear un equipo primero")

    # Consumir ticket
    current_user.arena_tickets -= 1

    # Buscar oponente (excluir al usuario actual)
    opponents = db.query(Team).filter(Team.user_id != current_user.id).all()

    if not opponents:
        # Oponente fantasma CPU adaptativo
        opp_team_name = "CPU FC"
        opp_ovr = max(60.0, min(95.0, my_team.overall_rating + random.uniform(-5, 5)))
        opp_elo = max(500, current_user.global_elo + random.randint(-40, 40))

        team1_goals, team2_goals = _simulate_match(my_team.overall_rating, opp_ovr)
        won = team1_goals > team2_goals
        draw = team1_goals == team2_goals

        # Solo actualizar global_elo del usuario
        elo_change = _calculate_elo_change(current_user.global_elo, opp_elo, won, draw)
        current_user.global_elo = max(100, current_user.global_elo + elo_change)

        coins_rewarded = 0
        if won:
            current_user.arena_wins += 1
            result = "victory"
            coins_rewarded = 5000000
            league_member = db.query(LeagueMember).filter(
                LeagueMember.league_id == my_team.league_id,
                LeagueMember.user_id == current_user.id
            ).first()
            if league_member:
                league_member.coins += coins_rewarded
        elif draw:
            current_user.arena_draws += 1
            result = "draw"
        else:
            current_user.arena_losses += 1
            result = "defeat"

        db.commit()

        return ArenaMatchResponse(
            id=0,
            team1_name=my_team.name,
            team1_ovr=my_team.overall_rating,
            team1_score=team1_goals,
            team2_name=opp_team_name,
            team2_ovr=opp_ovr,
            team2_score=team2_goals,
            winner_name=my_team.name if won else (opp_team_name if not draw else None),
            result=result,
            rating_change=elo_change,
            global_rating_change=elo_change,
            coins_rewarded=coins_rewarded,
            simulated_at=datetime.utcnow()
        )

    # Matchmaking: oponente más cercano en global_elo y OVR
    def match_score(t: Team):
        elo_diff = abs(t.user.global_elo - current_user.global_elo)
        ovr_diff = abs(t.overall_rating - my_team.overall_rating) * 10
        return elo_diff + ovr_diff

    opponents.sort(key=match_score)
    opp_team = opponents[0] if len(opponents) <= 3 else random.choice(opponents[:5])
    opp_user = opp_team.user

    team1_goals, team2_goals = _simulate_match(my_team.overall_rating, opp_team.overall_rating)
    won = team1_goals > team2_goals
    draw = team1_goals == team2_goals
    lost = team1_goals < team2_goals

    winner_id = None
    if won:
        winner_id = my_team.id
    elif lost:
        winner_id = opp_team.id

    # Calcular cambios de ELO (solo global_elo del usuario)
    my_elo_change = _calculate_elo_change(current_user.global_elo, opp_user.global_elo, won, draw)
    opp_elo_change = _calculate_elo_change(opp_user.global_elo, current_user.global_elo, lost, draw)

    # Actualizar ELOs globales (con piso en 100)
    current_user.global_elo = max(100, current_user.global_elo + my_elo_change)
    opp_user.global_elo = max(100, opp_user.global_elo + opp_elo_change)

    # Registrar W/D/L a nivel de usuario
    if won:
        current_user.arena_wins += 1
        opp_user.arena_losses += 1
        result = "victory"
    elif draw:
        current_user.arena_draws += 1
        opp_user.arena_draws += 1
        result = "draw"
    else:
        current_user.arena_losses += 1
        opp_user.arena_wins += 1
        result = "defeat"

    # Recompensa de monedas solo en victoria
    coins_rewarded = 0
    if won:
        coins_rewarded = 5000000
        league_member = db.query(LeagueMember).filter(
            LeagueMember.league_id == my_team.league_id,
            LeagueMember.user_id == current_user.id
        ).first()
        if league_member:
            league_member.coins += coins_rewarded

    # Guardar batalla en historial
    battle = ArenaBattle(
        team1_id=my_team.id,
        team2_id=opp_team.id,
        team1_score=team1_goals,
        team2_score=team2_goals,
        winner_id=winner_id,
        rating_change=my_elo_change,
        global_rating_change=my_elo_change,
        team1_rating_change=my_elo_change,
        team2_rating_change=opp_elo_change,
        team1_global_change=my_elo_change,
        team2_global_change=opp_elo_change,
    )
    db.add(battle)
    db.commit()
    db.refresh(battle)

    return ArenaMatchResponse(
        id=battle.id,
        team1_name=my_team.name,
        team1_ovr=my_team.overall_rating,
        team1_score=team1_goals,
        team2_name=opp_team.name,
        team2_ovr=opp_team.overall_rating,
        team2_score=team2_goals,
        winner_name=my_team.name if won else (opp_team.name if lost else None),
        result=result,
        rating_change=my_elo_change,
        global_rating_change=my_elo_change,
        coins_rewarded=coins_rewarded,
        simulated_at=battle.simulated_at
    )


@router.get("/history", response_model=List[BattleHistoryResponse])
async def battle_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Historial de batallas del usuario (cualquier equipo suyo)"""
    # Obtener todos los teams del usuario
    my_team_ids = [t.id for t in db.query(Team).filter(Team.user_id == current_user.id).all()]
    if not my_team_ids:
        return []

    battles = db.query(ArenaBattle).filter(
        (ArenaBattle.team1_id.in_(my_team_ids)) | (ArenaBattle.team2_id.in_(my_team_ids))
    ).order_by(desc(ArenaBattle.simulated_at)).limit(limit).all()

    result = []
    for b in battles:
        is_team1 = b.team1_id in my_team_ids
        opp = b.team2 if is_team1 else b.team1
        my_score = b.team1_score if is_team1 else b.team2_score
        opp_score = b.team2_score if is_team1 else b.team1_score

        if is_team1:
            elo_delta = b.team1_global_change or b.rating_change or 0
        else:
            elo_delta = b.team2_global_change or -(b.rating_change or 0)

        if b.winner_id in my_team_ids:
            match_result = "victory"
        elif b.winner_id is None:
            match_result = "draw"
        else:
            match_result = "defeat"

        result.append(BattleHistoryResponse(
            id=b.id,
            opponent_name=opp.name,
            my_score=my_score,
            opponent_score=opp_score,
            result=match_result,
            rating_change=elo_delta,
            global_rating_change=elo_delta,
            simulated_at=b.simulated_at
        ))

    return result


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ranking global por global_elo del usuario. Un usuario = una entrada."""
    users = db.query(User).order_by(User.global_elo.desc()).limit(limit).all()

    result = []
    for i, u in enumerate(users, 1):
        # Obtener el mejor equipo del usuario (mayor OVR) para mostrar nombre/escudo
        best_team = db.query(Team).filter(Team.user_id == u.id).order_by(
            Team.overall_rating.desc()
        ).first()

        result.append(LeaderboardEntry(
            rank=i,
            user_id=u.id,
            team_name=best_team.name if best_team else f"{u.username} FC",
            username=u.username,
            arena_rating=u.global_elo,           # <- siempre global_elo
            arena_wins=u.arena_wins or 0,
            arena_losses=u.arena_losses or 0,
            arena_draws=u.arena_draws or 0,
            overall_rating=best_team.overall_rating if best_team else 0.0
        ))
    return result
