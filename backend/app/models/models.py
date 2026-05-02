"""
Database Models - Esquema completo unificado
Todos los modelos de la base de datos en un solo archivo
"""

from sqlalchemy import Column, Integer, BigInteger, String, Float, Boolean, ForeignKey, DateTime, Text, Enum, UniqueConstraint
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
    
    # Email Verification
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    
    # Arena PvP Global
    global_elo = Column(Integer, default=1000)
    arena_tickets = Column(Integer, default=5)
    last_tickets_reset = Column(DateTime, default=datetime.utcnow)
    arena_wins = Column(Integer, default=0)
    arena_losses = Column(Integer, default=0)
    arena_draws = Column(Integer, default=0)
    
    # Estadísticas
    total_points = Column(Integer, default=0)  # Puntos Fantasy totales
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    avatar_url = Column(String(255), nullable=True)
    
    # Relaciones
    teams = relationship("Team", back_populates="user", cascade="all, delete-orphan")
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
    
    # Imagen/foto
    image_url = Column(String(255), nullable=True)

    # ==========================================
    # SISTEMA DE PUNTUACIÓN DE ICONOS
    # ==========================================
    # scoring_profile: LEGEND | MAESTRO | RELIABLE | VOLCANO | CURSED
    scoring_profile = Column(String(20), nullable=True)
    # Rango de puntos fantasy por jornada (solo iconos)
    min_fantasy = Column(Integer, nullable=True)
    max_fantasy = Column(Integer, nullable=True)

    # RELACIONAL: Estadísticas en tiempo real (Vista SQL)
    stats = relationship("PlayerStatsSummary", uselist=False, backref="player", viewonly=True)
    
    # Relaciones
    user_cards = relationship("UserCard", back_populates="player")
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def total_matches_played(self) -> int:
        return self.stats.total_matches_played if self.stats else 0

    @property
    def average_rating(self) -> float:
        """Calcula la nota promedio en tiempo real desde la vista"""
        return self.stats.avg_rating if self.stats else 0.0
    
    @property
    def average_fantasy_points(self) -> float:
        """Calcula los puntos Fantasy promedio en tiempo real desde la vista"""
        return self.stats.avg_fantasy_points if self.stats else 0.0
    
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
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=True)  
    # Puede estar presente sin team_id (carta en inventario de liga, no asignada a equipo)
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
    
    # Clausulazos: valor extra añadido por el usuario (Blindaje)
    protected_value = Column(Integer, default=0)
    
    # Metadatos
    acquired_at = Column(DateTime, default=datetime.utcnow)
    
    @property
    def current_market_value(self) -> float:
        """Obtiene el precio actual del jugador (base + blindaje)"""
        base_price = self.player.current_price if self.player else 0.0
        return base_price + (self.protected_value or 0)
    
    # Relación con el sobre del que salió (opcional)
    obtained_from_pack = relationship("PackOpeningCard", back_populates="card", uselist=False)
    
    def __repr__(self):
        return f"<UserCard User:{self.user_id} Player:{self.player_id} OVR:{self.current_overall}>"


# ==========================================
# MODELO: TEAM (Equipo del Usuario)
# ==========================================

