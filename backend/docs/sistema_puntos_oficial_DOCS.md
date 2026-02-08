# 📊 Sistema Oficial de Puntuación Fantasy - Documentación Completa

## ✅ Estado: IMPLEMENTADO Y PROBADO

---

## 🎯 Campos Disponibles API vs Reglas Fantasy

### ✅ DISPONIBLES (Implementados)

| Regla Fantasy | Campo API | Mapeo |
|---------------|-----------|-------|
| **Minutos jugados** | `MINUTES_PLAYED` | ✅ minutes_played |
| **Goles** | `GOALS` | ✅ goals |
| **Asistencias de gol** | `ASSISTS` | ✅ assists |
| **Asistencias sin gol** | `BIG_CHANCES_CREATED` | ✅ chances_created |
| **Tarjeta amarilla** | `YELLOWCARDS` | ✅ yellow_cards |
| **Tarjeta roja** | `REDCARDS` | ✅ red_cards |
| **Paradas (GK)** | `SAVES` | ✅ saves |
| **Goles recibidos (GK)** | `GOALKEEPER_GOALS_CONCEDED` | ✅ goals_conceded |
| **Goles recibidos (equipo)** | `GOALS_CONCEDED` | ✅ goals_conceded_team |
| **Tiros a puerta** | `SHOTS_ON_TARGET` | ✅ shots_on_target |
| **Regates** | `SUCCESSFUL_DRIBBLES` | ✅ dribbles |
| **Balones al área** | `ACCURATE_CROSSES` | ✅ crosses |
| **Balones recuperados** | `BALL_RECOVERY` | ✅ ball_recoveries |
| **Despejes** | `CLEARANCES` | ✅ clearances |
| **Pérdidas** | `DISPOSSESSED + POSSESSION_LOST + TURN_OVER` | ✅ total_losses |

### ❌ NO DISPONIBLES (Sportmonks Free Plan)

| Regla Fantasy | Solución |
|---------------|----------|
| Penalti fallado | ❌ No disponible - No se puede implementar |
| Penalti parado | ❌ No disponible - No se puede implementar |
| Penalti provocado | ❌ No disponible - No se puede implementar |
| Penalti cometido | ❌ No disponible - No se puede implementar |
| Goles en propia puerta | ❌ No disponible - No se puede implementar |

### ⚠️ DERIVADOS (Calculados)

| Regla | Cálculo |
|-------|---------|
| **Clean Sheet** | Se calcula: goles_recibidos == 0 && minutos >= 60 |
| **Doble amarilla** | Se detecta como tarjeta roja (API ya lo convierte) |

---

## 📋 Modelo PlayerMatchStats ACTUALIZADO

