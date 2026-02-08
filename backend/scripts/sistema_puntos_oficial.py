"""
SISTEMA MEJORADO DE PUNTUACIÓN FANTASY FOOTBALL
Versión optimizada para TFG
Mejoras: Modularidad, validaciones, logging, configuración flexible, testing
VALORES REBALANCEADOS aplicados ✅
"""

import os
import requests
from dotenv import load_dotenv
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import math
import logging
from datetime import datetime

load_dotenv()

# ============================================
# CONFIGURACIÓN Y LOGGING
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'fantasy_scoring_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

API_TOKEN = os.getenv('SPORTMONKS_API_KEY')
API_BASE_URL = "https://api.sportmonks.com/v3/football"
API_TIMEOUT = 30


# ============================================
# ENUMS Y DATACLASSES
# ============================================

class Position(Enum):
    """Posiciones de jugadores"""
    GK = "Portero"
    DEF = "Defensa"
    MID = "Mediocentro"
    FWD = "Delantero"
    
    def __str__(self):
        return self.value


@dataclass
class ScoringConfig:
    """Configuración flexible del sistema de puntuación - VALORES REBALANCEADOS ✅"""
    
    # Participación
    minutes_full_game: int = 60
    points_full_game: int = 2
    points_partial_game: int = 1
    
    # Goles por posición
    goals_gk_def: int = 6
    goals_mid: int = 5
    goals_fwd: int = 4
    
    # Asistencias
    assist_goal: int = 3
    assist_chance: int = 1
    
    # Clean Sheet por posición
    clean_sheet_gk: int = 4
    clean_sheet_def: int = 3
    clean_sheet_mid: int = 2
    clean_sheet_fwd: int = 1
    
    # Rating - REBALANCEADO ✅
    rating_max_points: int = 4
    rating_min_threshold: float = 5.0
    rating_max_threshold: float = 8.0  # era 8.5
    
    # Tarjetas
    yellow_card_penalty: int = -1
    red_card_penalty: int = -3
    
    # Acumuladores de ataque - SIN CAMBIO
    saves_per_point: int = 2
    shots_on_target_per_point: int = 2
    crosses_per_point: int = 2
    
    # REBALANCEADOS ✅
    dribbles_per_point: int = 3  # era 2
    
    # Acumuladores defensivos
    ball_recoveries_per_point: int = 5
    clearances_per_point: int = 3
    
    # REBALANCEADOS ✅
    tackles_per_point: int = 5  # era 3
    interceptions_per_point: int = 5  # era 3
    
    # Goles recibidos (penalización cada X goles)
    goals_conceded_per_penalty: int = 2
    goals_conceded_penalty_gk_def: int = -2
    goals_conceded_penalty_mid_fwd: int = -1
    
    # Pérdidas de balón (penalización cada X pérdidas según posición)
    losses_gk_def_threshold: int = 8
    losses_mid_threshold: int = 10
    losses_fwd_threshold: int = 12
    
    # Bonus extras - REBALANCEADOS ✅
    duels_won_per_point: int = 6  # era 4
    accurate_passes_per_point: int = 30  # era 15
    fouls_per_penalty: int = 3
    
    # Penaltis (si están disponibles en la API)
    penalty_save_bonus: int = 5       # Parar un penalti
    penalty_miss_penalty: int = -3    # Fallar un penalti
    penalty_won_bonus: int = 2        # Provocar penalti
    penalty_committed_penalty: int = -2  # Cometer penalti


@dataclass
class PlayerStats:
    """Estadísticas de un jugador"""
    
    # Identificación
    player_name: str = ""
    position: Optional[Position] = None
    participant_id: int = 0
    
    # Básicos
    minutes_played: int = 0
    rating: float = 0.0
    
    # Goles y asistencias
    goals: int = 0
    assists: int = 0
    chances_created: int = 0
    
    # Portero
    saves: int = 0
    goals_conceded: int = 0
    goals_conceded_team: int = 0
    
    # Penaltis
    penalty_miss: int = 0
    penalty_save: int = 0
    penalty_won: int = 0
    penalty_committed: int = 0
    
    # Tarjetas
    yellow_cards: int = 0
    red_cards: int = 0
    
    # Ataque
    shots_on_target: int = 0
    dribbles: int = 0
    crosses: int = 0
    
    # Defensa
    ball_recoveries: int = 0
    clearances: int = 0
    tackles: int = 0
    interceptions: int = 0
    
    # Pérdidas
    dispossessed: int = 0
    possession_lost: int = 0
    turnovers: int = 0
    
    # Extras
    duels_won: int = 0
    accurate_passes: int = 0
    fouls: int = 0
    
    # Contexto del partido
    clean_sheet: bool = False
    
    # Resultados
    fantasy_points: int = 0
    points_breakdown: Dict[str, float] = field(default_factory=dict)
    
    @property
    def total_losses(self) -> int:
        """Total de pérdidas de balón"""
        return self.dispossessed + self.possession_lost + self.turnovers


