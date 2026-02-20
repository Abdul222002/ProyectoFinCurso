"""
Pydantic Schemas para el Mercado de Subastas (Auction Market)
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ==========================================
# RESPUESTAS DE SUBASTA
# ==========================================

class AuctionBidResponse(BaseModel):
    id: int
    user_id: int
    username: str
    amount: int
    created_at: datetime

    class Config:
        from_attributes = True


class AuctionSlotResponse(BaseModel):
    id: int
    player_id: int
    player_name: str
    position: str
    overall_rating: int
    base_rarity: str
    image_url: Optional[str]
    
    base_price: int
    current_bid: int
    highest_bidder_id: Optional[int]
    highest_bidder_username: Optional[str]  # Para mostrar quién va ganando
    
    class Config:
        from_attributes = True


class AuctionResponse(BaseModel):
    id: int
    league_id: int
    ends_at: datetime
    is_active: bool
    server_time: datetime
    slots: List[AuctionSlotResponse]

    class Config:
        from_attributes = True


# ==========================================
# ACCIONES
# ==========================================

class BidRequest(BaseModel):
    amount: int


class BidResponse(BaseModel):
    message: str
    slot_id: int
    new_bid: int
    remaining_coins: int


class SellResponse(BaseModel):
    """Respuesta tras vender una carta al sistema (85% valor)"""
    message: str
    player_name: str
    price_received: int
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
    league_id: Optional[int]

    class Config:
        from_attributes = True
