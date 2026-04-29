"""
Pydantic Schemas para la Arena PvP
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ArenaMatchResponse(BaseModel):
    """Resultado de una simulación PvP"""
    id: int
    team1_name: str
    team1_ovr: float
    team1_score: int
    team2_name: str
    team2_ovr: float
    team2_score: int
    winner_name: Optional[str]
    result: str  # "victory", "defeat", "draw"
    rating_change: int
    global_rating_change: int
    coins_rewarded: int
    simulated_at: datetime

    class Config:
        from_attributes = True


class ArenaStatusResponse(BaseModel):
    """Estado del jugador en la Arena"""
    global_elo: int
    arena_tickets: int
    last_tickets_reset: datetime


class LeaderboardEntry(BaseModel):
    """Entrada del ranking"""
    rank: int
    user_id: int
    team_id: Optional[int]      # ID del equipo con mayor OVR del usuario — usado por el frontend como key y para detectar "Tú"
    team_name: str
    username: str
    arena_rating: int      # = user.global_elo (nombre mantenido para compatibilidad con frontend)
    arena_wins: int
    arena_losses: int
    arena_draws: int
    overall_rating: float

    class Config:
        from_attributes = True


class BattleHistoryResponse(BaseModel):
    """Historial de batalla simplificado"""
    id: int
    opponent_name: str
    my_score: int
    opponent_score: int
    result: str  # "victory", "defeat", "draw"
    rating_change: int
    global_rating_change: int
    simulated_at: datetime

    class Config:
        from_attributes = True
