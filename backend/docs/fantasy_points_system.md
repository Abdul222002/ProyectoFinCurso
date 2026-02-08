# Sistema de Puntos Fantasy - Diferenciado por Posición

## 🎯 Filosofía del Sistema

**Premisa:** Un gol de un portero vale MUCHO más que un gol de delantero (es extraordinario)

---

## 📊 Tabla de Puntos por Posición

### GOLES ⚽

| Acción | GK | DEF | MID | FWD |
|--------|----|----|-----|-----|
| **Gol** | +10 | +7 | +5 | +4 |

**Razón:**
- GK marca gol = evento rarísimo = mega recompensa
- DEF marca gol = muy valioso
- MID marca gol = valioso
- FWD marca gol = su trabajo normal

### ASISTENCIAS 🎯

| Acción | GK | DEF | MID | FWD |
|--------|----|----|-----|-----|
| **Asistencia** | +5 | +4 | +3 | +2 |

**Razón:**
- GK/DEF hacer asistencia = jugada excepcional
- MID hacer asistencia = parte de su juego
- FWD hacer asistencia = su rol secundario

### PORTERÍA IMBATIDA 🧤

| Acción | GK | DEF | MID | FWD |
|--------|----|----|-----|-----|
| **Clean Sheet** | +4 | +3 | +1 | 0 |

**Razón:**
- GK/DEF = responsables directos de la defensa
- MID = contribución indirecta
- FWD = no relevante

### MINUTOS JUGADOS ⏱️

| Acción | Todos |
|--------|-------|
| 60+ minutos | +2 |
| 1-59 minutos | +1 |
| 0 minutos | 0 |

### NOTA DEL PARTIDO ⭐

| Nota | Todos |
|------|-------|
| 9.0+ | +5 |
| 8.0-8.9 | +3 |
| 7.0-7.9 | +1 |
| <7.0 | 0 |

### PENALIZACIONES ⚠️

| Acción | Todos |
|--------|-------|
| Tarjeta amarilla | -1 |
| Tarjeta roja | -3 |
| Gol en contra | -2 |
| Penalti fallado | -3 |

---

## 💻 Implementación en Código

```python
from enum import Enum

class Position(Enum):
    GK = "GK"
    DEF = "DEF"
    MID = "MID"
    FWD = "FWD"

# Tablas de puntos por posición
GOAL_POINTS = {
    Position.GK: 10,
    Position.DEF: 7,
    Position.MID: 5,
    Position.FWD: 4
}

ASSIST_POINTS = {
    Position.GK: 5,
    Position.DEF: 4,
    Position.MID: 3,
    Position.FWD: 2
}

CLEAN_SHEET_POINTS = {
    Position.GK: 4,
    Position.DEF: 3,
    Position.MID: 1,
    Position.FWD: 0
}


def calcular_puntos_fantasy(stats: PlayerGameweekStats, player: Player) -> int:
    """
    Calcula puntos fantasy diferenciados por posición
    """
    
    puntos = 0
    position = player.position
    
    # ========================================
    # GOLES (diferenciado por posición)
    # ========================================
    puntos += stats.goals * GOAL_POINTS[position]
    
    # ========================================
    # ASISTENCIAS (diferenciado por posición)
    # ========================================
    puntos += stats.assists * ASSIST_POINTS[position]
    
    # ========================================
    # MINUTOS JUGADOS (todos igual)
    # ========================================
    if stats.minutes_played >= 60:
        puntos += 2
    elif stats.minutes_played > 0:
        puntos += 1
    
    # ========================================
    # NOTA DEL PARTIDO (todos igual)
    # ========================================
    if stats.rating:
        if stats.rating >= 9.0:
            puntos += 5
        elif stats.rating >= 8.0:
            puntos += 3
        elif stats.rating >= 7.0:
            puntos += 1
    
    # ========================================
    # PORTERÍA IMBATIDA (diferenciado)
    # ========================================
    if stats.clean_sheet:
        puntos += CLEAN_SHEET_POINTS[position]
    
    # ========================================
    # PENALIZACIONES (todos igual)
    # ========================================
    puntos -= stats.yellow_cards * 1
    puntos -= stats.red_cards * 3
    puntos -= stats.own_goals * 2
    puntos -= stats.penalties_missed * 3
    
    return puntos
```

