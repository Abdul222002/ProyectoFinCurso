"""
Sistema de Economía con Inercia de Precios
Gestiona la fluctuación gradual de precios basada en rendimiento
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Dict, Optional
from app.models.models import Player, PlayerMatchStats, UserCard
from app.services.calculator import calculator
from app.models.models import Position


class PriceInertiaSystem:
    """
    Sistema de precios con inercia
    
    Concepto:
    - Los fines de semana (tras partidos): Se calcula un PRECIO OBJETIVO basado en rendimiento
    - Durante la semana: El precio actual se mueve GRADUALMENTE hacia el objetivo
    - Esto evita volatilidad extrema y crea un mercado más realista
    """
    
    def __init__(self, db: Session):
        self.db = db
        # Configuración de inercia
        self.DAILY_MOVEMENT_PERCENTAGE = 0.15  # El precio se mueve 15% diario hacia el target
        self.MIN_PRICE = 50000.0  # Precio mínimo: 50k
        self.MAX_PRICE = 20000000.0  # Precio máximo: 20M
    
    def calculate_target_price(self, player_id: int, weeks: int = 4) -> float:
        """
        Calcula el precio OBJETIVO basado en rendimiento reciente
        
        Este método se ejecuta los fines de semana tras los partidos
        
        Args:
            player_id: ID del jugador
            weeks: Semanas de historial a considerar
            
        Returns:
            float: Precio objetivo calculado
        """
        player = self.db.query(Player).filter(Player.id == player_id).first()
        
        if not player or player.is_legend:
            # Las leyendas tienen precio fijo
            return player.base_market_value if player else self.MIN_PRICE
        
        # 1. Precio base según OVR
        base_price = self._calculate_base_price_by_ovr(player.overall_rating)
        
        # 2. Factor de rendimiento (últimas semanas)
        performance_multiplier = self._calculate_performance_multiplier(player_id, weeks)
        
        # 3. Factor de posición (algunas posiciones son más valiosas)
        position_multiplier = self._get_position_multiplier(player.position)
        
        # 4. Factor de edad (jóvenes con potencial son más caros)
        age_multiplier = self._calculate_age_multiplier(player.age, player.potential)
        
        # Calcular precio target
        target_price = base_price * performance_multiplier * position_multiplier * age_multiplier
        
        # Asegurar que está dentro de los límites
        target_price = max(self.MIN_PRICE, min(self.MAX_PRICE, target_price))
        
        return round(target_price, 2)
    
    def _calculate_base_price_by_ovr(self, ovr: int) -> float:
        """
        Precio base según la media (OVR)
        
        Tabla de precios base:
        - 90+ = 3-8M
        - 85-89 = 1.5-3M
        - 80-84 = 800k-1.5M
        - 75-79 = 400k-800k
        - 70-74 = 200k-400k
        - < 70 = 50k-200k
        """
        if ovr >= 90:
            return 3000000 + (ovr - 90) * 500000  # 3M base + 500k por cada punto sobre 90
        elif ovr >= 85:
            return 1500000 + (ovr - 85) * 300000
        elif ovr >= 80:
            return 800000 + (ovr - 80) * 140000
        elif ovr >= 75:
            return 400000 + (ovr - 75) * 80000
        elif ovr >= 70:
            return 200000 + (ovr - 70) * 40000
        else:
            return 50000 + (ovr - 50) * 7500
    
    def _calculate_performance_multiplier(self, player_id: int, weeks: int) -> float:
        """
        Multiplicador basado en rendimiento reciente
        
        Analiza los puntos Fantasy de las últimas semanas
        
        Returns:
            float: Multiplicador entre 0.5 (muy mal) y 2.0 (excelente)
        """
        cutoff_date = datetime.utcnow() - timedelta(weeks=weeks)
        
        recent_stats = (
            self.db.query(PlayerMatchStats)
            .filter(
                PlayerMatchStats.player_id == player_id,
                PlayerMatchStats.created_at >= cutoff_date,
                PlayerMatchStats.minutes_played > 0
            )
            .all()
        )
        
        if not recent_stats:
            return 1.0  # Sin datos = neutral
        
        # Calcular promedio de puntos Fantasy
        avg_fantasy_points = sum(s.fantasy_points for s in recent_stats) / len(recent_stats)
        
        # Convertir puntos en multiplicador
        if avg_fantasy_points >= 10:
            return 2.0  # Rendimiento excelente: +100%
        elif avg_fantasy_points >= 8:
            return 1.6  # Muy bien: +60%
        elif avg_fantasy_points >= 6:
            return 1.3  # Bien: +30%
        elif avg_fantasy_points >= 4:
            return 1.0  # Normal: sin cambio
        elif avg_fantasy_points >= 2:
            return 0.8  # Mal: -20%
        else:
            return 0.5  # Muy mal: -50%
    
    def _get_position_multiplier(self, position: Position) -> float:
        """
        Multiplicador según la posición
        
        Los delanteros suelen ser más caros en el mercado real
        """
        position_values = {
            Position.FWD: 1.2,  # Delanteros +20%
            Position.MID: 1.1,  # Mediocampistas +10%
            Position.DEF: 0.95,  # Defensas -5%
            Position.GK: 0.85   # Porteros -15% (menos demanda)
        }
        return position_values.get(position, 1.0)
    
    def _calculate_age_multiplier(self, age: int, potential: int) -> float:
        """
        Multiplicador por edad y potencial
        
        Los jóvenes con alto potencial son más valiosos
        """
        if age <= 21:
            # Jóvenes promesas
            if potential >= 85:
                return 1.4  # Superestrella en potencia: +40%
            elif potential >= 80:
                return 1.2  # Gran potencial: +20%
            else:
                return 1.0
        elif age <= 25:
            # Edad ideal
            return 1.15  # +15%
        elif age <= 28:
            # Madurez
            return 1.05  # +5%
        elif age <= 31:
            # Veterano
            return 0.95  # -5%
        else:
            # Veterano en declive
            return 0.8  # -20%
    
    def apply_daily_inertia(self, player_id: int) -> Dict[str, float]:
        """
        Aplica inercia diaria: mueve el precio actual hacia el target
        
        Este método se ejecuta DIARIAMENTE (Lunes a Viernes)
        
        Fórmula:
            nuevo_precio = precio_actual + (precio_target - precio_actual) * INERCIA
        
        Args:
            player_id: ID del jugador
            
        Returns:
            dict: {"old_price": float, "new_price": float, "target_price": float}
        """
        player = self.db.query(Player).filter(Player.id == player_id).first()
        
        if not player or player.is_legend:
            return {
                "old_price": player.base_market_value if player else 0,
                "new_price": player.base_market_value if player else 0,
                "target_price": player.base_market_value if player else 0
            }
        
        old_price = player.base_market_value
        target_price = self.calculate_target_price(player_id)
        
        # Calcular diferencia
        difference = target_price - old_price
        
        # Aplicar inercia (moverse solo un % hacia el target)
        daily_movement = difference * self.DAILY_MOVEMENT_PERCENTAGE
        new_price = old_price + daily_movement
        
        # Asegurar límites
        new_price = max(self.MIN_PRICE, min(self.MAX_PRICE, new_price))
        new_price = round(new_price, 2)
        
        # Actualizar en BD
        player.base_market_value = new_price
        self.db.commit()
        
        # También actualizar cartas de usuarios
        self._update_user_cards_price(player_id, new_price)
        
        return {
            "old_price": old_price,
            "new_price": new_price,
            "target_price": target_price,
            "movement": new_price - old_price,
            "movement_percentage": ((new_price - old_price) / old_price * 100) if old_price > 0 else 0
        }
    
    def set_target_price(self, player_id: int) -> Dict[str, float]:
        """
        Establece el precio target tras un partido
        
        Este método se ejecuta los FINES DE SEMANA (tras los partidos)
        
        Args:
            player_id: ID del jugador
            
        Returns:
            dict: {"old_target": float, "new_target": float}
        """
        player = self.db.query(Player).filter(Player.id == player_id).first()
        
        if not player:
            return {"old_target": 0, "new_target": 0}
        
        old_target = player.base_market_value
        new_target = self.calculate_target_price(player_id)
        
        # Guardar el target (en este caso, lo guardamos directamente en base_market_value)
        # En una implementación más compleja, podrías tener un campo separado "target_price"
        
        return {
            "old_target": old_target,
            "new_target": new_target,
            "change": new_target - old_target,
            "change_percentage": ((new_target - old_target) / old_target * 100) if old_target > 0 else 0
        }
    
    def _update_user_cards_price(self, player_id: int, new_price: float):
        """
        Actualiza el precio en todas las cartas de usuarios
        
        Args:
            player_id: ID del jugador
            new_price: Nuevo precio de mercado
        """
        user_cards = (
            self.db.query(UserCard)
            .filter(UserCard.player_id == player_id)
            .all()
        )
        
        for card in user_cards:
            card.current_market_value = new_price
        
        self.db.commit()
    
    def get_price_trend(self, player_id: int, days: int = 7) -> Dict:
        """
        Analiza la tendencia de precio (útil para mostrar gráficas)
        
        Args:
            player_id: ID del jugador
            days: Días a analizar
            
        Returns:
            dict: Información de tendencia
        """
        player = self.db.query(Player).filter(Player.id == player_id).first()
        
        if not player:
            return {"trend": "unknown", "percentage": 0}
        
        # Aquí podrías consultar un historial de precios si lo guardas
        # Por ahora, calculamos basándonos en el objetivo vs actual
        
        current_price = player.base_market_value
        target_price = self.calculate_target_price(player_id)
        
        difference_percentage = ((target_price - current_price) / current_price * 100) if current_price > 0 else 0
        
        if difference_percentage > 10:
            trend = "rising_fast"
        elif difference_percentage > 3:
            trend = "rising"
        elif difference_percentage < -10:
            trend = "falling_fast"
        elif difference_percentage < -3:
            trend = "falling"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "current_price": current_price,
            "target_price": target_price,
            "difference_percentage": round(difference_percentage, 2)
        }