# ============================================
# MAPEO API
# ============================================

STAT_MAPPING = {
    # Básicos
    'MINUTES_PLAYED': 'minutes_played',
    'RATING': 'rating',
    
    # Goles y asistencias
    'GOALS': 'goals',
    'ASSISTS': 'assists',
    'BIG_CHANCES_CREATED': 'chances_created',
    
    # Portero
    'SAVES': 'saves',
    'GOALKEEPER_GOALS_CONCEDED': 'goals_conceded',
    'GOALS_CONCEDED': 'goals_conceded_team',
    
    # Penaltis
    'PENALTY_MISS': 'penalty_miss',
    'PENALTY_SAVE': 'penalty_save',
    'PENALTY_WON': 'penalty_won',
    'PENALTY_COMMITTED': 'penalty_committed',
    
    # Tarjetas
    'YELLOWCARDS': 'yellow_cards',
    'REDCARDS': 'red_cards',
    
    # Ataque
    'SHOTS_ON_TARGET': 'shots_on_target',
    'SUCCESSFUL_DRIBBLES': 'dribbles',
    'ACCURATE_CROSSES': 'crosses',
    
    # Defensa
    'BALL_RECOVERY': 'ball_recoveries',
    'CLEARANCES': 'clearances',
    'TACKLES': 'tackles',
    'INTERCEPTIONS': 'interceptions',
    
    # Pérdidas
    'DISPOSSESSED': 'dispossessed',
    'POSSESSION_LOST': 'possession_lost',
    'TURN_OVER': 'turnovers',
    
    # Extras
    'DUELS_WON': 'duels_won',
    'ACCURATE_PASSES': 'accurate_passes',
    'FOULS': 'fouls',
}

POSITION_TYPE_MAPPING = {
    24: Position.GK,
    25: Position.DEF,
    26: Position.DEF,
    27: Position.DEF,
    28: Position.MID,
    29: Position.MID,
    30: Position.MID,
    31: Position.FWD,
    32: Position.FWD,
    33: Position.FWD,
}


# ============================================
# CLASE PRINCIPAL: MOTOR DE PUNTUACIÓN
# ============================================