class Team(Base):
    """
    Equipo de cada usuario dentro de una liga.
    Un usuario puede tener un equipo diferente por cada liga.
    """
    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint('user_id', 'league_id', name='uq_user_league_team'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    
    # Relación con usuario (muchos a 1 — un usuario tiene N equipos)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="teams")
    
    # Relación con liga (1 equipo por usuario por liga)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    league = relationship("League")
    
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
    active_formation = Column(String(10), default="4-4-2")
    
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
# MODELO: GAMEWEEK_LINEUP (Alineación por Jornada)
# ==========================================

class GameweekLineup(Base):
    """
    Alineación guardada por un equipo para una jornada específica = "Snapshot".
    Los puntos de la jornada se calculan sobre esta alineación.
    """
    __tablename__ = "gameweek_lineups"
    
    id = Column(Integer, primary_key=True, index=True)
    
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    gameweek_id = Column(Integer, ForeignKey("gameweeks.id"), nullable=False)
    
    # Snapshot de los datos
    active_formation = Column(String(10), nullable=False)
    
    # Puntos calculados específicamente para esta jornada con esta alineación
    points_earned = Column(Float, default=0.0)
    
    # Relaciones
    team = relationship("Team")
    gameweek = relationship("Gameweek")
    players = relationship("GameweekLineupPlayer", back_populates="lineup", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('team_id', 'gameweek_id', name='uq_team_gameweek'),
    )
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GameweekLineup Team:{self.team_id} GW:{self.gameweek_id}>"


class GameweekLineupPlayer(Base):
    """
    Tabla intermedia para GameweekLineup <-> UserCard.
    Permite normalizar la lista de jugadores.
    """
    __tablename__ = "gameweek_lineup_players"

    id = Column(Integer, primary_key=True, index=True)
    lineup_id = Column(Integer, ForeignKey("gameweek_lineups.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("user_cards.id"), nullable=False)
    
    position = Column(String(10), nullable=True)  # Posición específica en esa alineación
    is_captain = Column(Integer, default=0)       # 1 si es capitán
    points_earned = Column(Float, default=0.0)    # Puntos que ganó EXACTAMENTE en esta jornada

    # Relaciones
    lineup = relationship("GameweekLineup", back_populates="players")
    card = relationship("UserCard")

    def __repr__(self):
        return f"<GameweekLineupPlayer Lineup:{self.lineup_id} Card:{self.card_id}>"


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
# VISTA: PLAYER_STATS_SUMMARY (Estadísticas Reales)
# ==========================================

class PlayerStatsSummary(Base):
    """
    Modelo mapeado a una VISTA SQL que calcula agregativos en tiempo real.
    No se puede insertar/borrar en esta tabla.
    """
    __tablename__ = "player_stats_summary"
    
    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    total_matches_played = Column(Integer)
    sum_match_ratings = Column(Float)
    avg_rating = Column(Float)
    sum_fantasy_points = Column(Float)
    avg_fantasy_points = Column(Float)


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
    
    team1_rating_change = Column(Integer, default=0)
    team2_rating_change = Column(Integer, default=0)
    team1_global_change = Column(Integer, default=0)
    team2_global_change = Column(Integer, default=0)
    
    # ELO Changes relative to the battle
    rating_change = Column(Integer, default=0)
    global_rating_change = Column(Integer, default=0)
    
    # Metadatos
    simulated_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ArenaBattle {self.team1_id} vs {self.team2_id}>"


# ==========================================
# ENUM: INVITATION STATUS
# ==========================================

class InvitationStatus(enum.Enum):
    """Estado de una invitación a liga"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


# ==========================================
# MODELO: LEAGUE (Liga Fantasy)
# ==========================================

class League(Base):
    """
    Liga creada por un usuario. Otros usuarios pueden unirse
    mediante código de invitación o invitaciones directas.
    """
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Creador
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", foreign_keys=[owner_id])

    # Configuración
    max_members = Column(Integer, default=10)
    is_public = Column(Boolean, default=False)

    # Código de invitación único (UUID corto)
    invite_code = Column(String(20), unique=True, nullable=False, index=True)

    # Relaciones
    members = relationship("LeagueMember", back_populates="league", cascade="all, delete-orphan")
    invitations = relationship("LeagueInvitation", back_populates="league", cascade="all, delete-orphan")

    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def member_count(self) -> int:
        return len(self.members) if self.members else 0

    def __repr__(self):
        return f"<League {self.name} ({self.member_count}/{self.max_members})>"


# ==========================================
# MODELO: LEAGUE_MEMBER (Miembro de Liga)
# ==========================================

class LeagueMember(Base):
    """
    Relación usuario ↔ liga. Cada fila = un usuario en una liga.
    """
    __tablename__ = "league_members"

    id = Column(Integer, primary_key=True, index=True)

    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    league = relationship("League", back_populates="members")
    user = relationship("User")

    # Puntos acumulados dentro de esta liga
    league_points = Column(Integer, default=0)
    
    # Economía de la liga (cada usuario empieza con 100M)
    coins = Column(BigInteger, default=100000000)
    locked_coins = Column(BigInteger, default=0)

    # Rol dentro de la liga
    is_admin = Column(Boolean, default=False)

    joined_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<LeagueMember User:{self.user_id} League:{self.league_id}>"


# ==========================================
# MODELO: LEAGUE_INVITATION (Invitación)
# ==========================================

class LeagueInvitation(Base):
    """
    Invitación a una liga. Se puede enviar por email o username.
    """
    __tablename__ = "league_invitations"

    id = Column(Integer, primary_key=True, index=True)

    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    invited_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invited_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL si invitado por email externo

    league = relationship("League", back_populates="invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_id])
    invited_user = relationship("User", foreign_keys=[invited_user_id])

    # Email del invitado (por si no tiene cuenta aún)
    invited_email = Column(String(100), nullable=True)

    # Estado
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING)

    # Token único para aceptar/rechazar
    token = Column(String(40), unique=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<LeagueInvitation League:{self.league_id} Status:{self.status.value}>"


# ==========================================
# MODELO: PACK_OPENING (Apertura de Sobres)
# ==========================================

class PackOpening(Base):
    """
    Registro de cada sobre abierto por un usuario dentro de una liga.
    Actualmente solo hay sobres de iconos (legends).
    """
    __tablename__ = "pack_openings"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)

    pack_type = Column(String(20), default="icon")  # Por ahora solo "icon"
    cost = Column(Integer, nullable=False)
    cards_obtained = Column(Integer, default=0)

    opened_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    user = relationship("User")
    league = relationship("League")
    cards = relationship("PackOpeningCard", back_populates="pack_opening", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PackOpening User:{self.user_id} League:{self.league_id} Type:{self.pack_type}>"


# ==========================================
# MODELO: MARKET_AUCTION (Subasta Diaria)
# ==========================================

class MarketAuction(Base):
    """
    Representa una subasta diaria de 24h en una liga específica.
    Cada día se crea una nueva con 12 jugadores aleatorios.
    """
    __tablename__ = "market_auctions"

    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    
    # Tiempos
    started_at = Column(DateTime, default=datetime.utcnow)
    ends_at = Column(DateTime, nullable=False)
    
    # Estado
    is_active = Column(Boolean, default=True)
    is_resolved = Column(Boolean, default=False)
    
    league = relationship("League")
    slots = relationship("AuctionSlot", back_populates="auction", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MarketAuction League:{self.league_id} Ends:{self.ends_at}>"


class AuctionSlot(Base):
    """
    Un hueco en la subasta (un jugador a la venta).
    """
    __tablename__ = "auction_slots"

    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("market_auctions.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    
    # Economía
    base_price = Column(Integer, nullable=False)
    current_bid = Column(Integer, default=0)
    highest_bidder_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relaciones
    auction = relationship("MarketAuction", back_populates="slots")
    player = relationship("Player")
    highest_bidder = relationship("User", foreign_keys=[highest_bidder_id])
    bids = relationship("AuctionBid", back_populates="slot", cascade="all, delete-orphan")


class AuctionBid(Base):
    """
    Historial de pujas
    """
    __tablename__ = "auction_bids"

    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("auction_slots.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    slot = relationship("AuctionSlot", back_populates="bids")
    user = relationship("User")


# ==========================================
# MODELO: MARKET_LISTING (Venta de Usuario)
# ==========================================

class MarketListing(Base):
    """
    Un usuario pone a la venta una carta en el mercado de la liga.
    Precio mínimo = valor actual del jugador (Player.current_price).
    """
    __tablename__ = "market_listings"

    id = Column(Integer, primary_key=True, index=True)

    card_id = Column(Integer, ForeignKey("user_cards.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)

    asking_price = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

    listed_at = Column(DateTime, default=datetime.utcnow)
    sold_at = Column(DateTime, nullable=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    card = relationship("UserCard")
    seller = relationship("User", foreign_keys=[seller_id])
    buyer = relationship("User", foreign_keys=[buyer_id])
    league = relationship("League")
    bids = relationship("ListingBid", back_populates="listing", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MarketListing Card:{self.card_id} Price:{self.asking_price}>"


class ListingBid(Base):
    """
    Puja de un miembro de la liga por un jugador en venta (listado entre usuarios).
    Las monedas quedan bloqueadas hasta que el vendedor acepte una puja, cancele o venza la venta.
    """
    __tablename__ = "listing_bids"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("market_listings.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("MarketListing", back_populates="bids")
    user = relationship("User")

    def __repr__(self):
        return f"<ListingBid Listing:{self.listing_id} User:{self.user_id} {self.amount}>"


# ==========================================
# MODELO: SYSTEM_OFFER (Oferta del Sistema)
# ==========================================

class SystemOffer(Base):
    """
    Oferta automática del sistema para comprar una carta.
    Se genera 24h después de listar si nadie compra.
    Precio = 80-95% del asking_price.
    """
    __tablename__ = "system_offers"

    id = Column(Integer, primary_key=True, index=True)

    listing_id = Column(Integer, ForeignKey("market_listings.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("user_cards.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)

    offer_price = Column(Integer, nullable=False)
    is_accepted = Column(Boolean, default=False)
    is_expired = Column(Boolean, default=False)

    offered_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    listing = relationship("MarketListing")
    card = relationship("UserCard")
    user = relationship("User")
    league = relationship("League")

    def __repr__(self):
        return f"<SystemOffer Listing:{self.listing_id} Price:{self.offer_price}>"


# ==========================================
# MODELO: NOTIFICATION (Notificaciones de Subasta)
# ==========================================

class Notification(Base):
    """
    Notificaciones del sistema para los usuarios.
    Usada principalmente para informar del resultado de las subastas.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=True)

    # Tipo: "auction_won", "auction_lost"
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

    def __repr__(self):
        return f"<Notification User:{self.user_id} Type:{self.type}>"


# ==========================================
# MODELO: PACK_OPENING_CARD (Trazabilidad de Sobres)
# ==========================================

class PackOpeningCard(Base):
    """
    Relación n:m (o trazabilidad 1:n) entre un sobre abierto y las cartas obtenidas.
    Permite auditar qué cartas salieron en qué sobre.
    """
    __tablename__ = "pack_opening_cards"

    id = Column(Integer, primary_key=True, index=True)
    pack_opening_id = Column(Integer, ForeignKey("pack_openings.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("user_cards.id"), nullable=False, unique=True) # Una carta solo sale de un sobre

    pack_opening = relationship("PackOpening", back_populates="cards")
    card = relationship("UserCard", back_populates="obtained_from_pack")

    def __repr__(self):
        return f"<PackOpeningCard Pack:{self.pack_opening_id} Card:{self.card_id}>"
