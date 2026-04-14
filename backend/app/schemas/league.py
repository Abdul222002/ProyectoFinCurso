"""
Pydantic Schemas para Ligas e Invitaciones
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==========================================
# ASSIGNED PLAYERS (para animación de bienvenida)
# ==========================================

class AssignedPlayerCard(BaseModel):
    """Datos de cada jugador asignado al unirse a una liga"""
    id: int                    # UserCard.id
    player_id: int
    player_name: str
    position: str
    overall_rating: float
    base_rarity: str
    image_url: Optional[str] = None
    is_in_lineup: bool

    class Config:
        from_attributes = True


class InvitationStatusEnum(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


# ==========================================
# LEAGUE
# ==========================================

class LeagueCreate(BaseModel):
    """Crear una liga nueva"""
    name: str = Field(min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    max_members: int = Field(default=10, ge=2, le=50)
    is_public: bool = False


class LeagueUpdate(BaseModel):
    """Actualizar datos de una liga"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    max_members: Optional[int] = Field(None, ge=2, le=50)
    is_public: Optional[bool] = None


class LeagueMemberResponse(BaseModel):
    """Un miembro dentro de una liga"""
    id: int
    user_id: int
    username: str
    league_points: int
    coins: int
    locked_coins: int
    is_admin: bool
    joined_at: datetime

    class Config:
        from_attributes = True


class LeagueResponse(BaseModel):
    """Respuesta completa de una liga"""
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    owner_username: str
    max_members: int
    member_count: int
    is_public: bool
    invite_code: str
    created_at: datetime

    class Config:
        from_attributes = True


class LeagueListResponse(BaseModel):
    """Respuesta resumida para listados"""
    id: int
    name: str
    owner_username: str
    member_count: int
    max_members: int
    is_public: bool

    class Config:
        from_attributes = True


class LeagueJoinResponse(BaseModel):
    """Respuesta al crear o unirse a una liga — incluye jugadores asignados."""
    id: int
    name: str
    owner_username: str
    member_count: int
    max_members: int
    is_public: bool
    assigned_players: List[AssignedPlayerCard] = []

    class Config:
        from_attributes = True


class LeagueDetailResponse(LeagueResponse):
    """Liga con miembros (clasificación)"""
    members: List[LeagueMemberResponse] = []


# ==========================================
# INVITATIONS
# ==========================================

class InvitationCreate(BaseModel):
    """Crear invitación — por username o email"""
    username: Optional[str] = None
    email: Optional[str] = None


class InvitationResponse(BaseModel):
    """Respuesta de invitación"""
    id: int
    league_id: int
    league_name: str
    invited_by_username: str
    invited_email: Optional[str]
    invited_username: Optional[str]
    status: InvitationStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True
