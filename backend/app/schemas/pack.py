"""
Pydantic Schemas para el Sistema de Sobres (Packs)
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class PackCardResult(BaseModel):
    """Una carta obtenida de un sobre"""
    card_id: int
    player_id: int
    player_name: str
    position: str
    overall_rating: int
    base_rarity: str
    is_legend: bool
    image_url: Optional[str]

    class Config:
        from_attributes = True


class PackOpenResponse(BaseModel):
    """Resultado de abrir un sobre"""
    message: str
    pack_type: str
    cards: List[PackCardResult]
    cost: int
    remaining_coins: int


class PackHistoryItem(BaseModel):
    """Un sobre abierto en el historial"""
    id: int
    pack_type: str
    cost: int
    cards_obtained: int
    opened_at: datetime

    class Config:
        from_attributes = True