class FantasyScoringEngine:
    """Motor principal del sistema de puntuación Fantasy"""
    
    def __init__(self, config: Optional[ScoringConfig] = None):
        self.config = config or ScoringConfig()
        logger.info("Motor de puntuación inicializado con valores REBALANCEADOS")
    
    def calculate_points(self, stats: PlayerStats) -> PlayerStats:
        """
        Calcula los puntos fantasy de un jugador
        Devuelve el objeto PlayerStats actualizado con puntos y desglose
        """
        breakdown = {}
        total_points = 0.0
        
        # 1. Participación
        participation_points = self._calculate_participation(stats)
        if participation_points:
            breakdown['Participación'] = participation_points
            total_points += participation_points
        
        # 2. Goles
        goals_points = self._calculate_goals(stats)
        if goals_points:
            breakdown['Goles'] = goals_points
            total_points += goals_points
        
        # 3. Asistencias
        assists_points = self._calculate_assists(stats)
        if assists_points:
            breakdown['Asistencias'] = assists_points
            total_points += assists_points
        
        # 4. Clean Sheet
        clean_sheet_points = self._calculate_clean_sheet(stats)
        if clean_sheet_points:
            breakdown['Portería a cero'] = clean_sheet_points
            total_points += clean_sheet_points
        
        # 5. Rating
        rating_points = self._calculate_rating(stats)
        if rating_points:
            breakdown['Nota'] = rating_points
            total_points += rating_points
        
        # 6. Tarjetas
        cards_points = self._calculate_cards(stats)
        if cards_points:
            breakdown['Tarjetas'] = cards_points
            total_points += cards_points
        
        # 7. Paradas (solo GK)
        saves_points = self._calculate_saves(stats)
        if saves_points:
            breakdown['Paradas'] = saves_points
            total_points += saves_points
        
        # 8. Goles recibidos
        conceded_points = self._calculate_goals_conceded(stats)
        if conceded_points:
            breakdown['Goles recibidos'] = conceded_points
            total_points += conceded_points
        
        # 9. Bonus de ataque
        attack_points = self._calculate_attack_bonus(stats)
        if attack_points:
            breakdown['Bonus ataque'] = attack_points
            total_points += attack_points
        
        # 10. Bonus defensivos
        defense_points = self._calculate_defense_bonus(stats)
        if defense_points:
            breakdown['Bonus defensa'] = defense_points
            total_points += defense_points
        
        # 11. Pérdidas de balón
        losses_points = self._calculate_losses(stats)
        if losses_points:
            breakdown['Pérdidas'] = losses_points
            total_points += losses_points
        
        # 12. Bonus extras
        extra_points = self._calculate_extra_bonus(stats)
        if extra_points:
            breakdown['Bonus extras'] = extra_points
            total_points += extra_points
        
        # 13. Penaltis
        penalty_points = self._calculate_penalties(stats)
        if penalty_points:
            breakdown['Penaltis'] = penalty_points
            total_points += penalty_points
        
        # Actualizar stats
        stats.fantasy_points = round(total_points)
        stats.points_breakdown = breakdown
        
        logger.debug(f"{stats.player_name}: {stats.fantasy_points} puntos")
        
        return stats
    
    # ========================================
    # MÉTODOS DE CÁLCULO INDIVIDUAL
    # ========================================
    
    def _calculate_participation(self, stats: PlayerStats) -> float:
        """Puntos por participación"""
        if stats.minutes_played >= self.config.minutes_full_game:
            return self.config.points_full_game
        elif stats.minutes_played > 0:
            return self.config.points_partial_game
        return 0
    
    def _calculate_goals(self, stats: PlayerStats) -> float:
        """Puntos por goles según posición"""
        if not stats.goals:
            return 0
        
        if stats.position in [Position.GK, Position.DEF]:
            return stats.goals * self.config.goals_gk_def
        elif stats.position == Position.MID:
            return stats.goals * self.config.goals_mid
        else:  # FWD
            return stats.goals * self.config.goals_fwd
    
    def _calculate_assists(self, stats: PlayerStats) -> float:
        """Puntos por asistencias"""
        points = 0
        points += stats.assists * self.config.assist_goal
        points += stats.chances_created * self.config.assist_chance
        return points
    
    def _calculate_clean_sheet(self, stats: PlayerStats) -> float:
        """Puntos por portería a cero"""
        if not stats.clean_sheet or stats.minutes_played < self.config.minutes_full_game:
            return 0
        
        if stats.position == Position.GK:
            return self.config.clean_sheet_gk
        elif stats.position == Position.DEF:
            return self.config.clean_sheet_def
        elif stats.position == Position.MID:
            return self.config.clean_sheet_mid
        else:  # FWD
            return self.config.clean_sheet_fwd
    
    def _calculate_rating(self, stats: PlayerStats) -> float:
        """Puntos por nota del partido (escala lineal) - REBALANCEADO ✅"""
        if not stats.rating:
            return 0
        
        rating = stats.rating
        
        if rating >= self.config.rating_max_threshold:
            return self.config.rating_max_points
        elif rating >= self.config.rating_min_threshold:
            # Fórmula lineal: 5.0-8.0 = 0-4 pts
            rating_range = self.config.rating_max_threshold - self.config.rating_min_threshold
            points_per_rating = self.config.rating_max_points / rating_range
            return (rating - self.config.rating_min_threshold) * points_per_rating
        return 0
    
    def _calculate_cards(self, stats: PlayerStats) -> float:
        """Penalización por tarjetas"""
        points = 0
        points += stats.yellow_cards * self.config.yellow_card_penalty
        points += stats.red_cards * self.config.red_card_penalty
        return points
    
    def _calculate_saves(self, stats: PlayerStats) -> float:
        """Bonus por paradas (solo porteros)"""
        if stats.position != Position.GK:
            return 0
        return math.floor(stats.saves / self.config.saves_per_point)
    
    def _calculate_goals_conceded(self, stats: PlayerStats) -> float:
        """Penalización por goles recibidos"""
        goals_conceded = (stats.goals_conceded if stats.position == Position.GK 
                         else stats.goals_conceded_team)
        
        penalties = math.floor(goals_conceded / self.config.goals_conceded_per_penalty)
        
        if stats.position in [Position.GK, Position.DEF]:
            return penalties * self.config.goals_conceded_penalty_gk_def
        else:
            return penalties * self.config.goals_conceded_penalty_mid_fwd
    
    def _calculate_attack_bonus(self, stats: PlayerStats) -> float:
        """Bonus acumulados de ataque - REBALANCEADO ✅"""
        points = 0
        points += math.floor(stats.shots_on_target / self.config.shots_on_target_per_point)
        points += math.floor(stats.dribbles / self.config.dribbles_per_point)  # ÷3
        points += math.floor(stats.crosses / self.config.crosses_per_point)
        return points
    
    def _calculate_defense_bonus(self, stats: PlayerStats) -> float:
        """Bonus acumulados defensivos - REBALANCEADO ✅"""
        points = 0
        points += math.floor(stats.ball_recoveries / self.config.ball_recoveries_per_point)
        points += math.floor(stats.clearances / self.config.clearances_per_point)
        points += math.floor(stats.tackles / self.config.tackles_per_point)  # ÷5
        points += math.floor(stats.interceptions / self.config.interceptions_per_point)  # ÷5
        return points
    
    def _calculate_losses(self, stats: PlayerStats) -> float:
        """Penalización por pérdidas según posición"""
        total_losses = stats.total_losses
        
        if stats.position in [Position.GK, Position.DEF]:
            threshold = self.config.losses_gk_def_threshold
        elif stats.position == Position.MID:
            threshold = self.config.losses_mid_threshold
        else:  # FWD
            threshold = self.config.losses_fwd_threshold
        
        return -math.floor(total_losses / threshold)
    
    def _calculate_extra_bonus(self, stats: PlayerStats) -> float:
        """Bonus y penalizaciones extras - REBALANCEADO ✅"""
        points = 0
        points += math.floor(stats.duels_won / self.config.duels_won_per_point)  # ÷6
        points += math.floor(stats.accurate_passes / self.config.accurate_passes_per_point)  # ÷30
        points -= math.floor(stats.fouls / self.config.fouls_per_penalty)
        return points
    
    def _calculate_penalties(self, stats: PlayerStats) -> float:
        """Puntos/penalizaciones relacionados con penaltis"""
        points = 0
        
        # Parar un penalti (principalmente porteros)
        if stats.penalty_save:
            bonus = getattr(self.config, 'penalty_save_bonus', 5)
            points += stats.penalty_save * bonus
        
        # Fallar un penalti (penalización)
        if stats.penalty_miss:
            penalty = getattr(self.config, 'penalty_miss_penalty', -3)
            points += stats.penalty_miss * penalty
        
        # Provocar un penalti (bonus)
        if stats.penalty_won:
            bonus = getattr(self.config, 'penalty_won_bonus', 2)
            points += stats.penalty_won * bonus
        
        # Cometer penalti (penalización)
        if stats.penalty_committed:
            penalty = getattr(self.config, 'penalty_committed_penalty', -2)
            points += stats.penalty_committed * penalty
        
        return points


