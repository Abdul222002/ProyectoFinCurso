"""
Calculadora de Puntos Fantasy
Procesa las estadísticas de Sportmonks y calcula los puntos según las reglas
"""

from app.services.scoring_rules import (
    SCORING_RULES,
    calcular_puntos_por_nota,
    get_position_rules,
    get_common_penalties
)
from app.models.models import PlayerMatchStats, Position


class FantasyPointsCalculator:
    """
    Calculadora de puntos Fantasy basada en estadísticas reales
    """
    
    def __init__(self):
        self.scoring_rules = SCORING_RULES
    
    def calculate_minutes_points(self, minutes_played: int) -> float:
        """
        Calcula puntos por minutos jugados
        
        Args:
            minutes_played: Minutos jugados en el partido
            
        Returns:
            float: Puntos obtenidos por minutos
        """
        for threshold, points in SCORING_RULES["MINUTES_PLAYED"]:
            if minutes_played >= threshold:
                return points
        return 0
    
    def calculate_common_penalties(self, stats: PlayerMatchStats) -> float:
        """
        Calcula las penalizaciones comunes (tarjetas, errores, etc.)
        
        Args:
            stats: Estadísticas del jugador en el partido
            
        Returns:
            float: Puntos negativos totales
        """
        penalties = 0.0
        
        # Tarjetas amarillas
        penalties += stats.yellow_cards * SCORING_RULES["YELLOWCARDS"]
        
        # Tarjetas rojas
        penalties += stats.red_cards * SCORING_RULES["RED_CARD"]
        
        # Goles en propia puerta
        penalties += stats.own_goals * SCORING_RULES["OWN_GOALS"]
        
        # Penaltis fallados
        penalties += stats.penalties_missed * SCORING_RULES["PENALTIES_MISSED"]
        
        # Pérdidas de balón
        penalties += stats.dispossessed * SCORING_RULES["DISPOSSESSED"]
        
        # Goles en contra (afecta poco a todos)
        penalties += stats.goals_conceded * SCORING_RULES["GOALS_AGAINST"]
        
        return penalties
    
    def calculate_position_points(self, stats: PlayerMatchStats, position: Position) -> float:
        """
        Calcula puntos específicos según la posición del jugador
        
        Args:
            stats: Estadísticas del jugador
            position: Posición del jugador (GK, DEF, MID, FWD)
            
        Returns:
            float: Puntos obtenidos por acciones específicas de la posición
        """
        position_key = position.value  # Convierte Enum a string
        rules = get_position_rules(position_key)
        
        points = 0.0
        
        # Goles
        if "GOALS" in rules:
            points += stats.goals * rules["GOALS"]
        
        # Asistencias
        if "ASSISTS" in rules:
            points += stats.assists * rules["ASSISTS"]
        
        # Portería a cero (Clean Sheet)
        if "CLEAN_SHEET" in rules and stats.clean_sheet:
            points += rules["CLEAN_SHEET"]
        
        # Paradas (solo porteros)
        if "SAVES" in rules:
            points += stats.saves * rules["SAVES"]
        
        # Penaltis parados
        if "PENALTIES_SAVED" in rules:
            points += stats.penalties_saved * rules["PENALTIES_SAVED"]
        
        # Despejes efectivos
        if "EFFECTIVE_CLEARANCES" in rules:
            points += stats.effective_clearances * rules["EFFECTIVE_CLEARANCES"]
        
        # Recuperaciones
        if "BALL_RECOVERY" in rules:
            points += stats.ball_recoveries * rules["BALL_RECOVERY"]
        
        # Penaltis provocados
        if "PENALTIES_WON" in rules:
            points += stats.penalties_won * rules["PENALTIES_WON"]
        
        # Tiros a puerta
        if "SHOTS_ON_TARGET" in rules:
            points += stats.shots_on_target * rules["SHOTS_ON_TARGET"]
        
        # Regates exitosos
        if "SUCCESSFUL_DRIBBLES" in rules:
            points += stats.successful_dribbles * rules["SUCCESSFUL_DRIBBLES"]
        
        # Centros precisos
        if "ACCURATE_CROSSES" in rules:
            points += stats.accurate_crosses * rules["ACCURATE_CROSSES"]
        
        # Penalización especial para porteros (goles en contra)
        if position_key == "GK" and "GOALS_AGAINST" in rules:
            points += stats.goals_conceded * rules["GOALS_AGAINST"]
        
        return points
    
    def calculate_total_points(self, stats: PlayerMatchStats, position: Position) -> float:
        """
        Calcula los puntos Fantasy totales de un jugador en un partido
        
        Args:
            stats: Estadísticas del jugador en el partido
            position: Posición del jugador
            
        Returns:
            float: Total de puntos Fantasy
        """
        # 1. Puntos base por minutos jugados
        minutes_points = self.calculate_minutes_points(stats.minutes_played)
        
        # 2. Puntos por la nota del partido
        rating_points = calcular_puntos_por_nota(stats.rating) if stats.rating else 0
        
        # 3. Puntos específicos de la posición
        position_points = self.calculate_position_points(stats, position)
        
        # 4. Penalizaciones comunes
        penalty_points = self.calculate_common_penalties(stats)
        
        # Total
        total = minutes_points + rating_points + position_points + penalty_points
        
        # Los puntos no pueden ser negativos
        return max(0, total)
    
    def get_points_breakdown(self, stats: PlayerMatchStats, position: Position) -> dict:
        """
        Devuelve un desglose detallado de los puntos
        Útil para mostrar al usuario cómo se calcularon los puntos
        
        Args:
            stats: Estadísticas del jugador
            position: Posición del jugador
            
        Returns:
            dict: Desglose de puntos por categoría
        """
        return {
            "minutes": self.calculate_minutes_points(stats.minutes_played),
            "rating": calcular_puntos_por_nota(stats.rating) if stats.rating else 0,
            "position_specific": self.calculate_position_points(stats, position),
            "penalties": self.calculate_common_penalties(stats),
            "total": self.calculate_total_points(stats, position)
        }


# Instancia global del calculador
calculator = FantasyPointsCalculator()
