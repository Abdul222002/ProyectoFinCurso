"""
Database Models - Esquema completo unificado
Todos los modelos de la base de datos en un solo archivo
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum


# ==========================================
# ENUMS
# ==========================================

class UserRole(enum.Enum):
    """Roles de usuario"""
    ADMIN = "admin"
    PREMIUM = "premium"
    FREE = "free"


class CardRarity(enum.Enum):
    """Rareza de las cartas"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    LEGEND = "legend"


class Position(enum.Enum):
    """Posiciones de jugadores"""
    GK = "GK"   # Goalkeeper
    DEF = "DEF" # Defender
    MID = "MID" # Midfielder
    FWD = "FWD" # Forward


class MatchStatus(enum.Enum):
    """Estado de un partido"""
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    CANCELLED = "cancelled"


# ==========================================
# MODELO: USER (Usuario)
# ==========================================

class User(Base):
    """
    Tabla de Usuarios del juego
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Rol y permisos
    role = Column(Enum(UserRole), default=UserRole.FREE)
    
    # Economía
    coins = Column(Integer, default=10000)  # Monedas del juego
    
    # Estadísticas
    total_points = Column(Integer, default=0)  # Puntos Fantasy totales
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    
    # Relaciones
    team = relationship("Team", back_populates="user", uselist=False, cascade="all, delete-orphan")
    owned_players = relationship("UserCard", back_populates="user", cascade="all, delete-orphan")
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User {self.username} - Level {self.level}>"


# ==========================================
# MODELO: PLAYER (Jugador Base)
# ==========================================

class Player(Base):
    """
    Tabla Maestra de Jugadores
    Incluye jugadores reales (Scottish Premiership) y Leyendas
    
    SISTEMA DE INERCIA DE PRECIOS:
    - current_price: El precio que ve el usuario HOY (cambia diariamente)
    - target_price: El precio objetivo calculado tras los partidos (cambia solo los fines de semana)
    - El current_price persigue gradualmente al target_price durante la semana
    """
    __tablename__ = "players"
    
    # ID y datos básicos
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    age = Column(Integer, nullable=False)
    position = Column(Enum(Position), nullable=False)
    nationality = Column(String(50), nullable=False)
    
    # Medias FIFA-style
    overall_rating = Column(Integer, nullable=False, index=True)  # OVR (60-99)
    potential = Column(Integer, nullable=False)
    
    # Stats detalladas (0-99)
    pace = Column(Integer, default=50)
    shooting = Column(Integer, default=50)
    passing = Column(Integer, default=50)
    dribbling = Column(Integer, default=50)
    defending = Column(Integer, default=50)
    physical = Column(Integer, default=50)
    
    # Tipo de carta
    is_legend = Column(Boolean, default=False)
    base_rarity = Column(Enum(CardRarity), default=CardRarity.BRONZE)
    
    # Datos de rendimiento real (solo jugadores actuales)
    sportmonks_id = Column(Integer, nullable=True, unique=True)
    current_team = Column(String(100), nullable=True)
    
    # ==========================================
    # ECONOMÍA DE INERCIA (SISTEMA DE PRECIOS)
    # ==========================================
    
    # current_price: Precio que ve el usuario HOY (€5.2M)
    # Se actualiza DIARIAMENTE moviéndose hacia el target_price
    current_price = Column(Float, default=1000000.0, index=True)
    
    # target_price: Precio 'ideal' calculado tras partidos (€8.0M) 
    # Se actualiza solo los FINES DE SEMANA basado en rendimiento
    target_price = Column(Float, default=1000000.0)
    
    # Campos acumulativos (para cálculos rápidos sin consultar historial)
    total_matches_played = Column(Integer, default=0)
    sum_match_ratings = Column(Float, default=0.0)  # Suma total de notas
    sum_fantasy_points = Column(Float, default=0.0)  # Suma total de puntos Fantasy
    
    # Imagen/foto
    image_url = Column(String(255), nullable=True)
    
    # Relaciones
    user_cards = relationship("UserCard", back_populates="player")
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def average_rating(self) -> float:
        """Calcula la nota promedio de forma eficiente"""
        if self.total_matches_played == 0:
            return 0.0
        return self.sum_match_ratings / self.total_matches_played
    
    @property
    def average_fantasy_points(self) -> float:
        """Calcula los puntos Fantasy promedio"""
        if self.total_matches_played == 0:
            return 0.0
        return self.sum_fantasy_points / self.total_matches_played
    
    @property
    def price_gap(self) -> float:
        """Diferencia entre precio target y actual (para medir la inercia)"""
        return self.target_price - self.current_price
    
    @property
    def price_gap_percentage(self) -> float:
        """Diferencia porcentual entre target y actual"""
        if self.current_price == 0:
            return 0.0
        return (self.price_gap / self.current_price) * 100
    
    def __repr__(self):
        return f"<Player {self.name} - OVR {self.overall_rating} - {self.position.value} - €{self.current_price:,.0f}>"


# ==========================================
# MODELO: USER_CARD (Carta del Usuario)
# ==========================================

class UserCard(Base):
    """
    Tabla de Cartas que posee cada usuario
    Un usuario puede tener múltiples cartas del mismo jugador
    """
    __tablename__ = "user_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)  # NULL = en el inventario
    
    user = relationship("User", back_populates="owned_players")
    player = relationship("Player", back_populates="user_cards")
    team = relationship("Team", back_populates="players")
    
    # Datos dinámicos de la carta
    current_overall = Column(Integer, nullable=False)  # Puede fluctuar
    # Nota: current_market_value se obtiene del Player.current_price
    # No lo duplicamos aquí para evitar inconsistencias
    
    # Estado
    is_tradeable = Column(Boolean, default=True)
    is_in_lineup = Column(Boolean, default=False)
    
    # Metadatos
    acquired_at = Column(DateTime, default=datetime.utcnow)
    
    @property
    def current_market_value(self) -> float:
        """Obtiene el precio actual del jugador desde la tabla Player"""
        return self.player.current_price if self.player else 0.0
    
    def __repr__(self):
        return f"<UserCard User:{self.user_id} Player:{self.player_id} OVR:{self.current_overall}>"


# ==========================================
# MODELO: TEAM (Equipo del Usuario)
# ==========================================

class Team(Base):
    """
    Equipo de cada usuario (su plantilla activa)
    """
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    
    # Relación con usuario (1 a 1)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    user = relationship("User", back_populates="team")
    
    # Personalización
    shield_url = Column(String(255), nullable=True)
    kit_color_primary = Column(String(7), default="#FF0000")
    kit_color_secondary = Column(String(7), default="#FFFFFF")
    
    # Estadísticas
    overall_rating = Column(Float, default=0.0)
    total_fantasy_points = Column(Integer, default=0)
    
    # Arena (PvP)
    arena_wins = Column(Integer, default=0)
    arena_losses = Column(Integer, default=0)
    arena_draws = Column(Integer, default=0)
    arena_rating = Column(Integer, default=1000)  # ELO-style
    
    # Táctica/Formación
    active_formation = Column(String(10), default="4-4-2")  # Ej: "4-3-3", "4-4-2", "3-5-2"
    
    # Relaciones
    players = relationship("UserCard", back_populates="team")
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Team {self.name} - OVR {self.overall_rating:.1f}>"


# ==========================================
# MODELO: GAMEWEEK (Jornada)
# ==========================================

class Gameweek(Base):
    """
    Representa una jornada de la liga real
    """
    __tablename__ = "gameweeks"
    
    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, nullable=False, unique=True)  # Jornada 1, 2, 3...
    
    # Fechas
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Estado
    is_active = Column(Boolean, default=False)
    is_finished = Column(Boolean, default=False)
    
    # Relaciones
    matches = relationship("Match", back_populates="gameweek")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Gameweek {self.number}>"


# ==========================================
# MODELO: MATCH (Partido Real)
# ==========================================

class Match(Base):
    """
    Partidos de la Scottish Premiership (datos reales de Sportmonks)
    """
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    sportmonks_id = Column(Integer, unique=True, nullable=False)
    
    # Jornada
    gameweek_id = Column(Integer, ForeignKey("gameweeks.id"), nullable=False)
    gameweek = relationship("Gameweek", back_populates="matches")
    
    # Equipos
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    
    # Resultado
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    
    # Estado
    status = Column(Enum(MatchStatus), default=MatchStatus.SCHEDULED)
    
    # Fecha
    kickoff_time = Column(DateTime, nullable=False)
    
    # Relaciones
    player_stats = relationship("PlayerMatchStats", back_populates="match")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Match {self.home_team} vs {self.away_team}>"


# ==========================================
# MODELO: PLAYER_MATCH_STATS (Estadísticas por Partido)
# ==========================================

class PlayerMatchStats(Base):
    """
    Estadísticas de un jugador en un partido específico
    Sistema OFICIAL de puntuación Fantasy Football
    Solo incluye campos disponibles en Sportmonks API (Free Plan)
    """
    __tablename__ = "player_match_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    
    player = relationship("Player")
    match = relationship("Match", back_populates="player_stats")
    
    # ======================================
    # BÁSICOS (API: MINUTES_PLAYED, RATING)
    # ======================================
    minutes_played = Column(Integer, default=0)
    rating = Column(Float, nullable=True)  # Nota 0-10
    
    # ======================================
    # GOLES Y ASISTENCIAS
    # ======================================
    goals = Column(Integer, default=0)  # API: GOALS
    assists = Column(Integer, default=0)  # API: ASSISTS (asistencias de gol)
    chances_created = Column(Integer, default=0)  # API: BIG_CHANCES_CREATED (asistencias sin gol)
    
    # ======================================
    # DEFENSA
    # ======================================
    clean_sheet = Column(Boolean, default=False)  # CALCULADO (goles_recibidos == 0 && min >= 60)
    goals_conceded = Column(Integer, default=0)  # API: GOALKEEPER_GOALS_CONCEDED (solo GK)
    goals_conceded_team = Column(Integer, default=0)  # API: GOALS_CONCEDED (todos)
    saves = Column(Integer, default=0)  # API: SAVES (solo GK)
    clearances = Column(Integer, default=0)  # API: CLEARANCES (despejes)
    
    # ======================================
    # PENALTIS
    # ======================================
    penalty_miss = Column(Integer, default=0)  # API: PENALTY_MISS
    penalty_save = Column(Integer, default=0)  # API: PENALTY_SAVE (solo GK)
    penalty_won = Column(Integer, default=0)  # API: PENALTY_WON
    penalty_committed = Column(Integer, default=0)  # API: PENALTY_COMMITTED
    
    # ======================================
    # TARJETAS (API: YELLOWCARDS, REDCARDS)
    # ======================================
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    
    # ======================================
    # ATAQUE - Acumuladores
    # ======================================
    shots_on_target = Column(Integer, default=0)  # API: SHOTS_ON_TARGET (tiros a puerta)
    dribbles = Column(Integer, default=0)  # API: SUCCESSFUL_DRIBBLES (regates logrados)
    crosses = Column(Integer, default=0)  # API: ACCURATE_CROSSES (balones al área)
    
    # ======================================
    # DEFENSA - Acumuladores
    # ======================================
    ball_recoveries = Column(Integer, default=0)  # API: BALL_RECOVERY
    
    # ======================================
    # PÉRDIDAS (Penalización)
    # ======================================
    dispossessed = Column(Integer, default=0)  # API: DISPOSSESSED
    possession_lost = Column(Integer, default=0)  # API: POSSESSION_LOST
    turnovers = Column(Integer, default=0)  # API: TURN_OVER
    total_losses = Column(Integer, default=0)  # CALCULADO (suma de las 3 anteriores)
    
    # ======================================
    # STATS EXTRA (Disponibles pero no usadas en puntos)
    # ======================================
    shots_total = Column(Integer, default=0)  # API: SHOTS_TOTAL
    accurate_passes = Column(Integer, default=0)  # API: ACCURATE_PASSES
    total_passes = Column(Integer, default=0)  # API: PASSES
    tackles = Column(Integer, default=0)  # API: TACKLES
    interceptions = Column(Integer, default=0)  # API: INTERCEPTIONS
    duels_won = Column(Integer, default=0)  # API: DUELS_WON
    fouls = Column(Integer, default=0)  # API: FOULS
    
    # ======================================
    # RESULTADO FINAL
    # ======================================
    fantasy_points = Column(Float, default=0.0)  # CALCULADO con sistema oficial
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PlayerMatchStats Player:{self.player_id} Match:{self.match_id} Points:{self.fantasy_points}>"


# ==========================================
# MODELO: ARENA_BATTLE (Batalla PvP)
# ==========================================

class ArenaBattle(Base):
    """
    Registro de batallas en la Arena (simulaciones PvP)
    """
    __tablename__ = "arena_battles"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Equipos participantes
    team1_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    team2_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    team1 = relationship("Team", foreign_keys=[team1_id])
    team2 = relationship("Team", foreign_keys=[team2_id])
    
    # Resultado
    team1_score = Column(Integer, nullable=False)
    team2_score = Column(Integer, nullable=False)
    winner_id = Column(Integer, ForeignKey("teams.id"), nullable=True)  # NULL = empate
    
    # Metadatos
    simulated_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ArenaBattle {self.team1_id} vs {self.team2_id}>"
