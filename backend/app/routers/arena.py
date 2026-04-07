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
    """ELO dinámico con K escalable según diferencia de nivel"""
    expected = 1 / (1 + 10 ** ((opp_rating - my_rating) / 400))
    if won:
        actual = 1
    elif draw:
        actual = 0.5
    else:
        actual = 0
        
    # K base más alta para más movimiento
    k = 40
    
    # Aumentar K si el jugador de menor ELO gana al de mayor ELO
    if won and my_rating < opp_rating:
        k += 15
    # Reducir K si el jugador de alto ELO pierde o gana contra uno muy inferior
    elif won and my_rating > (opp_rating + 100):
        k -= 10
        
    return int(k * (actual - expected))


def _reset_tickets_if_needed(user: User, db: Session):
    """Resetea los tickets diarios si es un nuevo día"""
    now = datetime.utcnow()
    # Si last_tickets_reset no tiene valor o es de otro día natural
    if not user.last_tickets_reset or user.last_tickets_reset.date() < now.date():
        user.arena_tickets = 5
        user.last_tickets_reset = now
        db.commit()


@router.get("/status", response_model=ArenaStatusResponse)
async def get_arena_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Devuelve el estado mensual (ELO, tickets) del jugador"""
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
    """Simular un partido PvP contra un oponente de ELO similar"""
    _reset_tickets_if_needed(current_user, db)
    
    if current_user.arena_tickets <= 0:
        raise HTTPException(status_code=400, detail="No te quedan tickets de arena hoy")

    my_team = db.query(Team).filter(Team.id == req.team_id, Team.user_id == current_user.id).first()
    if not my_team:
        raise HTTPException(status_code=400, detail="Necesitas crear un equipo primero")

    # Buscar oponente aleatorio (excluir al usuario actual)
    opponents = db.query(Team).filter(Team.user_id != current_user.id).all()

    # Multiplicador del sistema global
    global_k = 32

    # Consumir ticket
    current_user.arena_tickets -= 1

    if not opponents:
        # Si no hay oponentes, crear uno fantasma adaptativo
        opp_team_name = "CPU FC"
        # Escalar con el nivel del jugador
        opp_ovr = max(60.0, min(95.0, my_team.overall_rating + random.uniform(-5, 5)))
        opp_rating = max(500, my_team.arena_rating + random.randint(-40, 40))
        opp_global_elo = max(500, current_user.global_elo + random.randint(-40, 40))

        team1_goals, team2_goals = _simulate_match(my_team.overall_rating, opp_ovr)

        won = team1_goals > team2_goals
        draw = team1_goals == team2_goals
        
        # ELO changes
        rating_change = _calculate_rating_change(my_team.arena_rating, opp_rating, won, draw)
        global_change = _calculate_rating_change(current_user.global_elo, opp_global_elo, won, draw)

        # Actualizar stats
        my_team.arena_rating += rating_change
        current_user.global_elo += global_change
        
        coins_rewarded = 0
        if won:
            my_team.arena_wins += 1
            result = "victory"
            # Recompensa
            coins_rewarded = 5000000
            league_member = db.query(LeagueMember).filter(
                LeagueMember.league_id == my_team.league_id,
                LeagueMember.user_id == current_user.id
            ).first()
            if league_member:
                league_member.coins += coins_rewarded

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
            global_rating_change=global_change,
            coins_rewarded=coins_rewarded,
            simulated_at=datetime.utcnow()
        )

    # Matchmaking: elegir oponente cercano en global_elo y overall_rating combinados (aprox)
    # Por simplicidad ahora, combinamos diferencia de ELO global y diferencia de team OVR
    def match_score(t: Team):
        elo_diff = abs(t.user.global_elo - current_user.global_elo)
        ovr_diff = abs(t.overall_rating - my_team.overall_rating) * 10  # Peso al OVR
        return elo_diff + ovr_diff

    opponents.sort(key=match_score)
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
    
    my_global_change = _calculate_rating_change(current_user.global_elo, opp_team.user.global_elo, won, draw)
    opp_global_change = _calculate_rating_change(opp_team.user.global_elo, current_user.global_elo, lost, draw)

    my_team.arena_rating += my_change
    opp_team.arena_rating += opp_change
    
    current_user.global_elo += my_global_change
    opp_team.user.global_elo += opp_global_change

    coins_rewarded = 0
    if won:
        my_team.arena_wins += 1
        opp_team.arena_losses += 1
        result = "victory"
        coins_rewarded = 5000000
        league_member = db.query(LeagueMember).filter(
            LeagueMember.league_id == my_team.league_id,
            LeagueMember.user_id == current_user.id
        ).first()
        if league_member:
            league_member.coins += coins_rewarded
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
        global_rating_change=my_global_change,
        coins_rewarded=coins_rewarded,
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
async def get_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ranking global por arena_rating (un solo equipo por usuario, el mejor)"""
    from sqlalchemy import func
    
    # 1. Obtener el máximo arena_rating por usuario
    subq_max = db.query(
        Team.user_id,
        func.max(Team.arena_rating).label('max_rating')
    ).filter(
        Team.arena_rating.isnot(None)
    ).group_by(Team.user_id).subquery()

    # 2. De los equipos con ese rating máximo, elegir solo uno (el de ID más bajo)
    subq_id = db.query(
        func.min(Team.id).label('target_id')
    ).join(
        subq_max,
        (Team.user_id == subq_max.c.user_id) & (Team.arena_rating == subq_max.c.max_rating)
    ).group_by(Team.user_id).subquery()

    # 3. Obtener los datos completos de esos equipos únicos
    teams = db.query(Team).filter(
        Team.id.in_(subq_id)
    ).order_by(Team.arena_rating.desc()
    ).limit(limit).all()

    result = []
    for i, team in enumerate(teams, 1):
        result.append(LeaderboardEntry(
            rank=i,
            team_id=team.id,
            team_name=team.name,
            username=team.user.username,
            arena_rating=team.arena_rating or 1000,
            arena_wins=team.arena_wins or 0,
            arena_losses=team.arena_losses or 0,
            arena_draws=team.arena_draws or 0,
            overall_rating=team.overall_rating or 0.0
        ))
    return result
