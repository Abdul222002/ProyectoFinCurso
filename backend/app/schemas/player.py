"""
Pydantic Schemas para Jugadores
Validación de entrada/salida de datos
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class PositionEnum(str, Enum):
    """Posiciones disponibles"""
    GK = "GK"
    DEF = "DEF"
    MID = "MID"
    FWD = "FWD"


class CardRarityEnum(str, Enum):
    """Rareza de cartas"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    LEGEND = "legend"


class PlayerStats(BaseModel):
    """Estadísticas FIFA-style de un jugador"""
    pace: int = Field(ge=0, le=99)
    shooting: int = Field(ge=0, le=99)
    passing: int = Field(ge=0, le=99)
    dribbling: int = Field(ge=0, le=99)
    defending: int = Field(ge=0, le=99)
    physical: int = Field(ge=0, le=99)


class PlayerBase(BaseModel):
    """Schema base de jugador"""
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=16, le=45)
    position: PositionEnum
    nationality: str = Field(min_length=1, max_length=50)
    overall_rating: int = Field(ge=50, le=99)
    potential: int = Field(ge=50, le=99)
    
    class Config:
        from_attributes = True


class PlayerCreate(PlayerBase):
    """Schema para crear un jugador"""
    pace: int = Field(default=50, ge=0, le=99)
    shooting: int = Field(default=50, ge=0, le=99)
    passing: int = Field(default=50, ge=0, le=99)
    dribbling: int = Field(default=50, ge=0, le=99)
    defending: int = Field(default=50, ge=0, le=99)
    physical: int = Field(default=50, ge=0, le=99)
    is_legend: bool = False
    base_rarity: CardRarityEnum = CardRarityEnum.BRONZE
    current_team: Optional[str] = None
    sportmonks_id: Optional[int] = None
    image_url: Optional[str] = None


class PlayerResponse(PlayerBase):
    """Schema de respuesta de jugador"""
    id: int
    stats: PlayerStats
    is_legend: bool
    base_rarity: CardRarityEnum
    base_market_value: float
    current_team: Optional[str]
    image_url: Optional[str]
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, player):
        """Convierte modelo ORM a schema"""
        return cls(
            id=player.id,
            name=player.name,
            age=player.age,
            position=player.position,
            nationality=player.nationality,
            overall_rating=player.overall_rating,
            potential=player.potential,
            stats=PlayerStats(
                pace=player.pace,
                shooting=player.shooting,
                passing=player.passing,
                dribbling=player.dribbling,
                defending=player.defending,
                physical=player.physical
            ),
            is_legend=player.is_legend,
            base_rarity=player.base_rarity,
            base_market_value=player.base_market_value,
            current_team=player.current_team,
            image_url=player.image_url
        )


class PlayerUpdate(BaseModel):
    """Schema para actualizar un jugador"""
    overall_rating: Optional[int] = Field(None, ge=50, le=99)
    potential: Optional[int] = Field(None, ge=50, le=99)
    pace: Optional[int] = Field(None, ge=0, le=99)
    shooting: Optional[int] = Field(None, ge=0, le=99)
    passing: Optional[int] = Field(None, ge=0, le=99)
    dribbling: Optional[int] = Field(None, ge=0, le=99)
    defending: Optional[int] = Field(None, ge=0, le=99)
    physical: Optional[int] = Field(None, ge=0, le=99)
    base_market_value: Optional[float] = Field(None, gt=0)
    
    class Config:
        from_attributes = True
