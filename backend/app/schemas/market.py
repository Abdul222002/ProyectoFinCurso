"""
Pydantic Schemas para el Mercado de Transferencias
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MarketPlayerResponse(BaseModel):
    """Jugador en el mercado"""
    id: int
    name: str
    position: str
    overall_rating: int
    current_team: Optional[str]
    current_price: float
    target_price: float
    base_rarity: str
    is_legend: bool
    image_url: Optional[str]

    # Calculados
    price_change_pct: float  # Diferencia % respecto al target

    class Config:
        from_attributes = True


class BuyResponse(BaseModel):
    """Respuesta tras comprar"""
    message: str
    card_id: int
    player_name: str
    price_paid: float
    remaining_coins: int


class SellResponse(BaseModel):
    """Respuesta tras vender"""
    message: str
    player_name: str
    price_received: float
    remaining_coins: int


class UserCardResponse(BaseModel):
    """Carta del usuario"""
    id: int
    player_id: int
    player_name: str
    position: str
    overall_rating: int
    current_overall: int
    current_price: float
    base_rarity: str
    is_legend: bool
    is_tradeable: bool
    is_in_lineup: bool
    image_url: Optional[str]
    acquired_at: datetime

    class Config:
        from_attributes = True
