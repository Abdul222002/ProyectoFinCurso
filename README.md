# ⚽ Ultimate Fantasy Legends: Fusión de Rendimiento Real y Simulación Deportiva

> Plataforma web de gestión deportiva que fusiona las mecánicas clásicas de Fantasy Football con elementos de colección y estrategia de videojuegos como FIFA Ultimate Team y Pokémon

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2+-61DAFB.svg)](https://reactjs.org/)

**Alumno:** Abdul Hakim Byaz Iglesias (2º DAW)  
**Tipo de Proyecto:** Desarrollo Web Full-Stack (TFG)  
**Liga:** Scottish Premiership  

---

## 📋 Tabla de Contenidos

- [Introducción y Concepto](#-introducción-y-concepto)
- [Sistema de Iconos/Leyendas](#-sistema-de-iconosleyendas)
- [Sistema de Mercado y Equipos](#-sistema-de-mercado-y-equipos)
- [Mecánica de Juego Híbrida](#-mecánica-de-juego-híbrida)
- [Arquitectura Técnica](#-arquitectura-técnica-y-datos)
- [Stack Tecnológico](#-stack-tecnológico)
- [Instalación](#-instalación-y-setup)

---

## 🎯 Introducción y Concepto

**Ultimate Fantasy Legends** es una plataforma web de gestión deportiva que revoluciona el concepto tradicional de Fantasy Football al fusionar:

- **Fantasy Clásico**: Puntuación basada en rendimiento real de jugadores
- **Colección de Iconos**: Leyendas del fútbol (Pelé, Maradona, Ronaldo)
- **Mercado Diario**: Sistema de pujas ciegas estratégico
- **Gamificación**: Sobres exclusivos para leyendas

---

## ⭐ Sistema de Iconos/Leyendas

### Concepto

100 leyendas del fútbol mundial disponibles **solo mediante sobres**:

- **Pelé** (OVR 99)
- **Maradona** (OVR 99)
- **Ronaldo Nazário** (OVR 96)
- **Zidane** (OVR 95)
- Y 96 iconos más (OVR 85-99)

### Características Únicas

✅ **NO vendibles** → Exclusivos de colección  
✅ **NO únicos** → Varios usuarios pueden tener el mismo icono  
✅ **Rangos de rendimiento variables** → Cada icono tiene min/max fantasy points únicos

**Ejemplo:**
```
Casillas: 5-9 puntos (consistente)
Ronaldo Nazário: 2-16 puntos (genio o lesión)
Maradona: 6-19 puntos (impredecible)
```

### Probabilidades por OVR

| OVR | Tipo | Probabilidad | Ejemplos |
|-----|------|--------------|----------|
| 99 | Gods | 0.01% | Pelé, Maradona |
| 95-98 | Legends | 0.1% | Ronaldo, Zidane, Ronaldinho |
| 90-94 | Icons | 0.5% | Gerrard, Del Piero, Roberto Carlos |
| 85-89 | Heroes | 2% | Schweinsteiger, Puyol, Totti |

---

## 💰 Sistema de Mercado y Equipos

### 1️⃣ Equipo Inicial

Al crear una liga, cada usuario recibe:

- **14 jugadores aleatorios** (OVR 60-70)
- **€100M** de presupuesto inicial
- Distribución balanceada:
  - 2 GK
  - 4-5 DEF
  - 4-5 MID
  - 3-4 FWD

### 2️⃣ Mercado Diario

**Renovación cada 24 horas:**

- **10-12 jugadores** aparecen diariamente
- Pool incluye **todos los OVR** (60-90)

**Probabilidades:**
- 50% → OVR 60-70 (comunes)
- 35% → OVR 71-78 (buenos)
- 12% → OVR 79-85 (top)
- 3% → OVR 86-90 (estrellas)

### 3️⃣ Sistema de Pujas Ciegas

**Mecánica:**

1. **Pujas ocultas** → Nadie ve las ofertas de otros
2. **Duración:** 24 horas
3. **Ganador:** Mayor puja al finalizar
4. **Empate:** Orden de llegada (timestamp)
5. **Dinero bloqueado** durante la puja

**Ejemplo:**
```
Mercado: [Callum McGregor - OVR 90]

Usuario A: €25M (oculto)
Usuario B: €22M (oculto)
Usuario C: €30M (oculto) ← GANADOR tras 24h

→ Usuario C recibe a McGregor
→ A y B recuperan su dinero
```

### 4️⃣ Sobres

- **Solo iconos** (Pelé, Ronaldo, etc.)
- Probabilidad basada en OVR del icono
- Única forma de conseguir leyendas

---

## 🎮 Mecánica de Juego Híbrida

### A. La Liga Fantasy (Fin de Semana)

Basado en rendimiento real de la **Scottish Premiership**:

- **Fuente:** API Sportmonks
- **Puntuación:** Goles, asistencias, minutos, notas
- **Objetivo:** Premia conocimiento futbolístico real

### B. Sobres y Colección (Diario)

- Apertura de sobres para conseguir leyendas
- Gestión de inventario
- Construcción de plantilla ideal

### C. Mercado y Pujas (Diario)

- Estrategia de compra/venta
- Análisis de rendimiento de jugadores
- Pujas ciegas contra otros usuarios

---

## 🏗️ Arquitectura Técnica y Datos

### Stack Tecnológico

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│  React 18.2+ │ Vite 5.0+ │ Drag & Drop │ Animaciones      │
└─────────────────────────────────────────────────────────────┘
                            ▼ HTTP/JSON
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                              │
│  FastAPI │ Pydantic │ Swagger UI │ Algoritmos Propios      │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATA LAYER                              │
│  MySQL 8.0+ │ SQLAlchemy 2.0+ │ Sportmonks API             │
└─────────────────────────────────────────────────────────────┘
```

### Modelos de Base de Datos

#### Player (Jugadores e Iconos)
```python
- is_legend: Boolean (True para iconos)
- is_tradeable: Boolean (False para iconos)
- min_fantasy_points: Integer (rango mínimo)
- max_fantasy_points: Integer (rango máximo)
- overall_rating: Integer (60-99)
- current_price: Float (NULL para iconos)
```

#### League (Ligas Privadas)
```python
- code: String (código para unirse)
- initial_budget: Float (€100M default)
- daily_market_size: Integer (12 default)
```

#### MarketListing (Mercado Diario)
```python
- league_id: ForeignKey
- player_id: ForeignKey
- expires_at: DateTime (+24h)
- is_active: Boolean
- winner_user_id: ForeignKey (nullable)
```

#### Bid (Pujas)
```python
- listing_id: ForeignKey
- user_id: ForeignKey
- amount: Float (dinero bloqueado)
- is_winning: Boolean
```

---

## 🛠️ Stack Tecnológico

### Backend
| Tecnología | Versión | Propósito |
|-----------|---------| ----------|
| Python | 3.10+ | Lenguaje principal |
| FastAPI | 0.104+ | Framework web asíncrono |
| SQLAlchemy | 2.0+ | ORM |
| MySQL | 8.0+ | Base de datos relacional |
| Pydantic | 2.0+ | Validación de datos |

### Frontend
| Tecnología | Versión | Propósito |
|-----------|---------| ----------|
| React | 18.2+ | UI Library |
| Vite | 5.0+ | Build tool |

### APIs Externas
| Servicio | Propósito |
|----------| ----------|
| Sportmonks | Datos Scottish Premiership |

---

## 🚀 Instalación y Setup

### Prerrequisitos

- Python >= 3.10
- Node.js >= 18.0
- MySQL >= 8.0
- Cuenta en Sportmonks API

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Abdul222002/ProyectoFinCurso.git
cd ProyectoFinCurso
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env con credenciales

# Seed jugadores reales
python scripts/seed_fifa_only.py

# Seed iconos
python scripts/seed_icons.py

# Iniciar servidor
uvicorn app.main:app --reload
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Acceder a la Aplicación

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📊 Scripts Disponibles

### Backend

```bash
# Verificar estado de la BD
python backend/scripts/verificar_bd.py

# Distribuir equipos iniciales
python backend/scripts/distribute_initial_squads.py --league_id=1

# Refrescar mercado diario
python backend/scripts/refresh_daily_market.py --league_id=1

# Seed iconos
python backend/scripts/seed_icons.py
```

---

## 🎮 Flujo de Usuario

### 1. Crear Liga
```
Usuario → Crear Liga → Código: ABC123
       → Invitar amigos
```

### 2. Equipo Inicial
```
Sistema → Asigna 14 jugadores (OVR 60-70)
        → Presupuesto: €100M
```

### 3. Mercado Diario
```
Usuario → Ver 12 jugadores disponibles
        → Hacer puja ciega
        → Esperar 24h
        → Recibir jugador si ganó
```

### 4. Sobres
```
Usuario → Abrir sobre
        → Probabilidad de icono según OVR
        → Añadir a colección
```

---

## 📈 Roadmap Actualizado

### ✅ Fase 1: Base de Datos
- [x] 334 jugadores Scottish Premiership
- [x] Posiciones corregidas con FIFA
- [x] Rarezas ajustadas (33% GOLD)
- [x] Precios escala premium

### 🚧 Fase 2: Sistema de Iconos
- [ ] CSV con 100 iconos
- [ ] Seed script de iconos
- [ ] Rangos de fantasy points

### 📝 Fase 3: Sistema de Mercado
- [ ] Modelo League
- [ ] Modelo MarketListing
- [ ] Modelo Bid
- [ ] Script de equipos iniciales
- [ ] Script de mercado diario
- [ ] Servicio de pujas

### 🎨 Fase 4: Frontend
- [ ] UI de mercado diario
- [ ] UI de pujas ciegas
- [ ] UI de sobres
- [ ] UI de colección de iconos

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

---

## 👨‍💻 Autor

**Abdul Hakim Byaz Iglesias**
- 📧 Email: hakimbyaz@gmail.com
- 🎓 Curso: 2º DAW
- 📅 Año Académico: 2025-2026

---

## 🙏 Agradecimientos

- **Sportmonks** por proporcionar la API de datos deportivos
- **FastAPI** por el excelente framework
- **React** por facilitar el desarrollo del frontend

---

**¡Empieza a construir tu Ultimate Fantasy Legends hoy! ⚽🎮✨**