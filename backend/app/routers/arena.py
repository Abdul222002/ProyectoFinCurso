"""
Router de la Arena PvP — Simular, Historial, Leaderboard
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import random

from app.core.database import get_db
from app.models.models import User, Team, ArenaBattle
from app.schemas.arena import ArenaMatchResponse, LeaderboardEntry, BattleHistoryResponse
from app.routers.auth import get_current_user

router = APIRouter()


def _simulate_match(team1_ovr: float, team2_ovr: float) -> tuple:
    """
    Simular un partido basado en OVR.
    Equipos con mayor OVR tienen más probabilidad de ganar.
    """
    # Factor de ventaja basado en diferencia de OVR
    diff = team1_ovr - team2_ovr
    team1_win_prob = 0.5 + (diff / 100)  # ej: +10 OVR = 60% prob
    team1_win_prob = max(0.15, min(0.85, team1_win_prob))  # Clamped 15%-85%

    # Generar goles (Poisson-like simplificado)
    avg_goals = 2.5
    team1_goals = 0
    team2_goals = 0

    for _ in range(int(avg_goals * 2)):
        if random.random() < (team1_win_prob * 0.6):
            team1_goals += 1
        if random.random() < ((1 - team1_win_prob) * 0.6):
            team2_goals += 1

    # Cap de goles razonables
    team1_goals = min(team1_goals, 5)
    team2_goals = min(team2_goals, 5)

    return team1_goals, team2_goals


def _calculate_rating_change(my_rating: int, opp_rating: int, won: bool, draw: bool) -> int:
    """ELO simplificado"""
    expected = 1 / (1 + 10 ** ((opp_rating - my_rating) / 400))
    if won:
        actual = 1
    elif draw:
        actual = 0.5
    else:
        actual = 0
    k = 32
    return int(k * (actual - expected))


@router.post("/simulate", response_model=ArenaMatchResponse)
async def simulate_pvp(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Simular un partido PvP contra un oponente aleatorio"""
    my_team = db.query(Team).filter(Team.user_id == current_user.id).first()
    if not my_team:
        raise HTTPException(status_code=400, detail="Necesitas crear un equipo primero")

    # Buscar oponente aleatorio (excluir al usuario actual)
    opponents = db.query(Team).filter(Team.user_id != current_user.id).all()

    if not opponents:
        # Si no hay oponentes, crear uno fantasma
        opp_team_name = "CPU FC"
        opp_ovr = random.uniform(60, 90)
        opp_rating = 1000

        team1_goals, team2_goals = _simulate_match(my_team.overall_rating, opp_ovr)

        won = team1_goals > team2_goals
        draw = team1_goals == team2_goals
        rating_change = _calculate_rating_change(my_team.arena_rating, opp_rating, won, draw)

        # Actualizar stats
        my_team.arena_rating += rating_change
        if won:
            my_team.arena_wins += 1
            result = "victory"
        elif draw:
            my_team.arena_draws += 1
            result = "draw"
        else:
            my_team.arena_losses += 1
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
            rating_change=rating_change,
            simulated_at=__import__('datetime').datetime.utcnow()
        )

    # Matchmaking: elegir oponente cercano en rating
    opponents.sort(key=lambda t: abs(t.arena_rating - my_team.arena_rating))
    opp_team = opponents[0] if len(opponents) <= 3 else random.choice(opponents[:5])

    team1_goals, team2_goals = _simulate_match(my_team.overall_rating, opp_team.overall_rating)

    won = team1_goals > team2_goals
    draw = team1_goals == team2_goals
    lost = team1_goals < team2_goals

    winner_id = None
    if won:
        winner_id = my_team.id
    elif lost:
        winner_id = opp_team.id

    # Crear registro
    battle = ArenaBattle(
        team1_id=my_team.id,
        team2_id=opp_team.id,
        team1_score=team1_goals,
        team2_score=team2_goals,
        winner_id=winner_id
    )
    db.add(battle)

    # Rating changes
    my_change = _calculate_rating_change(my_team.arena_rating, opp_team.arena_rating, won, draw)
    opp_change = _calculate_rating_change(opp_team.arena_rating, my_team.arena_rating, lost, draw)

    my_team.arena_rating += my_change
    opp_team.arena_rating += opp_change

    if won:
        my_team.arena_wins += 1
        opp_team.arena_losses += 1
        result = "victory"
    elif draw:
        my_team.arena_draws += 1
        opp_team.arena_draws += 1
        result = "draw"
    else:
        my_team.arena_losses += 1
        opp_team.arena_wins += 1
        result = "defeat"

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
        rating_change=my_change,
        simulated_at=battle.simulated_at
    )


@router.get("/history", response_model=List[BattleHistoryResponse])
async def battle_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Historial de batallas del usuario"""
    my_team = db.query(Team).filter(Team.user_id == current_user.id).first()
    if not my_team:
        return []

    battles = db.query(ArenaBattle).filter(
        (ArenaBattle.team1_id == my_team.id) | (ArenaBattle.team2_id == my_team.id)
    ).order_by(desc(ArenaBattle.simulated_at)).limit(limit).all()

    result = []
    for b in battles:
        is_team1 = b.team1_id == my_team.id
        opp = b.team2 if is_team1 else b.team1
        my_score = b.team1_score if is_team1 else b.team2_score
        opp_score = b.team2_score if is_team1 else b.team1_score

        if b.winner_id == my_team.id:
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
            simulated_at=b.simulated_at
        ))

    return result


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def leaderboard(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Ranking global por arena_rating"""
    teams = db.query(Team).order_by(desc(Team.arena_rating)).limit(limit).all()

    return [
        LeaderboardEntry(
            rank=i + 1,
            team_id=t.id,
            team_name=t.name,
            username=t.user.username,
            arena_rating=t.arena_rating,
            arena_wins=t.arena_wins,
            arena_losses=t.arena_losses,
            arena_draws=t.arena_draws,
            overall_rating=t.overall_rating
        )
        for i, t in enumerate(teams)
    ]