# ============================================
# CLASE: API CLIENT
# ============================================

class SportmonksAPIClient:
    """Cliente para interactuar con Sportmonks API"""
    
    def __init__(self, api_token: str):
        if not api_token:
            raise ValueError("API token is required")
        self.api_token = api_token
        self.base_url = API_BASE_URL
    
    def get_fixture(self, fixture_id: int) -> Optional[Dict]:
        """Obtiene datos de un partido"""
        url = f"{self.base_url}/fixtures/{fixture_id}"
        params = {
            "api_token": self.api_token,
            "include": "lineups.details.type;participants;scores"
        }
        
        try:
            logger.info(f"Obteniendo fixture {fixture_id}...")
            response = requests.get(url, params=params, timeout=API_TIMEOUT)
            response.raise_for_status()
            return response.json().get('data')
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener fixture {fixture_id}: {e}")
            return None


# ============================================
# CLASE: DATA EXTRACTOR
# ============================================

class StatsExtractor:
    """Extrae y procesa estadísticas de la API"""
    
    @staticmethod
    def map_position(type_id: int) -> Position:
        """Mapea type_id a Position"""
        return POSITION_TYPE_MAPPING.get(type_id, Position.FWD)
    
    @staticmethod
    def extract_player_stats(player_entry: Dict, clean_sheet: bool = False) -> PlayerStats:
        """Extrae estadísticas de un jugador desde la API"""
        stats = PlayerStats(
            player_name=player_entry.get('player_name', 'N/A'),
            position=StatsExtractor.map_position(player_entry.get('type_id')),
            participant_id=player_entry.get('participant_id', 0),
            clean_sheet=clean_sheet
        )
        
        details = player_entry.get('details', [])
        
        for stat in details:
            developer_name = stat.get('type', {}).get('developer_name', '')
            value = stat.get('data', {}).get('value')
            
            if developer_name in STAT_MAPPING:
                field_name = STAT_MAPPING[developer_name]
                
                try:
                    if field_name == 'rating':
                        setattr(stats, field_name, float(value) if value else 0.0)
                    else:
                        setattr(stats, field_name, int(value) if value else 0)
                except (ValueError, TypeError):
                    logger.warning(f"Error convirtiendo {field_name}={value}")
                    setattr(stats, field_name, 0)
        
        return stats
    
    @staticmethod
    def determine_clean_sheet(
        position: Position,
        participant_id: int,
        home_team_id: int,
        away_team_id: int,
        home_score: int,
        away_score: int
    ) -> bool:
        """Determina si un jugador tiene clean sheet"""
        if position not in [Position.GK, Position.DEF]:
            return False
        
        is_home = participant_id == home_team_id
        return (away_score == 0) if is_home else (home_score == 0)


