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
- [Mecánica de Juego Híbrida](#-mecánica-de-juego-híbrida-la-innovación)
- [Arquitectura Técnica y Datos](#-arquitectura-técnica-y-datos)
- [Sistema de Economía y Mercado](#-sistema-de-economía-y-mercado)
- [Personalización y Gestión](#-personalización-y-gestión)
- [Objetivos del TFG](#-objetivos-del-tfg)
- [Stack Tecnológico](#-stack-tecnológico)
- [Referencias Principales](#-referencias-principales)

---

## 🎯 Introducción y Concepto

**Ultimate Fantasy Legends** es una plataforma web de gestión deportiva que revoluciona el concepto tradicional de Fantasy Football al fusionar:

- **Fantasy Clásico**: Puntuación basada en rendimiento real de jugadores
- **Colección de Cartas**: Sistema de sobres estilo FIFA Ultimate Team
- **Simulación de Combate**: Batallas PvP inspiradas en Pokémon
- **Gamificación**: Apertura de sobres "Gacha" y cartas de Leyenda

### 💡 La Innovación

Este proyecto nace de la necesidad de **modernizar el Fantasy tradicional** (Biwenger, Marca) añadiendo:

✨ **Capa de Gamificación**: Sistema de apertura de sobres con probabilidades ponderadas  
🎮 **Modo de Juego Diario**: Disfruta de la plataforma todos los días, no solo durante la jornada de liga  
⚔️ **Combates Simulados**: Usa tus cartas de Leyenda en batallas estratégicas  
📊 **Mercado Vivo**: Fluctuación dinámica de valores según rendimiento real  

---

## 🎮 Mecánica de Juego Híbrida (LA INNOVACIÓN)

Para resolver la monotonía de las ligas menores (como la Escocesa) y dar utilidad a las cartas de Leyenda, el juego se divide en **dos vertientes conectadas**:

### A. La Liga Fantasy (Modo PVE - Fin de Semana)

**Funcionamiento:** Basado en la realidad. Los usuarios alinean a sus jugadores de la Scottish Premiership.

- **Fuente de Datos**: API de Sportmonks (Plan Free)
- **Sistema de Puntuación**: Datos en tiempo real de partidos
  - ⚽ Goles
  - 🎯 Asistencias
  - ⏱️ Minutos jugados
  - 🏃 Regates completados
  - ⭐ Nota del partido
- **Objetivo**: Premia el conocimiento futbolístico real del usuario

### B. La Arena de Batalla (Modo PVP - Entre Semana)

**Concepto "Estilo Pokémon":** Aquí es donde las medias (OVR) cobran sentido. Los usuarios enfrentan sus plantillas en una simulación 1vs1.

#### 🎲 Algoritmo de Simulación

Sistema donde la probabilidad de victoria depende de la media global del equipo:

**Ejemplo:**
```
Equipo A (Media 90) vs Equipo B (Media 80)
→ Equipo A tiene 70% de probabilidad de victoria
→ Factor suerte (dado virtual) siempre deja margen a la sorpresa
```

#### 🏆 Justificación de las Leyendas

Este modo permite usar **cartas de jugadores históricos** (ej: Ronaldo, Zidane) que no juegan en la vida real pero tienen stats muy altas para los combates simulados.

---

## 🏗️ Arquitectura Técnica y Datos

### Stack Tecnológico Seleccionado

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    React     │  │     Vite     │  │  Drag & Drop │     │
│  │   (SPA)      │  │   (Build)    │  │  (Alineación)│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │   Animaciones de Apertura de Sobres             │     │
│  └──────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ▼ HTTP/JSON
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   FastAPI    │  │   Pydantic   │  │  Swagger UI  │     │
│  │  (Asíncrono) │  │ (Validación) │  │    (Docs)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │    Algoritmos Propios (Simulación + Mercado)     │     │
│  └──────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATA LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    MySQL     │  │  SQLAlchemy  │  │ Sportmonks   │     │
│  │  (Relacional)│  │     (ORM)    │  │     API      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 🛠️ Justificación Tecnológica

#### Backend: Python con FastAPI

**¿Por qué FastAPI en lugar de Flask o Django?**

✅ **Velocidad**: Asíncrono por defecto  
✅ **Validación Automática**: Pydantic integrado  
✅ **Documentación Nativa**: Swagger UI/ReDoc  
✅ **Ideal para**: Algoritmos de simulación y conexión con API externa  

#### Frontend: React (con Vite)

**¿Por qué React?**

✅ **SPA Dinámica**: Interfaz reactiva y fluida  
✅ **Drag & Drop**: Gestión de alineaciones intuitiva  
✅ **Animaciones**: Apertura de sobres espectacular  
✅ **Vite**: Build ultra-rápido  

#### Base de Datos: MySQL

**¿Por qué MySQL?**

✅ **Naturaleza Relacional**: Usuarios ↔ Equipos ↔ Cartas ↔ Mercado  
✅ **Integridad Transaccional**: Evita duplicidad de ítems  
✅ **Confiabilidad**: Garantiza consistencia en economía  

#### ORM: SQLAlchemy

**¿Por qué SQLAlchemy?**

✅ **Integración Python**: Gestión OOP de objetos del juego  
✅ **Migraciones**: Evolución del schema  
✅ **Queries Complejas**: Ideal para estadísticas y rankings  

---

## 📊 Origen de los Datos (Solución Técnica)

### ❌ Descartado: Web Scraping
Inestable, ilegal, y propenso a errores.

### ✅ Solución: API Oficial de Sportmonks

**Liga:** Scottish Premiership

**Datos Disponibles (JSON):**

- ✅ Alineaciones y minutos jugados
- ✅ Eventos (Goles, Tarjetas)
- ✅ Estadísticas avanzadas (Regates/Dribbles)
- ✅ Notas de los jugadores

**Ventajas:**
- Legal y oficial
- Formato JSON estructurado
- Actualizaciones en tiempo real
- Documentación completa

---

## 📈 Algoritmo de Fluctuación de Medias (Dynamic Rating)

Para simular el mercado del FIFA, las medias de los jugadores **no serán estáticas**.

### 🔄 Recalculo Semanal (Backend)

```python
# Pseudocódigo del algoritmo
if partido.nota >= 8.0 or jugador.goles > 0:
    jugador.media += randint(1, 2)  # ⬆️ Sube media
elif partido.nota < 5.0 or not jugador.jugo:
    jugador.media -= randint(1, 2)  # ⬇️ Baja media
```

**Resultado:** Mercado vivo y especulativo 📊

---

## 💰 Sistema de Economía y Mercado

### 📈 Mercado de Valores (Oferta y Demanda)

El precio de los jugadores **no será fijo**. Algoritmo de bolsa:

- 🔴 **Alta Demanda**: Si muchos usuarios compran a Kevin Nisbet → Precio ⬆️
- 🔵 **Baja Demanda**: Si muchos usuarios venden → Precio ⬇️

### 🎁 Sistema "Gacha" (Sobres)

**Tienda de Sobres con Probabilidades Ponderadas:**

| Tipo de Carta | Probabilidad | Descripción |
|--------------|--------------|-------------|
| 🌟 Leyenda   | 1%           | Ronaldo, Zidane, Messi |
| 🥇 Oro       | 10%          | Jugadores top de la liga |
| 🥈 Plata     | 89%          | Jugadores comunes |

**Emoción de la aleatoriedad + Colección adictiva**

---

## 🎨 Personalización y Gestión

A diferencia de un Fantasy plano, aquí el usuario ejerce de **"Manager Total"**:

### 🏟️ Creación de Club

- 📝 Nombre del club
- 🛡️ Escudo personalizado
- 👕 Equipación

### 📋 Gestión de Plantilla

- ⭐ Alineación titular
- 💺 Banquillo
- 🔄 Cambios automáticos (si un titular no juega)

---

## 🎯 Objetivos del TFG

### 1️⃣ Integración de APIs Externas
✅ Consumo y normalización de datos JSON de Sportmonks  
✅ Manejo de errores y rate limiting  

### 2️⃣ Desarrollo de Algoritmos Propios
✅ Lógica de simulación de partidos (PvP)  
✅ Cálculo de fluctuación de mercado  
✅ Sistema de probabilidades para sobres  

### 3️⃣ Base de Datos Compleja
✅ Gestión de usuarios  
✅ Inventarios de cartas  
✅ Historial de partidos  
✅ Mercado en tiempo real  

### 4️⃣ Experiencia de Usuario (UX)
✅ Interfaz adictiva  
✅ Datos estadísticos + Elementos visuales de videojuego  
✅ Cartas brillantes  
✅ Animaciones de sobres  

---

## 🛠️ Stack Tecnológico

### Backend
| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| ![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python) | 3.10+ | Lenguaje principal |
| ![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?logo=fastapi) | 0.104+ | Framework web asíncrono |
| ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red) | 2.0+ | ORM |
| ![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?logo=mysql) | 8.0+ | Base de datos |
| ![Pydantic](https://img.shields.io/badge/Pydantic-2.0+-E92063) | 2.0+ | Validación de datos |

### Frontend
| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| ![React](https://img.shields.io/badge/React-18.2+-61DAFB?logo=react) | 18.2+ | UI Library |
| ![Vite](https://img.shields.io/badge/Vite-5.0+-646CFF?logo=vite) | 5.0+ | Build tool |
| ![TailwindCSS](https://img.shields.io/badge/Tailwind-3.0+-06B6D4?logo=tailwindcss) | 3.0+ (opcional) | Estilos |

### APIs Externas
| Servicio | Propósito |
|----------|-----------|
| ![Sportmonks](https://img.shields.io/badge/Sportmonks-API-orange) | Datos en tiempo real de Scottish Premiership |

---

## 🎮 Referencias Principales

### Fantasy Clásico
- **Biwenger**: Mercado de fichajes y puntuación basada en partidos reales
- **Marca Fantasy**: Sistema de puntos por rendimiento

### Simulación y Gestión
- **Online Soccer Manager (OSM)**: Personalización profunda de club, estadio y tácticas

### Colección y Cartas
- **FIFA Ultimate Team**: Sistema de cartas, medias (OVR) y apertura de sobres
- **Kings League**: Gamificación deportiva moderna

### Combate y Estrategia
- **Pokémon**: Mecánicas de combate por turnos y probabilidades

---

## 📁 Estructura del Proyecto

```
ProyectoFinCurso/
├── backend/                    # API FastAPI
│   ├── app/
│   │   ├── api/               # Endpoints
│   │   │   ├── auth.py
│   │   │   ├── players.py
│   │   │   ├── market.py
│   │   │   └── simulation.py
│   │   ├── core/              # Configuración
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── player.py
│   │   │   └── team.py
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Lógica de negocio
│   │   │   ├── simulation_engine.py
│   │   │   ├── market_algorithm.py
│   │   │   └── sportmonks_client.py
│   │   └── main.py
│   ├── alembic/               # Migraciones DB
│   └── requirements.txt
│
├── frontend/                   # React + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── cards/         # Cartas de jugadores
│   │   │   ├── packs/         # Apertura de sobres
│   │   │   └── lineup/        # Alineación drag & drop
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Market.jsx
│   │   │   ├── Arena.jsx
│   │   │   └── MyTeam.jsx
│   │   ├── services/          # API calls
│   │   └── App.jsx
│   └── package.json
│
├── docs/                       # Documentación TFG
│   ├── memoria.pdf
│   ├── presentacion.pptx
│   └── diagramas/
│
└── README.md
```

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
# Editar .env con tus credenciales de MySQL y Sportmonks API

# Ejecutar migraciones
alembic upgrade head

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
- **API Docs (Swagger)**: http://localhost:8000/docs

---

## 📊 Roadmap de Desarrollo

### Fase 1: Fundamentos (Semanas 1-4)
- [ ] Setup del proyecto
- [ ]  Configuración de BD MySQL
- [ ] Sistema de autenticación JWT
- [ ] Integración con Sportmonks API
- [ ] CRUD básico de usuarios y equipos

### Fase 2: Mecánica Fantasy (Semanas 5-8)
- [ ] Sistema de puntuación en tiempo real
- [ ] Gestión de alineaciones
- [ ] Cálculo de puntos por jornada
- [ ] Ranking de usuarios

### Fase 3: Sistema de Cartas (Semanas 9-12)
- [ ] Algoritmo de generación de sobres
- [ ] Animación de apertura de sobres
- [ ] Inventario de cartas
- [ ] Sistema de medias (OVR)

### Fase 4: Arena de Batalla (Semanas 13-16)
- [ ] Algoritmo de simulación PvP
- [ ] Sistema de combate probabilístico
- [ ] Historial de batallas
- [ ] Rankings de arena

### Fase 5: Mercado (Semanas 17-20)
- [ ] Algoritmo de fluctuación de precios
- [ ] Sistema de oferta/demanda
- [ ] Transacciones entre usuarios
- [ ] Historial de mercado

### Fase 6: Pulido y Deploy (Semanas 21-24)
- [ ] Optimización de rendimiento
- [ ] Testing E2E
- [ ] Documentación final
- [ ] Deployment en producción

---

## 🧪 Testing

```bash
# Backend
cd backend
pytest tests/ -v --cov=app

# Frontend
cd frontend
npm run test
npm run test:e2e
```

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

---

## 👨‍💻 Autor

**Abdul Hakim Byaz Iglesias**
- 📧 Email: hakimbyaz@gmail.com
- 🎓 Curso: 2º DAW
- 🏫 Centro: [Tu Centro Educativo]
- 📅 Año Académico: 2025-2026

---

## 🙏 Agradecimientos

- **Sportmonks** por proporcionar la API de datos deportivos
- **FastAPI** por el excelente framework
- **React** por facilitar el desarrollo del frontend
- A todos los que apoyan este proyecto

---

**¡Empieza a construir tu Ultimate Fantasy Legends hoy! ⚽🎮✨**