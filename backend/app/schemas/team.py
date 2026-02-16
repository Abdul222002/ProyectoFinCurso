"""
Pydantic Schemas para Equipos
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==========================================
# TEAM
# ==========================================

class TeamCreate(BaseModel):
    """Crear equipo"""
    name: str = Field(min_length=3, max_length=100)
    formation: str = Field(default="4-4-2", max_length=10)
    kit_color_primary: str = Field(default="#FF0000", max_length=7)
    kit_color_secondary: str = Field(default="#FFFFFF", max_length=7)


class TeamUpdate(BaseModel):
    """Actualizar equipo"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    formation: Optional[str] = Field(None, max_length=10)
    kit_color_primary: Optional[str] = Field(None, max_length=7)
    kit_color_secondary: Optional[str] = Field(None, max_length=7)


class CardInLineup(BaseModel):
    """Una carta en la alineación"""
    id: int
    player_id: int
    player_name: str
    position: str
    current_overall: int
    is_in_lineup: bool

    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    """Respuesta completa de equipo"""
    id: int
    name: str
    user_id: int
    overall_rating: float
    total_fantasy_points: int
    arena_wins: int
    arena_losses: int
    arena_draws: int
    arena_rating: int
    active_formation: str
    kit_color_primary: str
    kit_color_secondary: str
    players: List[CardInLineup] = []
    created_at: datetime

    class Config:
        from_attributes = True


class SetLineupRequest(BaseModel):
    """Establecer alineación — IDs de UserCard"""
    lineup_card_ids: List[int] = Field(..., min_length=1, max_length=11)
