"""
Servicio de puntuación de iconos / leyendas por jornada.

Cada icono puntúa según su 'scoring_profile' y su rango [min_fantasy, max_fantasy].
Los puntos se generan aleatoriamente pero con distribuciones controladas:

  LEGEND   — Nunca 0. 85% en top 60% del rango, 15% en parte baja. Media alta.
  MAESTRO  — Min 2+. Normal centrada al 65% del rango. Algún bajón puntual.
  RELIABLE — Distribución estrecha alrededor del 55% del rango. Sin sorpresas.
  VOLCANO  — Bimodal: 20% hace 0, 65% cerca del max, 15% en zona media.
  CURSED   — 35% hace 0, 45% épico (top 30%), 20% zona media.
"""

import random


def calculate_icon_points(player) -> float:
    """
    Calcula los puntos fantasy de un icono para una jornada.
    
    Args:
        player: instancia de Player con scoring_profile, min_fantasy, max_fantasy.
    
    Returns:
        float con los puntos de la jornada (0.0 si no tiene perfil configurado).
    """
    profile = player.scoring_profile
    lo = player.min_fantasy
    hi = player.max_fantasy

    if not profile or lo is None or hi is None:
        return 0.0

    rng = hi - lo  # amplitud del rango

    if profile == "LEGEND":
        # 85% en top 60% del rango, 15% en parte baja — nunca 0
        if random.random() < 0.85:
            # Top 60% del rango
            pts = lo + rng * random.uniform(0.40, 1.0)
        else:
            # Parte baja (pero nunca 0 — tenemos suelo garantizado)
            pts = lo + rng * random.uniform(0.0, 0.40)

    elif profile == "MAESTRO":
        # Normal centrada al 65% del rango
        mean = lo + rng * 0.65
        std  = rng * 0.18
        pts = random.gauss(mean, std)
        pts = max(lo, min(hi, pts))  # clamp al rango

    elif profile == "RELIABLE":
        # Distribución muy estrecha alrededor del 55% del rango
        mean = lo + rng * 0.55
        std  = rng * 0.10
        pts = random.gauss(mean, std)
        pts = max(lo, min(hi, pts))

    elif profile == "VOLCANO":
        # Bimodal: 20% → 0, 65% → top 35%, 15% → zona media
        roll = random.random()
        if roll < 0.20:
            pts = 0.0
        elif roll < 0.85:  # 65% del total
            # Top 35% del rango
            pts = lo + rng * random.uniform(0.65, 1.0)
        else:
            # Zona media (20-65%)
            pts = lo + rng * random.uniform(0.20, 0.65)

    elif profile == "CURSED":
        # 35% → 0 (la maldición), 45% → épico (top 30%), 20% → zona media
        roll = random.random()
        if roll < 0.35:
            pts = 0.0
        elif roll < 0.80:  # 45% del total
            # Épico: top 30% del rango
            pts = lo + rng * random.uniform(0.70, 1.0)
        else:
            # Zona media (25-70%)
            pts = lo + rng * random.uniform(0.25, 0.70)

    else:
        # Perfil desconocido → media simple
        pts = (lo + hi) / 2.0

    return round(max(0.0, pts), 1)