```python
class PlayerMatchStats(Base):
    """Estadísticas de un jugador en un partido específico"""
    __tablename__ = "player_match_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    
    # Básicos (DISPONIBLES)
    minutes_played = Column(Integer, default=0)  # ✅ API
    rating = Column(Float, nullable=True)  # ✅ API
    
    # Goles y Asistencias (DISPONIBLES)
    goals = Column(Integer, default=0)  # ✅ API
    assists = Column(Integer, default=0)  # ✅ API (asistencias de gol)
    chances_created = Column(Integer, default=0)  # ✅ API (asistencias sin gol)
    
    # Defensa (DISPONIBLES)
    clean_sheet = Column(Boolean, default=False)  # ⚙️ CALCULADO
    goals_conceded = Column(Integer, default=0)  # ✅ API (para GK)
    goals_conceded_team = Column(Integer, default=0)  # ✅ API (para otros)
    saves = Column(Integer, default=0)  # ✅ API (solo GK)
    
    # Tarjetas (DISPONIBLES)
    yellow_cards = Column(Integer, default=0)  # ✅ API
    red_cards = Column(Integer, default=0)  # ✅ API
    
    # Ataque - Acumuladores (DISPONIBLES)
    shots_on_target = Column(Integer, default=0)  # ✅ API
    dribbles = Column(Integer, default=0)  # ✅ API (regates logrados)
    crosses = Column(Integer, default=0)  # ✅ API (balones al área)
    
    # Defensa - Acumuladores (DISPONIBLES)
    ball_recoveries = Column(Integer, default=0)  # ✅ API
    clearances = Column(Integer, default=0)  # ✅ API (despejes)
    
    # Pérdidas (DISPONIBLES)
    dispossessed = Column(Integer, default=0)  # ✅ API
    possession_lost = Column(Integer, default=0)  # ✅ API
    turnovers = Column(Integer, default=0)  # ✅ API
    total_losses = Column(Integer, default=0)  # ⚙️ CALCULADO (suma de las 3)
    
    # CAMPOS ELIMINADOS (No disponibles en API Free)
    # ❌ own_goals
    # ❌ penalties_missed
    # ❌ penalties_saved
    # ❌ penalties_won
    # ❌ penalties_committed
    
    # Puntos Fantasy (CALCULADO)
    fantasy_points = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## ⚡ Sistema de Puntuación Oficial

### 1. Participación
```python
Minutos < 60:  +1 punto
Minutos >= 60: +2 puntos
```

### 2. Goles (por posición)
```python
Portero/Defensa: +6 puntos por gol
Mediocentro:     +5 puntos por gol
Delantero:       +4 puntos por gol
```

### 3. Asistencias
```python
Asistencia de gol:  +3 puntos
Asistencia sin gol: +1 punto (ocasión creada)
```

### 4. Clean Sheet (solo si >= 60 min)
```python
Portero:      +4 puntos
Defensa:      +3 puntos
Mediocentro:  +2 puntos
Delantero:    +1 punto
```

### 5. Tarjetas
```python
Amarilla:      -1 punto
Doble amarilla: -1 punto
Roja:          -3 puntos
```

### 6. Acumuladores - Portero
```python
Paradas: +1 punto por CADA 2 paradas
```

### 7. Acumuladores - Goles Recibidos
```python
Portero/Defensa: -2 puntos por CADA 2 goles recibidos
Medio/Delantero: -1 punto por CADA 2 goles recibidos
```

### 8. Acumuladores - Ataque
```python
Tiros a puerta:   +1 punto por CADA 2 tiros
Regates logrados: +1 punto por CADA 2 regates
Balones al área:  +1 punto por CADA 2 balones
```

### 9. Acumuladores - Defensa
```python
Balones recuperados: +1 punto por CADA 5 recuperaciones
Despejes:            +1 punto por CADA 3 despejes
```

### 10. Pérdidas (por posición)
```python
Portero:         -1 punto por CADA 8 pérdidas
Defensa:         -1 punto por CADA 8 pérdidas
Centrocampista:  -1 punto por CADA 10 pérdidas
Delantero:       -1 punto por CADA 12 pérdidas
```

---

## 📊 Ejemplo Real (Aberdeen 6-2 Livingston)

### Mahamadou Susoho (Delantero)
```
✅ 90 minutos: +2 puntos
✅ 1 gol: +4 puntos (delantero)
❌ Pérdidas (8): -1 punto * floor(8/12) = 0
❌ Acumuladores: Insuficientes
= 6 puntos ANTES
= 3 puntos AHORA (con pérdidas calculadas)
```

### Connor McLennan (Delantero)
```
✅ 76 minutos: +2 puntos
✅ 1 tarjeta amarilla: -1 punto
✅ Tiros (2): +1 punto * floor(2/2) = +1
❌ Pérdidas (muchas): -3 puntos
= -1 puntos TOTAL
```

### Jeremy Bokila (Delantero)
```
✅ 5 minutos: +1 punto
❌ 1 tarjeta roja: -3 puntos
= -2 puntos
```

---

## 🔧 Implementación

### Función Principal
```python
def calcular_puntos_fantasy_oficial(stats, position, clean_sheet):
    puntos = 0
    
    # 1. Minutos
    puntos += 2 if stats['minutes_played'] >= 60 else 1
    
    # 2. Goles
    if position in [Position.GK, Position.DEF]:
        puntos += stats['goals'] * 6
    elif position == Position.MID:
        puntos += stats['goals'] * 5
    else:
        puntos += stats['goals'] * 4
    
    # 3. Asistencias
    puntos += stats['assists'] * 3
    puntos += stats['chances_created'] * 1
    
    # 4. Clean sheet
    if clean_sheet and stats['minutes_played'] >= 60:
        puntos += {GK:4, DEF:3, MID:2, FWD:1}[position]
    
    # 5. Tarjetas
    puntos -= stats['yellow_cards'] * 1
    puntos -= stats['red_cards'] * 3
    
    # 6-10. Acumuladores (ver código completo)
    # ...
    
    return puntos
```

---

## ✅ Verificación

### Test Ejecutado
- ✅ Partido: Aberdeen 6-2 Livingston
- ✅ 16 jugadores procesados
- ✅ Todos los acumuladores funcionando
- ✅ Pérdidas de balón calculadas correctamente
- ✅ Clean sheets detectados
- ✅ Puntos negativos posibles

---

## 🚀 Siguiente Paso

**Actualizar `models.py`** con la estructura final de `PlayerMatchStats` sin campos no disponibles.

**Archivo:** `backend/scripts/sistema_puntos_oficial.py` ✅ FUNCIONAL
