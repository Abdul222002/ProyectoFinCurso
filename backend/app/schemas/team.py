"""
Pydantic Schemas para Equipos
"""

from pydantic import BaseModel, Field, model_validator
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

    @model_validator(mode="after")
    def check_formation(self):
        from app.services.lineup_validator import VALID_FORMATIONS
        if self.formation not in VALID_FORMATIONS:
            raise ValueError(f"Formación '{self.formation}' no válida. Opciones: {', '.join(VALID_FORMATIONS.keys())}")
        return self


class TeamUpdate(BaseModel):
    """Actualizar equipo"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    formation: Optional[str] = Field(None, max_length=10)
    shield_url: Optional[str] = Field(None, max_length=500)
    kit_color_primary: Optional[str] = Field(None, max_length=7)
    kit_color_secondary: Optional[str] = Field(None, max_length=7)

    @model_validator(mode="after")
    def check_formation(self):
        from app.services.lineup_validator import VALID_FORMATIONS
        if self.formation and self.formation not in VALID_FORMATIONS:
            raise ValueError(f"Formación '{self.formation}' no válida. Opciones: {', '.join(VALID_FORMATIONS.keys())}")
        return self


class CardInLineup(BaseModel):
    """Una carta en la alineación"""
    id: int
    player_id: int
    player_name: str
    position: str
    current_overall: int
    is_in_lineup: bool
    protected_value: int = 0
    current_team: Optional[str] = None
    nationality: Optional[str] = None
    pace: int = 50
    shooting: int = 50
    passing: int = 50
    dribbling: int = 50
    defending: int = 50
    physical: int = 50
    
    # Icon attributes
    is_legend: Optional[bool] = False
    scoring_profile: Optional[str] = None
    min_fantasy: Optional[int] = None
    max_fantasy: Optional[int] = None

    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    """Respuesta completa de equipo"""
    id: int
    name: Optional[str] = "Equipo"
    user_id: Optional[int] = None
    overall_rating: float
    total_fantasy_points: Optional[int] = 0
    arena_wins: Optional[int] = 0
    arena_losses: Optional[int] = 0
    arena_draws: Optional[int] = 0
    arena_rating: Optional[int] = 0
    active_formation: Optional[str] = "4-4-2"
    kit_color_primary: Optional[str] = "#FF0000"
    kit_color_secondary: Optional[str] = "#FFFFFF"
    league_id: int
    team_value: int = 0
    players: List[CardInLineup] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SetLineupRequest(BaseModel):
    """Establecer alineación — IDs de UserCard"""
    lineup_card_ids: List[int] = Field(default=[], max_length=11)


class GameweekLineupResponse(BaseModel):
    """Respuesta de una alineación guardada para una jornada"""
    id: int
    team_id: int
    gameweek_id: int
    player_ids: List[int]  # Se transforma de la relación en el validador
    active_formation: str
    points_earned: float
    created_at: datetime
    
    @model_validator(mode="before")
    @classmethod
    def extract_player_ids(cls, data):
        # Si data es un objeto SQLAlchemy, extraemos los IDs de la relación 'players'
        if hasattr(data, "players") and data.players is not None:
            # GameweekLineup tiene relación 'players' -> List[GameweekLineupPlayer]
            data.player_ids = [p.card_id for p in data.players]
        return data

    class Config:
        from_attributes = True
