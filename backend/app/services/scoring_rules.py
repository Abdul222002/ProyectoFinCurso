"""
Reglas de Puntuación Fantasy (Scoring Rules)
Sistema de puntos basado en estadísticas reales de Sportmonks
"""

# ==========================================
# CONFIGURACIÓN DE PUNTUACIÓN (RULES ENGINE)
# ==========================================

SCORING_RULES = {
    # --- 1. MINUTOS (Para todos) ---
    # "minutes played"
    "MINUTES_PLAYED": [
        (60, 2),  # > 60 min: +2 puntos
        (1, 1)    # < 60 min: +1 punto
    ],

    # --- 2. SANCIONES Y ERRORES (Para todos) ---
    "YELLOWCARDS": -1,       # "yellow card"
    "RED_CARD": -3,          # "red card" (incluye "second yellow card")
    "OWN_GOALS": -2,         # "own goals"
    "PENALTIES_MISSED": -2,  # "penalties missed"
    "PENALTIES_COMMITTED": -2, # "commited penalties"
    "DISPOSSESSED": -0.5,    # "lost balls" (Pérdidas de balón)
    "GOALS_AGAINST": -0.5,   # "goals agaisnts" (Afecta a todos, pero poco)

    # --- 3. PORTEROS (GK) ---
    "GK": {
        "GOALS": 10,
        "ASSISTS": 6,
        "SAVES": 1,              # "saves"
        "PENALTIES_SAVED": 5,    # "penalties saved"
        "CLEAN_SHEET": 4,        # (Calculado)
        "EFFECTIVE_CLEARANCES": 0.5, # "effective clearances"
        "BALL_RECOVERY": 0.5,    # "recoveries"
        "GOALS_AGAINST": -1,     # (Castigo doble para el portero)
    },

    # --- 4. DEFENSAS (DEF) ---
    "DEF": {
        "GOALS": 6,              # "goals"
        "ASSISTS": 4,            # "goals assists"
        "CLEAN_SHEET": 4,        # Portería a cero
        "EFFECTIVE_CLEARANCES": 0.5, # "effective clearances" (Su trabajo principal)
        "BALL_RECOVERY": 0.5,    # "recoveries"
        "INTERCEPTIONS": 0.5,    # (Cuenta como recuperación)
        "PENALTIES_WON": 2,      # "penalties won"
        "SHOTS_ON_TARGET": 1,    # "goal attempts" (Premio por subir al ataque)
    },

    # --- 5. MEDIOCENTROS (MID) ---
    "MID": {
        "GOALS": 5,
        "ASSISTS": 3,
        "CLEAN_SHEET": 1,        # Premio pequeño
        "SUCCESSFUL_DRIBBLES": 0.5, # "effective dribles"
        "ACCURATE_CROSSES": 0.5, # "balls into the box" (Balones al área)
        "BALL_RECOVERY": 0.5,    # "recoveries" (Vital para pivotes defensivos)
        "PENALTIES_WON": 2,
        "SHOTS_ON_TARGET": 1,    # "goal attempts"
    },

    # --- 6. DELANTEROS (FWD) ---
    "FWD": {
        "GOALS": 4,              # "goals" (Valen menos porque es su obligación)
        "ASSISTS": 3,
        "SHOTS_ON_TARGET": 1,    # "goal attempts"
        "SUCCESSFUL_DRIBBLES": 0.5, # "effective dribles"
        "PENALTIES_WON": 2,      # "penalties won"
        "ACCURATE_CROSSES": 0.5, # "balls into the box" (Extremos)
        "BALL_RECOVERY": 0.2,    # "recoveries" (Se premia menos porque presionan menos)
    }
}


# --- 7. FACTOR DE NOTA (RATING) ---
def calcular_puntos_por_nota(rating_sportmonks: float) -> float:
    """
    Convierte la nota de Sportmonks (0-10) en puntos Fantasy.
    
    Regla: Si la nota es menor de 5, suma 0 puntos.
    
    Args:
        rating_sportmonks: Nota del jugador (0-10)
        
    Returns:
        float: Puntos Fantasy correspondientes
        
    Ejemplos:
        >>> calcular_puntos_por_nota(8.5)
        4
        >>> calcular_puntos_por_nota(4.2)
        0
    """
    if rating_sportmonks >= 8.0:
        return 4  # Partidazo
    elif rating_sportmonks >= 7.0:
        return 3  # Muy bien
    elif rating_sportmonks >= 6.0:
        return 2  # Bien
    elif rating_sportmonks >= 5.0:
        return 1  # Aprobado raspado
    else:
        return 0  # Suspenso (< 5.0) -> 0 Puntos


def get_position_rules(position: str) -> dict:
    """
    Devuelve las reglas de puntuación específicas de una posición
    
    Args:
        position: Posición del jugador (GK, DEF, MID, FWD)
        
    Returns:
        dict: Reglas de puntuación para esa posición
    """
    position = position.upper()
    
    if position not in SCORING_RULES:
        raise ValueError(f"Posición no válida: {position}. Debe ser GK, DEF, MID o FWD")
    
    return SCORING_RULES[position]


def get_common_penalties() -> dict:
    """
    Devuelve las penalizaciones comunes para todas las posiciones
    
    Returns:
        dict: Penalizaciones aplicables a todos los jugadores
    """
    return {
        "YELLOWCARDS": SCORING_RULES["YELLOWCARDS"],
        "RED_CARD": SCORING_RULES["RED_CARD"],
        "OWN_GOALS": SCORING_RULES["OWN_GOALS"],
        "PENALTIES_MISSED": SCORING_RULES["PENALTIES_MISSED"],
        "PENALTIES_COMMITTED": SCORING_RULES["PENALTIES_COMMITTED"],
        "DISPOSSESSED": SCORING_RULES["DISPOSSESSED"],
        "GOALS_AGAINST": SCORING_RULES["GOALS_AGAINST"],
    }
