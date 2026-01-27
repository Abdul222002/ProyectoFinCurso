"""
Actualizador de Mercado
Algoritmo de fluctuación de precios y medias (OVR) según rendimiento
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import Player, PlayerMatchStats, UserCard
import random


class MarketUpdater:
    """
    Gestiona la fluctuación dinámica de:
    - Medias (OVR) de jugadores
    - Valores de mercado
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_performance_score(self, player_id: int, weeks: int = 4) -> float:
        """
        Calcula el rendimiento promedio de un jugador en las últimas semanas
        
        Args:
            player_id: ID del jugador
            weeks: Número de semanas a considerar
            
        Returns:
            float: Puntuación promedio de rendimiento
        """
        # Fecha límite (últimas N semanas)
        cutoff_date = datetime.utcnow() - timedelta(weeks=weeks)
        
        # Obtener estadísticas recientes
        recent_stats = (
            self.db.query(PlayerMatchStats)
            .filter(
                PlayerMatchStats.player_id == player_id,
                PlayerMatchStats.created_at >= cutoff_date,
                PlayerMatchStats.minutes_played > 0  # Solo partidos donde jugó
            )
            .all()
        )
        
        if not recent_stats:
            return 0.0
        
        # Calcular promedio de:
        # - Nota del partido (rating)
        # - Puntos Fantasy
        avg_rating = sum(s.rating for s in recent_stats if s.rating) / len(recent_stats)
        avg_fantasy = sum(s.fantasy_points for s in recent_stats) / len(recent_stats)
        
        # Fórmula ponderada (70% nota, 30% puntos fantasy)
        performance_score = (avg_rating * 0.7) + (avg_fantasy * 0.3)
        
        return performance_score
    
    def update_player_overall(self, player_id: int) -> int:
        """
        Actualiza la media (OVR) de un jugador según su rendimiento reciente
        
        Lógica:
        - Rendimiento excelente (>= 8.0) -> +1 o +2 OVR
        - Rendimiento bueno (6.0-7.9) -> Sin cambios
        - Rendimiento malo (< 5.0) -> -1 o -2 OVR
        
        Args:
            player_id: ID del jugador
            
        Returns:
            int: Nueva media del jugador
        """
        player = self.db.query(Player).filter(Player.id == player_id).first()
        
        if not player or player.is_legend:
            # Las Leyendas no fluctúan
            return player.overall_rating if player else 0
        
        performance = self.calculate_performance_score(player_id)
        
        if performance == 0.0:
            # Sin datos recientes, no actualizar
            return player.overall_rating
        
        old_ovr = player.overall_rating
        new_ovr = old_ovr
        
        # Determinar cambio según rendimiento
        if performance >= 8.0:
            # Rendimiento excelente
            change = random.randint(1, 2)
            new_ovr = min(99, old_ovr + change)  # Máximo 99
            
        elif performance < 5.0:
            # Rendimiento malo
            change = random.randint(1, 2)
            new_ovr = max(50, old_ovr - change)  # Mínimo 50
        
        # Actualizar en la base de datos
        player.overall_rating = new_ovr
        self.db.commit()
        
        # También actualizar todas las cartas de este jugador en posesión de usuarios
        self._update_user_cards_ovr(player_id, new_ovr)
        
        return new_ovr
    
    def _update_user_cards_ovr(self, player_id: int, new_ovr: int):
        """
        Actualiza el OVR de todas las cartas de un jugador en posesión de usuarios
        
        Args:
            player_id: ID del jugador
            new_ovr: Nueva media del jugador
        """
        user_cards = (
            self.db.query(UserCard)
            .filter(UserCard.player_id == player_id)
            .all()
        )
        
        for card in user_cards:
            card.current_overall = new_ovr
        
        self.db.commit()
    
    def update_market_value(self, player_id: int) -> float:
        """
        Actualiza el valor de mercado de un jugador
        
        Factores:
        - Rendimiento reciente
        - Media (OVR) actual
        - Demanda (cuántos usuarios lo tienen)
        
        Args:
            player_id: ID del jugador
            
        Returns:
            float: Nuevo valor de mercado
        """
        player = self.db.query(Player).filter(Player.id == player_id).first()
        
        if not player:
            return 0.0
        
        # Valor base según OVR
        base_value = self._calculate_base_value_by_ovr(player.overall_rating)
        
        # Factor de rendimiento (multiplicador)
        performance = self.calculate_performance_score(player_id)
        performance_multiplier = 1.0
        
        if performance >= 8.0:
            performance_multiplier = 1.3  # +30%
        elif performance >= 7.0:
            performance_multiplier = 1.15  # +15%
        elif performance < 5.0:
            performance_multiplier = 0.8  # -20%
        
        # Factor de demanda (cuántos usuarios lo tienen)
        demand_multiplier = self._calculate_demand_multiplier(player_id)
        
        # Valor final
        new_value = base_value * performance_multiplier * demand_multiplier
        
        # Actualizar en BD
        player.base_market_value = new_value
        self.db.commit()
        
        # Actualizar todas las cartas de usuarios
        self._update_user_cards_value(player_id, new_value)
        
        return new_value
    
    def _calculate_base_value_by_ovr(self, ovr: int) -> float:
        """
        Calcula el valor base según la media (OVR)
        
        Escala:
        - 90+ = 5M+
        - 85-89 = 2-5M
        - 80-84 = 1-2M
        - 75-79 = 500k-1M
        - 70-74 = 250k-500k
        - < 70 = 100k-250k
        """
        if ovr >= 90:
            return random.uniform(5000000, 10000000)
        elif ovr >= 85:
            return random.uniform(2000000, 5000000)
        elif ovr >= 80:
            return random.uniform(1000000, 2000000)
        elif ovr >= 75:
            return random.uniform(500000, 1000000)
        elif ovr >= 70:
            return random.uniform(250000, 500000)
        else:
            return random.uniform(100000, 250000)
    
    def _calculate_demand_multiplier(self, player_id: int) -> float:
        """
        Calcula multiplicador según la demanda (cuántos usuarios lo tienen)
        
        Args:
            player_id: ID del jugador
            
        Returns:
            float: Multiplicador de demanda (0.8 - 1.5)
        """
        # Contar cuántos usuarios tienen este jugador
        count = (
            self.db.query(UserCard)
            .filter(UserCard.player_id == player_id)
            .count()
        )
        
        # A más demanda, más caro
        if count > 100:
            return 1.5  # +50%
        elif count > 50:
            return 1.3  # +30%
        elif count > 20:
            return 1.15  # +15%
        elif count < 5:
            return 0.9  # -10% (nadie lo quiere)
        else:
            return 1.0  # Neutral
    
    def _update_user_cards_value(self, player_id: int, new_value: float):
        """
        Actualiza el valor de mercado de todas las cartas de un jugador
        
        Args:
            player_id: ID del jugador
            new_value: Nuevo valor de mercado
        """
        user_cards = (
            self.db.query(UserCard)
            .filter(UserCard.player_id == player_id)
            .all()
        )
        
        for card in user_cards:
            card.current_market_value = new_value
        
        self.db.commit()
    
    def update_all_players(self):
        """
        Actualiza las medias y valores de TODOS los jugadores activos
        (Se ejecutaría semanalmente como tarea programada)
        """
        # Obtener todos los jugadores que no son leyendas
        active_players = (
            self.db.query(Player)
            .filter(Player.is_legend == False)
            .all()
        )
        
        updated_count = 0
        
        for player in active_players:
            # Actualizar OVR
            new_ovr = self.update_player_overall(player.id)
            
            # Actualizar valor de mercado
            new_value = self.update_market_value(player.id)
            
            updated_count += 1
            print(f"✅ {player.name}: OVR {new_ovr} | Value: €{new_value:,.0f}")
        
        print(f"\n📊 Total jugadores actualizados: {updated_count}")