# ============================================
# CLASE: PRESENTADOR DE RESULTADOS
# ============================================

class ResultsPresenter:
    """Formatea y presenta los resultados"""
    
    @staticmethod
    def print_match_header(home_team: str, away_team: str, home_score: int, away_score: int):
        """Imprime encabezado del partido"""
        print(f"\n{'='*130}")
        print(f"⚽ SISTEMA DE PUNTUACIÓN FANTASY FOOTBALL - VERSIÓN REBALANCEADA ✅")
        print(f"{'='*130}")
        print(f"\n🏟️  {home_team} {home_score} - {away_score} {away_team}\n")
        print(f"{'='*130}\n")
    
    @staticmethod
    def print_table_header():
        """Imprime encabezado de la tabla"""
        print(f"{'JUGADOR':<25} | {'POS':<10} | {'MIN':<3} | {'GOL':<3} | {'AST':<3} | "
              f"{'NOTA':<4} | {'PUNTOS':<6} | DESGLOSE")
        print("-" * 130)
    
    @staticmethod
    def print_player_row(stats: PlayerStats):
        """Imprime fila de un jugador"""
        if stats.minutes_played == 0:
            return  # No mostrar jugadores que no jugaron
        
        # Desglose simplificado
        desglose_items = []
        if stats.goals > 0:
            desglose_items.append(f"{stats.goals}G")
        if stats.assists > 0:
            desglose_items.append(f"{stats.assists}A")
        if stats.clean_sheet:
            desglose_items.append("CS")
        if stats.yellow_cards > 0:
            desglose_items.append("🟨" * stats.yellow_cards)
        if stats.red_cards > 0:
            desglose_items.append("🟥")
        
        desglose_str = " ".join(desglose_items) if desglose_items else "-"
        
        print(f"{stats.player_name:<25} | {str(stats.position):<10} | "
              f"{stats.minutes_played:<3} | {stats.goals:<3} | {stats.assists:<3} | "
              f"{stats.rating:<4.1f} | {stats.fantasy_points:>6} | {desglose_str}")
    
    @staticmethod
    def print_detailed_breakdown(stats: PlayerStats):
        """Imprime desglose detallado de puntos"""
        print(f"\n📊 Desglose detallado - {stats.player_name}")
        print("-" * 60)
        for category, points in stats.points_breakdown.items():
            print(f"  {category:<25}: {points:>+6.1f} pts")
        print("-" * 60)
        print(f"  {'TOTAL':<25}: {stats.fantasy_points:>6} pts")
        print()
    
    @staticmethod
    def print_top_scorers(players_stats: List[PlayerStats], top_n: int = 10):
        """Imprime top N jugadores por puntos"""
        sorted_players = sorted(
            [p for p in players_stats if p.minutes_played > 0],
            key=lambda x: x.fantasy_points,
            reverse=True
        )[:top_n]
        
        print(f"\n🏆 TOP {top_n} JUGADORES DEL PARTIDO")
        print("-" * 80)
        for i, player in enumerate(sorted_players, 1):
            print(f"{i}. {player.player_name:<25} ({player.position}) - "
                  f"{player.fantasy_points} pts")
        print()


# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def analyze_fixture(fixture_id: int, config: Optional[ScoringConfig] = None, 
                   show_detailed: bool = False, top_n: int = 10):
    """
    Analiza un partido y calcula puntos fantasy
    
    Args:
        fixture_id: ID del partido
        config: Configuración personalizada (opcional)
        show_detailed: Mostrar desglose detallado
        top_n: Número de mejores jugadores a mostrar
    """
    
    # Validación
    if not API_TOKEN:
        logger.error("SPORTMONKS_API_KEY no está configurada")
        return
    
    # Inicializar componentes
    api_client = SportmonksAPIClient(API_TOKEN)
    scoring_engine = FantasyScoringEngine(config)
    presenter = ResultsPresenter()
    
    # Obtener datos del partido
    fixture_data = api_client.get_fixture(fixture_id)
    if not fixture_data:
        return
    
    # Extraer información del partido
    lineups = fixture_data.get('lineups', [])
    participants = fixture_data.get('participants', [])
    scores = fixture_data.get('scores', [])
    
    # Info de equipos
    home_team = next((p for p in participants 
                     if p.get('meta', {}).get('location') == 'home'), {})
    away_team = next((p for p in participants 
                     if p.get('meta', {}).get('location') == 'away'), {})
    
    home_score = next((s['score']['goals'] for s in scores 
                      if s['description'] == 'CURRENT' 
                      and s['participant_id'] == home_team.get('id')), 0)
    away_score = next((s['score']['goals'] for s in scores 
                      if s['description'] == 'CURRENT' 
                      and s['participant_id'] == away_team.get('id')), 0)
    
    # Mostrar encabezado
    presenter.print_match_header(
        home_team.get('name', 'Home'),
        away_team.get('name', 'Away'),
        home_score,
        away_score
    )
    
    # Procesar jugadores
    players_stats = []
    presenter.print_table_header()
    
    for player_entry in lineups:
        # Determinar clean sheet
        clean_sheet = StatsExtractor.determine_clean_sheet(
            StatsExtractor.map_position(player_entry.get('type_id')),
            player_entry.get('participant_id'),
            home_team.get('id'),
            away_team.get('id'),
            home_score,
            away_score
        )
        
        # Extraer stats
        stats = StatsExtractor.extract_player_stats(player_entry, clean_sheet)
        
        # Calcular puntos
        stats = scoring_engine.calculate_points(stats)
        players_stats.append(stats)
        
        # Mostrar en tabla
        presenter.print_player_row(stats)
    
    # Resumen
    print("\n" + "="*130)
    
    # Top jugadores
    presenter.print_top_scorers(players_stats, top_n)
    
    # Desglose detallado (opcional)
    if show_detailed:
        top_player = max((p for p in players_stats if p.minutes_played > 0),
                        key=lambda x: x.fantasy_points, default=None)
        if top_player:
            presenter.print_detailed_breakdown(top_player)
    
    logger.info(f"Análisis completado - {len([p for p in players_stats if p.minutes_played > 0])} jugadores procesados")
    print("="*130 + "\n")
    
    return players_stats


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    # Análisis con sistema REBALANCEADO
    print("\n🎯 PROBANDO SISTEMA REBALANCEADO")
    print("="*80)
    analyze_fixture(19428039, show_detailed=True, top_n=10)