---

## 📊 Ejemplos Prácticos

### Ejemplo 1: Portero con gran partido

```
Kasper Schmeichel (GK)
- 90 minutos: +2
- Clean sheet: +4
- Nota 8.5: +3
= 9 puntos
```

### Ejemplo 2: Portero que marca gol!

```
Kasper Schmeichel (GK)
- 90 minutos: +2
- 1 gol: +10 (¡mega recompensa!)
- Clean sheet: +4
- Nota 9.2: +5
= 21 puntos (ESPECTACULAR!)
```

### Ejemplo 3: Defensa ofensivo

```
Roberto Carlos (DEF)
- 90 minutos: +2
- 1 gol: +7
- 1 asistencia: +4
- Clean sheet: +3
- Nota 8.8: +3
= 19 puntos
```

### Ejemplo 4: Centrocampista equilibrado

```
Xavi (MID)
- 90 minutos: +2
- 1 gol: +5
- 2 asistencias: +6 (3x2)
- Nota 8.2: +3
= 16 puntos
```

### Ejemplo 5: Delantero hat-trick

```
Ronaldo Nazário (FWD)
- 90 minutos: +2
- 3 goles: +12 (4x3)
- 1 asistencia: +2
- Nota 9.5: +5
= 21 puntos
```

### Ejemplo 6: Día muy malo con tarjeta roja

```
Sergio Ramos (DEF)
- 45 minutos: +1
- 1 tarjeta roja: -3
- Gol encajado (no clean sheet): 0
= -2 puntos (¡puede ser negativo!)
```

---

## 🎮 Comparativa: Sistema Antiguo vs Nuevo

### Gol de Portero

| Sistema | Puntos |
|---------|--------|
| Antiguo (todos igual) | +6 |
| **Nuevo (diferenciado)** | **+10** |

### Gol de Delantero

| Sistema | Puntos |
|---------|--------|
| Antiguo | +6 |
| **Nuevo** | **+4** (más balanceado) |

### Asistencia de Defensa

| Sistema | Puntos |
|---------|--------|
| Antiguo | +3 |
| **Nuevo** | **+4** (más valioso) |

---

## 📡 Datos de la API Necesarios

### Por cada jugador en cada partido:

```json
{
  "player_id": 2015,
  "minutes_played": 90,
  "goals": 1,
  "assists": 2,
  "yellowcards": 0,
  "redcards": 0,
  "rating": 8.5,
  "position": "MID"  // ← CRÍTICO para cálculo correcto
}
```

### Datos adicionales del partido:

```json
{
  "home_score": 2,
  "away_score": 0,
  "player_team": "Celtic"
}
```

**Para calcular Clean Sheet:**
- Si jugador es GK/DEF del equipo local y away_score = 0 → Clean sheet
- Si jugador es GK/DEF del equipo visitante y home_score = 0 → Clean sheet

---

## ✅ Ventajas del Sistema Diferenciado

1. **Más realista** → Premia acciones extraordinarias
2. **Más estratégico** → Porteros con clean sheets valen oro
3. **Más emocionante** → Un gol de portero = evento épico
4. **Más justo** → Delanteros no dominan siempre
5. **Más variado** → Diferentes posiciones tienen valor

---

## 🎯 Resultado en el Juego

Con este sistema:

- **Porteros consistentes** → Valiosos (clean sheets + notas altas)
- **Defensas ofensivos** → Muy valiosos (goles/asistencias raras)
- **Medios creativos** → Buenos (asistencias + control)
- **Delanteros goleadores** → Dependen de marcar mucho

**Ejemplo Top 10 de una jornada podría ser:**

1. Portero con clean sheet + nota 9 = 12 puntos
2. Defensa con gol + clean sheet = 16 puntos
3. Delantero con hat-trick = 20 puntos
4. Medio con 2 asistencias + gol = 15 puntos

¡Mucho más balanceado y emocionante!
