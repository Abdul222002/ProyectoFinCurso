# Ultimate Fantasy Legends: Scottish Premiership

> **Trabajo de Fin de Grado** — Plataforma de Fantasy Football con mecánicas de mercado financiero, simulación PvP y datos reales de la Scottish Premiership.

![Version](https://img.shields.io/badge/version-1.0.0-gold.svg)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/Frontend-React-61DAFB.svg?style=for-the-badge&logo=react)
![Docker](https://img.shields.io/badge/Deployment-Docker-2496ED.svg?style=for-the-badge&logo=docker)
![MySQL](https://img.shields.io/badge/Database-MySQL-4479A1.svg?style=for-the-badge&logo=mysql)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=for-the-badge&logo=python)

---

## Índice

1. [Resumen Ejecutivo](#-resumen-ejecutivo)
2. [Arquitectura del Sistema](#-arquitectura-del-sistema)
3. [Stack Tecnológico y Justificación](#-stack-tecnológico-y-justificación)
4. [Funcionalidades Principales](#-funcionalidades-principales)
5. [Modelo de Datos y Diagrama ER](#-modelo-de-datos)
6. [Motor de Puntuación](#-motor-de-puntuación)
7. [Ingeniería Económica](#-ingeniería-económica)
8. [Arena PvP](#-arena-pvp)
9. [Estructura del Proyecto](#-estructura-del-proyecto)
10. [API Reference](#-api-reference)
11. [Instalación y Despliegue](#-instalación-y-despliegue)
12. [Capturas de Pantalla](#-capturas-de-pantalla)
13. [Guía de Contribución](#-guía-de-contribución)
14. [Trabajo Futuro](#-trabajo-futuro)
15. [Licencia](#-licencia)

---

## Resumen Ejecutivo

### ¿Qué es Ultimate Fantasy Legends?

Ultimate Fantasy Legends (UFL) es una **plataforma de fantasy football** basada en la **Scottish Premiership** (la primera división del fútbol escocés) que va mucho más allá de lo que ofrecen las aplicaciones tradicionales de este tipo. Mientras que la mayoría de las plataformas de fantasy se limitan a asignar puntos según el rendimiento real de los jugadores y mostrar una clasificación, UFL crea un **ecosistema completo de gestión deportiva** que integra economía virtual, mercado de fichajes, combate entre usuarios y datos en tiempo real.

### El Problema que Resuelve

Las plataformas de fantasy football existentes presentan varias limitaciones que UFL aborda:

1. **Pasividad del usuario**: En un fantasy tradicional, el usuario elige su equipo una vez por jornada y espera. No hay interacción entre jornadas. UFL resuelve esto con un **mercado activo 24/7** donde las subastas diarias, las ventas entre usuarios y los clausulazos mantienen la tensión constante.

2. **Falta de estrategia financiera**: Los fantasy clásicos tienen un presupuesto fijo. UFL introduce un **sistema económico dinámico** donde cada decisión de compra/venta/blindaje tiene consecuencias a largo plazo, creando una capa de estrategia adicional.

3. **Competición limitada a la liga**: UFL añade la **Arena PvP**, donde tu equipo puede enfrentarse a cualquier otro equipo de la plataforma en simulaciones asíncronas, con un sistema de ranking ELO global.

4. **Desconexión con la realidad**: Gracias a la integración con **Sportmonks API**, las estadísticas de cada partido real de la Scottish Premiership se ingestan automáticamente y se traducen en puntos fantasy, creando un vínculo directo entre el fútbol real y el juego.

### Los Tres Pilares de UFL

**Pilar 1: Mercado Cíclico y Renovado**

Cada liga cuenta con un **mercado de subastas que se renueva cada 24 horas** de forma automática. En cada ciclo se ofrecen **12 jugadores aleatorios** del catálogo de la Scottish Premiership. Los precios de los jugadores son **estables** (fijados en el catálogo de datos) y no fluctúan dinámicamente, lo que simplifica la estrategia: el foco está en decidir **cuándo pujar** y **cuánto ofrecer** por cada jugador, en lugar de intentar aprovechar oscilaciones de precio. Esto crea un mercado accesible y predecible donde la toma de decisiones se centra en la teoría de juegos (subasta ciega) y la gestión de recursos (monedas limitadas).

**Pilar 2: Arena PvP con Ranking ELO**

La Arena permite simular enfrentamientos entre equipos de cualquier usuario de la plataforma. El algoritmo compara las líneas (ataque vs defensa, mediocampo vs mediocampo), aplica bonificadores por sinergias (jugadores del mismo club o nacionalidad) y genera un resultado. Cada batalla afecta al **ELO global** del usuario, creando un ranking competitivo que trasciende las ligas individuales.

**Pilar 3: Datos Reales en Tiempo Real**

La integración con **Sportmonks API** permite ingestar estadísticas reales de cada partido de la Scottish Premiership: goles, asistencias, tarjetas, porterías a cero, salvamentos, tackles, pases precisos, duelos ganados, y más de 25 métricas diferentes. Estas estadísticas se procesan a través del motor de puntuación y se traducen en puntos fantasy, que a su vez se convierten en monedas (1 punto = 100.000 monedas) que alimentan la economía del mercado.

### Tecnologías Clave

El proyecto utiliza una **arquitectura de microservicios dockerizada** con tres contenedores principales:

- **Frontend**: React 18 + Vite, servido por Nginx (puerto 3000)
- **Backend**: FastAPI con Uvicorn, incluyendo un scheduler APScheduler para tareas automatizadas (puerto 8000)
- **Base de datos**: MySQL 8.0 con inicialización automática desde script SQL (puerto 3306)

El scheduler es el "corazón" del sistema: se encarga de resolver subastas expiradas, generar nuevas subastas cíclicas, calcular los puntos de las jornadas, crear ofertas del sistema automáticamente, y sincronizar datos con la API de Sportmonks, todo sin intervención humana.

---

## Arquitectura del Sistema

### Visión General de la Infraestructura

El sistema está diseñado como una **arquitectura de tres capas** completamente contenedorizada con Docker Compose. Cada capa vive en su propio contenedor y se comunica con las demás a través de la red interna de Docker.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DOCKER NETWORK                              │
│                                                                     │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │   Frontend   │────>│   Backend    │────>│   MySQL 8.0  │        │
│  │ React + Vite │     │   FastAPI    │     │              │        │
│  │   (Nginx)    │     │  Uvicorn     │     │  ultimate_   │        │
│  │   :3000      │     │   :8000      │     │  fantasy_    │        │
│  │              │     │              │     │  legends     │        │
│  └──────────────┘     └──────┬───────┘     └──────────────┘        │
│                              │                                     │
│                    ┌─────────┴─────────┐                           │
│                    │   APScheduler     │                           │
│                    │                   │                           │
│                    │  • Resolución subastas                          │
│                    │  • Nuevas subastas cíclicas                      │
│                    │  • Sync Sportmonks│                           │
│                    │  • Cálculo jornadas                           │
│                    └───────────────────┘                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────┐          │
│  │  Servicios Externos                                   │          │
│  │  • Sportmonks API (datos reales de partidos)         │          │
│  │  • SMTP (verificación de email por OTP)              │          │
│  └──────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

**Explicación de cada componente:**

- **Frontend (React + Vite + Nginx)**: Es la interfaz que ve el usuario. Vite se usa en desarrollo para hot-reloading instantáneo. En producción, se compila a archivos estáticos que Nginx sirve. Nginx también actúa como proxy inverso para las rutas `/api/` y `/static/`, redirigiéndolas al backend.

- **Backend (FastAPI + Uvicorn)**: Es el cerebro de la aplicación. Expone una API REST con más de 50 endpoints documentados con Swagger UI. FastAPI fue elegido por su rendimiento asíncrono (basado en Starlette) y su sistema de validación de datos con Pydantic. Uvicorn es el servidor ASGI que ejecuta la aplicación.

- **MySQL 8.0**: Almacena todos los datos persistentes: usuarios, jugadores, equipos, ligas, subastas, batallas, etc. Al iniciar el contenedor por primera vez, ejecuta automáticamente el script `ultimate_fantasy_legends.sql` que crea todas las tablas, vistas, índices y datos semilla (1000+ jugadores).

 - **APScheduler**: Es un scheduler integrado en el backend que se inicia junto con FastAPI. Ejecuta tareas periódicas en segundo plano sin necesidad de herramientas externas como Celery o cron. Sus funciones principales son:
   - **Cierre de subastas**: Cada 5 minutos, identifica las subastas que han terminado y están pendientes de resolución, determina los ganadores, transfiere las cartas y devuelve el dinero a los perdedores.
   - **Creación de nuevas subastas**: Cuando una subasta se resuelve, genera automáticamente la siguiente con 12 nuevos jugadores aleatorios.
   - **Sync con Sportmonks**: Consulta la API externa para obtener resultados y estadísticas de partidos reales.
   - **Cálculo de jornadas**: Al finalizar una jornada real, calcula los puntos de cada alineación y los añade al saldo de los usuarios.
   - **Ofertas del sistema**: Genera automáticamente ofertas del sistema para listados de venta sin comprador tras 24 horas.
   - **Reconciliación económica**: Verifica periódicamente que los `locked_coins` de todos los miembros coincidan con sus pujas activas reales.

### Flujo de Datos Completo

El siguiente diagrama muestra cómo viaja la información desde un partido real hasta la pantalla del usuario:

```
┌─────────────┐
│ Sportmonks  │  API externa que proporciona estadísticas
│    API      │  de cada partido de la Scottish Premiership
└──────┬──────┘
       │  HTTP GET → JSON con stats de cada jugador
       ▼
┌─────────────────┐
│   Scheduler     │  Tarea programada que consulta la API
│  (Ingesta)      │  al finalizar cada partido real
└──────┬──────────┘
       │  Parsea JSON → Mapea a modelo PlayerMatchStats
       ▼
┌───────────────────────┐
│  PlayerMatchStats     │  Tabla con 28+ campos:
│  (28+ métricas)       │  goles, asistencias, tackles,
│                       │  pases, duelos, tarjetas, etc.
└──────┬────────────────┘
       │
       ▼
┌───────────────────────┐
│  Scoring Calculator   │  Aplica las reglas de puntuación
│                       │  según posición del jugador:
│                       │  - Gol delantero = 4 pts
│                       │  - Gol defensa = 6 pts
│                       │  - Portería a cero = 4 pts
│                       │  - etc.
└──────┬────────────────┘
       │
       ├─────────────────────────────────────┐
       ▼                                     ▼
┌─────────────────┐              ┌──────────────────┐
│ GameweekLineup  │              │  Market Auction  │  Cada 24h se crean
│  (Snapshot de   │              │  (Cíclica)       │  12 jugadores nuevos
│   alineación)   │              │                  │  aleatorios con precios
└──────┬──────────┘              │  estables         │
       │                         └────────┬─────────┘
       │ Puntos totales del equipo        │
       ▼                                 │
┌─────────────────┐                      │
│  Coins del      │                      │
│  Usuario        │                      │
│  (pts × 100K)   │                      │
└──────┬──────────┘                      │
       │                                 │
       └──────────────┬──────────────────┘
                      ▼
              ┌───────────────┐
              │   MERCADO     │  Subastas ciegas, ventas
              │               │  entre usuarios, clausulazos
              └───────────────┘
```

**Ejemplo práctico del flujo:**

1. Un partido real entre **Celtic vs Rangers** termina 2-1.
2. El scheduler consulta la API de Sportmonks y obtiene que **Kyogo Furuhashi** (delantero del Celtic) marcó 2 goles, dio 1 asistencia y jugó 85 minutos.
3. Estas stats se guardan en `player_match_stats`.
4. El scoring calculator aplica las reglas:
   - 85 minutos: 1 pt (jugado) + 2 pts (60+ min) = 3 pts
   - 2 goles como delantero: 2 × 4 pts = 8 pts
   - 1 asistencia como delantero: 3 pts
   - Total: **14 puntos fantasy**
5. Si un usuario tiene a Kyogo en su alineación, recibe 14 × 100.000 = **1.400.000 monedas**.
6. Esas monedas pueden usarse en el mercado de subastas, donde cada 24h aparecen 12 nuevos jugadores disponibles con precios estables.

---

## Stack Tecnológico y Justificación

Cada tecnología fue seleccionada no por moda, sino por su capacidad de resolver problemas específicos de la lógica de negocio. A continuación se detalla el porqué de cada elección.

### Backend

| Tecnología | Versión | Propósito | Justificación |
|---|---|---|---|
| **Python** | 3.10+ | Lenguaje principal | Permite manipulación de datos compleja (cálculos de puntuación, lógica de mercado) con código legible. Librerías maduras para todo lo necesario. |
| **FastAPI** | Latest | Framework HTTP asíncrono | La latencia en las pujas de mercado es inaceptable. FastAPI ofrece rendimiento cercano a Node.js/Go, pero con la potencia de Python. Basado en Starlette para async y Pydantic para validación. |
| **SQLAlchemy** | 2.x | ORM | Permite definir los 20+ modelos de datos de forma declarativa. Las relaciones complejas (User→Team→UserCard→Player) se gestionan de forma elegante. |
| **PyMySQL** | Latest | Driver MySQL | Driver puro de Python para MySQL. No requiere compilación de librerías C, lo que facilita el despliegue en Docker. |
| **Pydantic** | 2.x | Validación de datos | Valida automáticamente cada request entrante. Si un usuario envía un tipo incorrecto (ej: string donde va un integer), FastAPI rechaza la petición antes de que toque la base de datos. |
| **APScheduler** | Latest | Tareas programadas | Ejecuta el cierre de subastas, cálculo de jornadas, generación de ofertas del sistema y reconciliación económica sin necesidad de servicios externos como Celery + Redis. Más simple para este caso de uso. |
| **python-jose** | Latest | JWT | Genera y verifica tokens JWT para autenticación. Los tokens incluyen el user_id y el rol, permitiendo verificación rápida sin consultar la BD en cada request. |
| **passlib + bcrypt** | Latest | Hash de contraseñas | Almacena las contraseñas hasheadas con bcrypt, que es resistente a ataques de fuerza bruta. Cada contraseña tiene su propio salt. |
| **httpx** | Latest | Cliente HTTP async | Se usa para las llamadas a la API de Sportmonks. Al ser asíncrono, no bloquea el servidor mientras espera la respuesta externa. |

### Frontend

| Tecnología | Versión | Propósito | Justificación |
|---|---|---|---|
| **React 18** | 18.x | Biblioteca de UI | Necesitábamos una SPA que gestionara estados complejos: mercado en tiempo real, alineaciones con validación de formación, modales de puja, etc. El sistema de componentes de React permite reutilizar UI de forma eficiente. |
| **Vite** | 5.x | Bundler y dev server | Proporciona hot-reloading instantáneo (menos de 1 segundo). En producción, genera un bundle optimizado con tree-shaking y code-splitting. |
| **Axios** | Latest | Cliente HTTP | Permite configurar interceptores globales: añade automáticamente el token JWT a cada request y maneja los errores 401 redirigiendo al login. |
| **React Router 6** | 6.x | Enrutamiento | Gestiona la navegación entre las 15+ páginas de la aplicación sin recargar el navegador. Soporta parámetros de URL (ej: `/leagues/3?tab=market`). |
| **Sonner** | Latest | Notificaciones toast | Proporciona notificaciones elegantes y no intrusivas para confirmar acciones (puja realizada, equipo guardado, etc.) con soporte para acciones de undo. |
| **Vanilla CSS** | — | Estilos | Se eligió CSS puro en lugar de frameworks como Tailwind o Bootstrap para tener control total sobre el diseño. El sistema de **tokens CSS** (variables) permite gestionar el tema oscuro, colores dorados y transiciones de forma centralizada. |

### Infraestructura

| Tecnología | Propósito | Justificación |
|---|---|---|
| **Docker Compose** | Orquestación de 3 servicios | Garantiza que el entorno de desarrollo sea idéntico al de producción. Elimina el clásico "en mi máquina funciona". Un solo comando (`docker compose up`) levanta toda la aplicación. |
| **MySQL 8.0** | Base de datos relacional | Las transacciones ACID son esenciales para la economía del juego. Si falla la transferencia de dinero al comprar un jugador, la operación se revierte completamente (rollback). MySQL 8.0 ofrece rendimiento robusto para este volumen de datos. |
| **Nginx** | Servidor web + proxy | Sirve los archivos estáticos del frontend compilado y actúa como proxy inverso para las rutas `/api/` y `/static/` hacia el backend. Maneja la compresión gzip y caching de assets. |
| **Uvicorn** | Servidor ASGI | Ejecuta la aplicación FastAPI con soporte para async/await. En producción puede correr con múltiples workers para manejar peticiones concurrentes. |

---

## Funcionalidades Principales

### 1. Autenticación y Gestión de Usuarios

El sistema de autenticación está diseñado para ser seguro pero accesible:

- **Registro con verificación OTP por email**: Cuando un usuario se registra, no recibe un token de acceso inmediatamente. En su lugar, recibe un código de 6 dígitos por email que debe introducir en la pantalla de verificación. Esto previene cuentas falsas y spam. Solo tras verificar el email se activa la cuenta y se genera el JWT.

- **JWT (JSON Web Tokens)**: Una vez autenticado, el usuario recibe un token JWT que se almacena en `localStorage`. Este token se envía automáticamente en el header `Authorization: Bearer <token>` de cada petición al backend. El token contiene el `user_id` y el `role` del usuario, lo que permite al backend verificar permisos sin consultar la base de datos en cada request.

- **Roles con permisos diferenciados**:
  - `free`: Usuario estándar. Puede crear ligas, pujar en subastas, combatir en la Arena.
  - `premium`: Rol reservado para futuras funcionalidades premium.
  - `admin`: Acceso al panel de administración con herramientas de gestión global (editar jugadores, ajustar economías, eliminar usuarios/ligas).

- **Perfil editable**: El usuario puede cambiar su username, subir un avatar (por URL), y ver sus estadísticas globales (ELO, victorias, derrotas, ligas activas).

### 2. Sistema de Ligas Privadas

Las ligas son el núcleo social de la aplicación. Cada liga es un espacio cerrado donde un grupo de usuarios compite entre sí:

- **Creación**: Al crear una liga, el usuario establece un nombre, descripción y número máximo de miembros (de 4 a 20). El sistema genera automáticamente un **código de invitación único** de 8 caracteres (ej: `A7K2M9P3`).

- **Invitaciones**: Se pueden invitar usuarios de dos formas:
  - **Por username**: Se busca al usuario por su nombre de usuario dentro de la plataforma. Recibe una notificación interna que puede aceptar o rechazar.
  - **Por email externo**: Se envía una invitación por email a alguien que aún no tiene cuenta. Si esa persona se registra, se le asigna automáticamente a la liga.

- **Gestión de miembros**: El propietario de la liga (y los admins de la liga) pueden expulsar miembros. Cualquier miembro puede abandonar la liga voluntariamente.

- **Clasificación**: Los miembros se ordenan por `league_points` (puntos fantasy acumulados en esa liga). Los tres primeros puestos se destacan visualmente con bordes dorado, plateado y bronce.

- **Asignación inicial de jugadores**: Al unirse a una liga, el sistema asigna automáticamente **15 jugadores iniciales** al nuevo usuario, creando su equipo base para empezar a competir.

### 3. Mercado y Subastas

El mercado es la funcionalidad más compleja y diferenciadora de UFL. Combina varios mecanismos de comercio:

#### Subastas Ciegas Diarias

Cada liga tiene una subasta activa que se renueva automáticamente cada 24 horas. En cada subasta se ofrecen **12 jugadores aleatorios** extraídos del catálogo global:

- **Puja ciega**: Los usuarios no ven cuánto están pujando sus rivales. Solo ven el número total de pujas en cada slot y si ellos mismos han pujado. Esto introduce la **teoría de juegos**: ¿Pujo lo justo para ganar o pongo un extra para asegurarme?

- **Monedas bloqueadas**: Cuando un usuario puja, la cantidad pujada se resta de su saldo disponible y se mueve a `locked_coins`. Esto impide que un usuario puje más dinero del que tiene. Si pierde la puja, el dinero se desbloquea automáticamente al cerrarse la subasta.

- **Cierre automático**: El scheduler resuelve la subasta cuando llega a su `ends_at` (cada 5 minutos verifica subastas expiradas). El usuario con la puja más alta gana el jugador, se le cobra el dinero y la carta se añade a su equipo. Los perdedores recuperan su dinero.

- **Mercado cíclico**: Una vez resuelta una subasta, el sistema genera automáticamente la siguiente con 12 nuevos jugadores aleatorios. Los **precios son estables** (fijados en el catálogo de datos del jugador) y no fluctúan dinámicamente. La estrategia reside en gestionar bien las monedas disponibles y decidir qué jugadores fichar, no en timing de mercado.

#### Ventas entre Usuarios (Listings)

Cualquier usuario puede poner a la venta una de sus cartas en el mercado de la liga:

- **Precio mínimo**: El precio de venta no puede ser inferior al `current_price` del jugador. Esto evita que se malbaraten jugadores accidentalmente.

- **Pujas de compra**: Otros miembros de la liga pueden pujar por la carta. El vendedor ve todas las pujas y decide a cuál aceptar. No está obligado a aceptar ninguna.

- **Ofertas del sistema**: Si tras 24 horas nadie ha comprado la carta, el sistema genera automáticamente una oferta al 80-95% del precio pedido. El vendedor puede aceptarla o cancelarla.

#### Clausulazo

Cualquier jugador de un equipo rival puede ser comprado directamente pagando su **valor de mercado actual** (base + blindaje). No requiere consentimiento del propietario. Esta mecánica genera dinamismo constante: nadie puede sentirse seguro con sus jugadores.

#### Blindaje

Para protegerse del clausulazo, un usuario puede inyectar monedas adicionales al valor de un jugador. Estas monedas se restan de su saldo disponible y **aumentan el coste del clausulazo**. No mejoran el rendimiento del jugador, solo su precio de rescate. Es la eterna lucha entre **ataque** (guardar monedas para fichar) vs **defensa** (gastar monedas en blindar).

### 4. Gestión de Equipos

El equipo es la representación tangible del progreso del usuario en una liga:

- **15 jugadores iniciales**: Al unirse a una liga, el sistema asigna automáticamente un equipo base. Estos jugadores proceden del catálogo de la Scottish Premiership y tienen un OVR variado para dar un punto de partida equilibrado.

- **Formaciones tácticas**: El usuario puede elegir entre 7 formaciones: 4-4-2, 4-3-3, 3-5-2, 4-2-3-1, 3-4-3, 5-3-2, 5-4-1. Cada formación define cuántos jugadores de cada posición (GK, DEF, MID, FWD) deben ser titulares.

- **Alineación con validación**: El usuario selecciona 11 titulares del banquillo. El sistema valida que la selección respete los slots de la formación (ej: en 4-4-2 no se pueden poner 5 defensas). Si la formación cambia, la alineación se reajusta automáticamente para encajar.

- **Deadline de jornada**: Cuando comienza una jornada real, la alineación se bloquea. Los usuarios no pueden modificarla hasta la siguiente jornada. Esto crea un "snapshot" legal para el cálculo de puntos.

- **Pitch visual**: La alineación se muestra en un campo de fútbol interactivo con las posiciones de cada jugador. Se puede hacer clic en un jugador para ver su detalle o arrastrar jugadores del banquillo a slots vacíos.

- **Vista de equipos rivales**: Cualquier miembro de la liga puede ver el equipo de otro usuario en modo solo lectura. Esto permite espiar las estrategias de los rivales.

### 5. Sobres de Iconos (Pack Opening)

Los sobres son la mecánica de adquisición de jugadores legendarios:

- **Sobre legendario**: Cuesta 150.000.000 de monedas y contiene **1 carta legendaria** garantizada. Las leyendas son jugadores históricos del fútbol mundial (no actuales de la Scottish Premiership) con OVR elevado (85-99).

- **Perfiles de puntuación**: Cada leyenda tiene un perfil de puntuación que determina cómo genera puntos sin jugar partidos reales:
  - **LEGEND**: Consistente, 85% de probabilidad de puntuación alta.
  - **VOLCANO**: Bimodal, puede dar 90 puntos o 0 en una jornada.
  - **CURSED**: Alto riesgo, 35% de probabilidad de puntuar 0.

- **Animación de apertura**: Al abrir un sobre, se muestra una animación con revelación progresiva de la carta, mostrando su OVR, nombre, posición y rareza con efectos visuales.

- **Historial**: Se puede consultar el historial de sobres abiertos, con las cartas obtenidas en cada uno, expandible para ver los detalles.

### 6. Notificaciones por Liga

El sistema de notificaciones mantiene al usuario informado de eventos importantes, **filtradas por liga**:

- **Notificaciones únicas por liga**: Cada notificación está vinculada a una liga específica (`league_id`). Cuando el usuario navega a una liga, solo ve las notificaciones relacionadas con esa liga (subastas ganidas/perdidas, eventos de mercado, etc.). Esto evita confusión cuando un usuario participa en múltiples ligas simultáneamente.

- **Resultados de subasta**: Cuando se cierra una subasta, cada participante recibe una notificación indicando si ganó o perdió, qué jugador estaba en juego y cuánto pujó.

- **Badge de no leídas**: El header muestra un badge rojo con el número de notificaciones no leídas **de la liga actual**, visible desde cualquier página dentro de esa liga.

- **Panel deslizable**: Al pulsar el icono de campana, se despliega un panel con las 10 notificaciones más recientes de la liga. Se pueden marcar todas como leídas, eliminar individualmente o borrar todas las de esa liga.

### 7. Panel de Administración

El panel de admin permite a los administradores mantener la salud del ecosistema:

- **Estadísticas globales**: Vista rápida del total de usuarios, ligas, jugadores y equipos registrados.

- **CRUD de jugadores**: El admin puede editar cualquier jugador del catálogo: nombre, edad, nacionalidad, posición, OVR, stats individuales (pace, shooting, passing, etc.), precio actual, equipo, imagen URL, y si es leyenda.

- **Gestión de usuarios**: Buscar usuarios por username/email, eliminarlos, y ajustar sus monedas en cada liga. El editor de monedas muestra el total, las retenidas y las libres, con botones rápidos de +/- 1M y +/- 10M.

- **Gestión de ligas**: Buscar ligas, ver sus códigos de invitación y eliminarlas si es necesario.

- **Gestión de equipos**: Ver todos los equipos con sus stats, formaciones, número de jugadores y record de Arena.

---
## Modelo de Datos

### Diagrama Entidad-Relación (ER)

A continuación se presenta el diagrama ER completo del sistema, **100% fiel al esquema de base de datos real** (models.py). Cada entidad muestra sus campos clave y todas las relaciones entre tablas están documentadas con cardinalidad.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    DIAGRAMA ENTIDAD-RELACIÓN                        │
│                 Ultimate Fantasy Legends — Schema                    │
└──────────────────────────────────────────────────────────────────────┘

┌─────────────┐1        N┌──────────────┐N        1┌───────────────┐
│   USER      │──────────│    TEAM      │──────────│   LEAGUE      │
│─────────────│           │──────────────│          │───────────────│
│ id (PK)     │           │ id (PK)      │          │ id (PK)       │
│ username    │           │ name         │          │ name          │
│ email       │           │ user_id (FK) │          │ owner_id (FK) │
│ password    │           │ league_id(FK)│          │ invite_code   │
│ role        │           │ overall      │          │ max_members   │
│ global_elo  │           │ formation    │          │ is_public     │
│ arena_wins  │           │ arena_rating │          │ created_at    │
│ total_points│           │ shield_url   │          └───────┬───────┘
│ level       │           │ kit_color    │                  │
│ experience  │           │ created_at   │                  │
│ created_at  │           │ updated_at   │          1       │N
└──────┬──────┘           └──────┬───────┘   ┌──────────────────────┐
       │N                        │N           │  LEAGUE_MEMBER      │
       │1             ┌──────────┘            │─────────────────────│
       │              │1            N         │ id (PK)             │
       │              │          ┌────────────┤ league_id (FK)      │
       │              │          │            │ user_id (FK)        │
       │              │          │            │ coins (BigInt)      │
       │              │          │            │ locked_coins(BigInt)│
       │              │          │            │ league_points       │
       │              │          │            │ is_admin            │
       │              │          │            │ joined_at           │
       │              │          │            └─────────────────────┘
       │              │          │
       │              │          │N
       │              │          └──────────────┐
       │              │1         N              │
       │              │    ┌────────────┐       │
       │              │    │ USER_CARD  │       │
       │              │    │────────────│       │
       │              │    │ id (PK)    │       │
       │              │    │ user_id(FK)│       │
       │              │    │ player_id  │       │
       │              │    │ team_id(FK)│─── NULL si no asignada
       │              │    │ league_id  │       │
       │              │    │ current_ovr│       │
       │              │    │ protected  │       │
       │              │    │ is_lineup  │       │
       │              │    │ is_trade   │       │
       │              │    │ acquired_at│       │
       │              │    └─────┬──────┘       │
       │              │          │N              │
       │              │          │1              │
       │              │          ▼               │
       │              │    ┌────────────┐       │
       │              │    │  PLAYER    │       │
       │              │    │────────────│       │
       │              │    │ id (PK)    │       │
       │              │    │ name       │       │
       │              │    │ position   │       │
       │              │    │ nationality│       │
       │              │    │ overall    │       │
       │              │    │ current_prc│       │
       │              │    │ target_prc │       │
       │              │    │ is_legend  │       │
       │              │    │ rarity     │       │
       │              │    │ sportmonks │       │
       │              │    │ scoring_prf│       │
       │              │    │ min_fantasy│       │
       │              │    │ max_fantasy│       │
       │              │    └─────┬──────┘       │
       │              │          │1              │
       │              │          │N              │
       │              │          │               │
       │              │    ┌─────▼──────┐       │
       │              │    │ AUCTION_SLOT│       │
       │              │    │────────────│       │
       │              │    │ id (PK)    │       │
       │              │    │ auction_id │       │
       │              │    │ player_id  │       │
       │              │    │ base_price │       │
       │              │    └─────┬──────┘       │
       │              │          │1              │
       │              │          │N              │
       │              │    ┌─────▼──────┐       │
       │              │    │ AUCTION_BID │       │
       │              │    │────────────│       │
       │              │    │ id (PK)    │       │
       │              │    │ slot_id(FK)│       │
       │              │    │ user_id(FK)│       │
       │              │    │ amount     │       │
       │              │    │ created_at │       │
       │              │    └────────────┘       │
       │              │                          │
       │              │                          │
       │              │    ┌────────────────┐   │
       │              │    │ MARKET_AUCTION │   │
       │              │    │────────────────│   │
       │              │    │ id (PK)        │   │
       │              │    │ league_id (FK) │   │
       │              │    │ started_at     │   │
       │              │    │ ends_at        │   │
       │              │    │ is_active      │   │
       │              │    │ is_resolved    │   │
       │              │    └────────────────┘   │
       │              │                          │
       │              │    ┌────────────────┐   │
       │              │    │ MARKET_LISTING │   │
       │              │    │────────────────│   │
       │              │    │ id (PK)        │   │
       │              │    │ card_id (FK)   │───┘
       │              │    │ seller_id (FK) │───> USER
       │              │    │ league_id (FK) │───> LEAGUE
       │              │    │ asking_price   │
       │              │    │ is_active      │
       │              │    │ buyer_id (FK)  │───> USER
       │              │    └───────┬────────┘
       │              │            │1
       │              │            │N
       │              │    ┌───────▼────────┐
       │              │    │  LISTING_BID   │
       │              │    │────────────────│
       │              │    │ id (PK)        │
       │              │    │ listing_id(FK) │
       │              │    │ user_id (FK)   │───> USER
       │              │    │ amount         │
       │              │    └────────────────┘
       │              │
       │              │    ┌────────────────┐
       │              │    │ SYSTEM_OFFER   │
       │              │    │────────────────│
       │              │    │ id (PK)        │
       │              │    │ listing_id(FK) │───> MARKET_LISTING
       │              │    │ card_id (FK)   │───> USER_CARD
       │              │    │ user_id (FK)   │───> USER
       │              │    │ league_id (FK) │───> LEAGUE
       │              │    │ offer_price    │
       │              │    │ is_accepted    │
       │              │    │ is_expired     │
       │              │    └────────────────┘
       │              │
       │              │    ┌─────────────────┐
       │              │    │ PACK_OPENING    │
       │              │    │─────────────────│
       │              │    │ id (PK)         │
       │              │    │ user_id (FK)    │───> USER
       │              │    │ league_id (FK)  │───> LEAGUE
       │              │    │ pack_type       │
       │              │    │ cost            │
       │              │    └───────┬─────────┘
       │              │            │1
       │              │            │N
       │              │    ┌───────▼─────────┐
       │              │    │ PACK_OPENING_CRD│
       │              │    │─────────────────│
       │              │    │ id (PK)         │
       │              │    │ pack_id (FK)    │
       │              │    │ card_id (FK)    │───> USER_CARD
       │              │    └─────────────────┘
       │              │
       │              │    ┌─────────────────┐
       │              │    │ NOTIFICATION    │
       │              │    │─────────────────│
       │              │    │ id (PK)         │
       │              │    │ user_id (FK)    │───> USER
       │              │    │ league_id (FK)  │───> LEAGUE
       │              │    │ type            │
       │              │    │ title           │
       │              │    │ message         │
       │              │    │ is_read         │
       │              │    └─────────────────┘
       │              │
       │              │    ┌─────────────────┐
       │              │    │ LEAGUE_INVITE   │
       │              │    │─────────────────│
       │              │    │ id (PK)         │
       │              │    │ league_id (FK)  │───> LEAGUE
       │              │    │ invited_by (FK) │───> USER
       │              │    │ invited_user(FK)│───> USER
       │              │    │ invited_email   │
       │              │    │ status          │
       │              │    │ token           │
       │              │    └─────────────────┘


┌──────────────┐1       N┌───────────────┐N        1┌──────────────┐
│   GAMEWEEK   │─────────│    MATCH      │──────────│PLAYER_MT_STATS│
│──────────────│          │───────────────│          │───────────────│
│ id (PK)      │          │ id (PK)       │          │ id (PK)       │
│ number       │          │ sportmonks_id │          │ player_id(FK) │──> PLAYER
│ start_date   │          │ gameweek(FK)  │          │ match_id (FK) │──> MATCH
│ end_date     │          │ home_team     │          │ minutes       │
│ is_active    │          │ away_team     │          │ rating        │
│ is_finished  │          │ home_score    │          │ goals         │
│              │          │ away_score    │          │ assists       │
│              │          │ status        │          │ clean_sheet   │
│              │          │ kickoff_time  │          │ fantasy_pts   │
└──────┬───────┘          └───────────────┘          │ + 20 campos  │
       │1                                            └──────────────┘
       │N
       │
       │1       N┌──────────────────┐
       └─────────│GAMEWEEK_LINEUP   │
                 │──────────────────│
                 │ id (PK)          │
                 │ team_id (FK)     │──> TEAM
                 │ gameweek_id (FK) │──> GAMEWEEK
                 │ formation        │
                 │ points_earned    │
                 └───────┬──────────┘
                         │1
                         │N
                         │
                 ┌───────▼──────────────┐
                 │GAMEWEEK_LINEUP_PLAYER│
                 │──────────────────────│
                 │ id (PK)              │
                 │ lineup_id (FK)       │──> GAMEWEEK_LINEUP
                 │ card_id (FK)         │──> USER_CARD
                 │ position             │
                 │ is_captain           │
                 │ points_earned        │
                 └──────────────────────┘


┌──────────────┐N        N┌──────────────┐
│   TEAM       │──────────│ARENA_BATTLE  │
│──────────────│           │──────────────│
│ id (PK)      │           │ id (PK)      │
│ user_id (FK) │           │ team1_id(FK) │──> TEAM
│ league_id(FK)│           │ team2_id(FK) │──> TEAM
│ ...          │           │ team1_score  │
└──────┬───────┘           │ team2_score  │
       │                   │ winner_id(FK)│──> TEAM (NULL=empate)
       │                   │ rating_chg   │
       │                   │ global_chg   │
       │                   └──────────────┘
       │
       │1        N┌────────────────────┐
       └──────────│PLAYER_STATS_SUMMARY│  (VISTA SQL)
                  │────────────────────│
                  │ player_id (PK,FK)  │──> PLAYER
                  │ total_matches      │
                  │ sum_ratings        │
                  │ avg_rating         │
                  │ sum_fantasy        │
                  │ avg_fantasy        │
                  └────────────────────┘
```

### Entidades Principales — Flujo de Relaciones

```
User (1) ────────< Team (N) ────────< UserCard (N) ──> Player (1)
  │                   │                  │
  │                   │                  └── league_id ──> League (1)
  │                   │
  │                   └── league_id ──> LeagueMember (1)
  │
  ├── owned_players ──> UserCard (N)
  ├── ArenaBattle (N) (a través de Team)
  └── Notification (N)

League (1) ──< MarketAuction (N) ──< AuctionSlot (N) ──> Player (1)
                     │                    │
                     │                    └── AuctionBid (N) ──> User (1)
                     │
                     └── MarketListing (N) ──> UserCard (1)
                                      │
                                      └── ListingBid (N) ──> User (1)

League (1) ──< Notification (N) ──> User (1)
League (1) ──< PackOpening (N) ───< PackOpeningCard (N) ──> UserCard (1)
League (1) ──< LeagueInvitation (N) ──> User (1) (invited_by, invited_user)
League (1) ──< LeagueMember (N) ──> User (1)

Gameweek (1) ──< Match (N) ──< PlayerMatchStats (N) ──> Player (1)
Gameweek (1) ──< GameweekLineup (N) ──< GameweekLineupPlayer (N) ──> UserCard (1)

Team (1) ──< GameweekLineup (N)
Team (1) ──< ArenaBattle (N) (como team1 o team2)
```

**Explicación de las relaciones más importantes:**

- **User → Team**: Un usuario puede tener **múltiples equipos**, uno por cada liga en la que participa. La relación es `user_id` + `league_id` con constraint único.

- **Team → UserCard**: Un equipo tiene **múltiples cartas** (user_cards). Cada carta representa la posesión de un jugador por parte de un usuario. La carta tiene `team_id` si está asignada a un equipo, o `NULL` si está en el inventario general del usuario.

- **UserCard → Player**: Cada carta apunta a un **jugador base** del catálogo. Esto permite que múltiples usuarios tengan cartas del mismo jugador (ej: varios usuarios pueden tener una carta de Kyogo Furuhashi).

- **League → LeagueMember**: Una liga tiene **múltiples miembros**. Cada miembro tiene sus propios `coins`, `locked_coins` y `league_points`, independientes de otras ligas.

- **League → MarketAuction → AuctionSlot → AuctionBid**: Una liga tiene subastas. Cada subasta tiene 12 slots (uno por jugador). Cada slot puede tener múltiples pujas de diferentes usuarios.

- **Gameweek → Match → PlayerMatchStats**: Una jornada tiene múltiples partidos. Cada partido tiene múltiples estadísticas de jugadores. Esta cadena es la que conecta los datos reales con el sistema de puntuación.

### Tablas Principales con Detalle

| Tabla | Descripción | Campos Clave | Notas Importantes |
|---|---|---|---|
| `users` | Usuarios del sistema | `id`, `username`, `email`, `password_hash`, `role`, `global_elo`, `arena_tickets`, `email_verified` | La contraseña se almacena como hash bcrypt. `global_elo` empieza en 1000. `arena_tickets` se resetean diariamente. |
| `players` | Catálogo de jugadores reales + leyendas | `id`, `name`, `position`, `overall_rating`, `current_price`, `is_legend`, `scoring_profile`, `base_rarity` | `current_price` es el precio estable del jugador en el mercado. `scoring_profile` solo aplica a leyendas. |
| `user_cards` | Cartas que posee cada usuario | `id`, `user_id`, `player_id`, `team_id`, `current_overall`, `protected_value`, `is_in_lineup`, `is_tradeable` | `protected_value` son las monedas inyectadas para blindar. `team_id` es NULL si no está en un equipo. |
| `teams` | Equipos de usuario por liga | `id`, `user_id`, `league_id`, `name`, `overall_rating`, `active_formation`, `arena_rating`, `shield_url` | `overall_rating` es la media del OVR de los jugadores. `active_formation` define los slots del pitch. |
| `leagues` | Ligas fantasy privadas | `id`, `name`, `owner_id`, `invite_code`, `max_members`, `is_public` | `invite_code` es un UUID corto de 8 caracteres generado al crear la liga. |
| `league_members` | Membresía usuario-liga con economía | `id`, `league_id`, `user_id`, `league_points`, `coins`, `locked_coins`, `is_admin` | Cada miembro tiene su propia economía por liga. `coins` empieza en 100.000.000. |
| `market_auctions` | Subastas diarias por liga | `id`, `league_id`, `started_at`, `ends_at`, `is_active`, `is_resolved` | Se crea una nueva cada 24h. `is_resolved` se activa cuando el scheduler la procesa. |
| `auction_slots` | Jugadores individuales en subasta | `id`, `auction_id`, `player_id`, `base_price`, `current_bid`, `highest_bidder_id` | `base_price` es el precio mínimo. `current_bid` es la puja más alta actual. |
| `market_listings` | Ventas entre usuarios | `id`, `card_id`, `seller_id`, `league_id`, `asking_price`, `is_active`, `buyer_id` | `asking_price` no puede ser menor que `current_price` del jugador. |
| `gameweeks` | Jornadas de la liga real | `id`, `number`, `start_date`, `end_date`, `is_active`, `is_finished` | Definen cuándo se bloquean las alineaciones y cuándo se calculan los puntos. |
| `gameweek_lineups` | Snapshots de alineaciones por jornada | `id`, `team_id`, `gameweek_id`, `active_formation`, `points_earned` | Se crea al guardar la alineación antes del deadline. Los puntos se calculan post-jornada. |
| `matches` | Partidos reales de la Scottish Premiership | `id`, `sportmonks_id`, `home_team`, `away_team`, `home_score`, `away_score`, `status`, `kickoff_time` | `sportmonks_id` permite evitar duplicados al sincronizar con la API. |
| `player_match_stats` | Stats de cada jugador en cada partido | `id`, `player_id`, `match_id`, `goals`, `assists`, `minutes_played`, `clean_sheet`, `yellow_cards`, `red_cards`, `fantasy_points`, +20 campos más | `fantasy_points` se calcula con el sistema de puntuación. `clean_sheet` se calcula automáticamente. |
| `arena_battles` | Historial de batallas PvP | `id`, `team1_id`, `team2_id`, `team1_score`, `team2_score`, `winner_id`, `rating_change`, `global_rating_change` | El `rating_change` es el delta ELO de la batalla. `global_rating_change` afecta al usuario. |
| `pack_openings` | Registro de sobres abiertos | `id`, `user_id`, `league_id`, `pack_type`, `cost`, `cards_obtained` | `pack_type` es actualmente "icon". El coste es fijo a 150M. |
| `notifications` | Notificaciones del sistema por liga | `id`, `user_id`, `league_id`, `type`, `title`, `message`, `is_read` | Cada notificación está vinculada a una liga específica (`league_id`). Se filtran por liga en la UI. `type` puede ser "auction_won" o "auction_lost". |
| `system_offers` | Ofertas automáticas del sistema | `id`, `listing_id`, `card_id`, `user_id`, `league_id`, `offer_price`, `is_accepted`, `is_expired` | Se generan 24h después de listar si nadie compra. Precio = 80-95% del asking_price. |

---

## Motor de Puntuación

### Filosofía de Diseño

El sistema de puntuación fue diseñado para que **las acciones decisivas (goles y asistencias) sean las más valiosas**, mientras que las acciones acumulativas (pases, tackles, duelos) aporten un bonus secundario. Esta decisión se tomó tras analizar que en la configuración original, un mediocentro que hacía muchos pases y tackles podía superar en puntos a un delantero que marcaba 2 goles, lo cual no refleja la importancia real de cada acción en el fútbol.

**Paridad económica**: **1 punto fantasy = 100.000 monedas**. Esta paridad fue calibrada para mantener un equilibrio financiero saludable. Una jornada de 50 puntos se traduce en 5.000.000 de monedas, suficiente para pujar por jugadores de nivel medio sin romper la economía.

### Tabla Completa de Puntuación

#### Acciones Decisivas (las más valiosas)

| Acción | Portero | Defensa | Medio | Delantero | Racional |
|---|---|---|---|---|---|
| **Gol** | **10 pts** | **6 pts** | **5 pts** | **4 pts** | Premia la rareza: un gol de portero es excepcional, uno de delantero es su trabajo. |
| **Asistencia** | **6 pts** | **4 pts** | **3 pts** | **3 pts** | Una asistencia de portero o defensa es más valiosa porque es menos esperada. |
| **Ocasión creada** | 2 pts | 2 pts | 2 pts | 2 pts | Un pase clave que genera una oportunidad clara de gol. |

#### Acciones de Tiempo

| Acción | Todos | Racional |
|---|---|---|
| Minuto jugado | 1 pt | Premia la participación mínima. |
| 60+ minutos jugados | 2 pts adicionales | Premia la resistencia y titularidad. |

#### Acciones Defensivas

| Acción | Portero | Defensa | Racional |
|---|---|---|---|
| Portería a cero | 5 pts | 4 pts | Mantener la puerta a cero es el objetivo principal del GK y la defensa. |
| Gol recibido | -3 pts | -3 pts | Penaliza los goles encajados. |
| Salvamento | +1 pt | — | Cada parada del portero suma. |
| Tackles (cada 8) | +1 pt | +1 pt | Cada 8 tackles completados = 1 punto. |
| Intercepciones (cada 8) | +1 pt | +1 pt | Cada 8 intercepciones = 1 punto. |
| Despejes (cada 6) | +1 pt | +1 pt | Cada 6 despejes = 1 punto. |
| Recuperaciones (cada 10) | +1 pt | +1 pt | Cada 10 recuperaciones de balón = 1 punto. |

#### Acciones Ofensivas

| Acción | Todos | Racional |
|---|---|---|
| Tiros a puerta (cada 4) | +1 pt | Cada 4 tiros a puerta = 1 punto. Premia la participación ofensiva. |
| Regates logrados (cada 5) | +1 pt | Cada 5 regates exitosos = 1 punto. |
| Balones al área (cada 4) | +1 pt | Cada 4 centros precisos al área = 1 punto. |
| Pases precisos (cada 50) | +1 pt | Cada 50 pases completados = 1 punto. Se puso alto para que no supere a los goles. |
| Duelos ganados (cada 10) | +1 pt | Cada 10 duelos ganados = 1 punto. |

#### Penalizaciones

| Acción | Todos | Racional |
|---|---|---|
| Tarjeta amarilla | -1 pt | Penalización leve por conducta antideportiva. |
| Tarjeta roja | -3 pts | Penalización severa por expulsión. |
| Penalti fallado | -2 pts | Oportunidad de gol desperdiciada. |
| Penalti cometido | -2 pts | Dar un penalti al rival es grave. |
| Penalti recibido | +1 pt | Haber provocado un penalti a favor. |
| Penalti parado (GK) | +5 pts | Detener un penalti es excepcional. |
| Faltas cometidas (cada 2) | -1 pt | Cada 2 faltas = -1 punto. |

#### Bonus por Rating

| Rating | Puntos |
|---|---|
| 8.0 - 8.9 | +2 pts |
| 9.0 - 9.9 | +3 pts |
| 10.0 | +4 pts |

### Perfiles de Puntuación de Iconos

Los jugadores legendarios no participan en partidos reales de la Scottish Premiership, por lo que su puntuación se genera mediante **algoritmos probabilísticos** que simulan su rendimiento:

| Perfil | Comportamiento | Ejemplo de Rango | Descripción |
|---|---|---|---|
| **LEGEND** | 85% en rango alto | 40-80 pts | Consistencia pura. Son caros porque garantizan puntos jornada tras jornada. Ideales para managers que prefieren estabilidad. |
| **MAESTRO** | Alta regularidad | 30-70 pts | Rendimiento estable con picos moderados. Equilibrio entre fiabilidad y sorpresa. |
| **RELIABLE** | Moderado-alto | 20-55 pts | Fiable pero sin explosiones de puntos. Buen complemento para un equipo equilibrado. |
| **VOLCANO** | Bimodal (20% → 0) | 0-100 pts | Factor sorpresa: pueden ganar una jornada ellos solos con 100 puntos o hundirte con 0. Solo para managers arriesgados. |
| **CURSED** | 35% → 0 puntos | 0-90 pts | Riesgo máximo. Representan el talento frágil de jugadores como Balotelli o Cassano. Pueden dar un 90 o un 0. |

**Cómo funciona el algoritmo de iconos**: Cuando se calculan los puntos de una jornada, el sistema detecta si un jugador tiene `scoring_profile` definido. Si es así, ignora las stats del partido y genera un número aleatorio según la distribución de probabilidad del perfil. Por ejemplo, un perfil VOLCANO tiene un 20% de probabilidad de generar un puntuación en el rango alto (70-100) y un 80% de generar una puntuación baja o cero.

---

## Ingeniería Económica

### El Problema que Resuelve la Economía

En un fantasy football tradicional, los usuarios reciben puntos pero no hay forma de gastarlos estratégicamente. UFL crea una **economía circular** donde los puntos se convierten en monedas, las monedas se gastan en el mercado, los jugadores comprados generan más puntos, y así sucesivamente. Esta circularidad mantiene el juego activo entre jornadas.

### Mercado Cíclico con Precios Estables

El mercado de UFL se basa en un **sistema cíclico y renovado**. Cada 24 horas, una nueva subasta con **12 jugadores aleatorios** aparece en cada liga. Los precios de los jugadores son **estables**: se establecen en el catálogo de datos (`Player.current_price`) y no fluctúan dinámicamente. Esto simplifica la toma de decisiones del usuario, que se centra en:

1. **Gestión de presupuesto**: ¿En qué jugadores invertir mis monedas limitadas?
2. **Teoría de juegos** (subasta ciega): ¿Cuánto pujar cuando no sé cuánto pujan mis rivales?
3. **Timing del mercado cíclico**: Si un jugador deseado no aparece hoy, puede aparecer mañana en la siguiente subasta.

```
                    ┌──────────────────┐
                    │   NUEVA SUBASTA  │  Cada 24h en cada liga
                    │   (12 jugadores) │  12 jugadores aleatorios
                    │                  │  extraídos del catálogo
                    └────────┬─────────┘
                             │
                             │ Los usuarios pujan con monedas
                             │ (puja ciega: no ven rivales)
                             ▼
                    ┌──────────────────┐
                    │  CIERRE AUTOMÁTICO│  Scheduler resuelve
                    │  (cada 5min)     │  Ganador: mayor puja
                    │                  │  Perdedores: monedas
                    └────────┬─────────┘  devueltas
                             │
                             ▼
                    ┌──────────────────┐
                    │  CARTA ASIGNADA  │  Carta al equipo del
                    │  + PRÓXIMA SUBASTA│ ganador → nueva subasta
                    │                  │  automática con 12 nuevos
                    └──────────────────┘
```

**Ventajas del mercado cíclico:**
- **Predecible**: Los usuarios saben exactamente cuánto cuesta cada jugador.
- **Renovado**: Nuevas oportunidades cada día con jugadores diferentes.
- **Accesible**: No requiere conocimiento de tendencias de precios para tomar decisiones.
- **Justo**: Todos los usuarios ven los mismos precios, la competitividad está en la puja.

### Economía por Liga

Cada liga tiene su propia economía independiente. Esto significa que un usuario puede tener **100 millones de monedas en una liga y solo 10 millones en otra**, dependiendo de su rendimiento en cada una.

- **Saldo inicial**: Cada usuario empieza con **100.000.000 de monedas** en cada liga que se une.
- **Ingreso por jornada**: Al finalizar cada jornada real, el sistema calcula los puntos totales de la alineación del usuario y los multiplica por 100.000. Ejemplo: 50 puntos × 100.000 = 5.000.000 de monedas.
- **Monedas bloqueadas (`locked_coins`)**: Cuando un usuario puja en una subasta, el dinero pujado se bloquea. Si puja 8M por un jugador y tiene 100M, su saldo disponible baja a 92M y sus `locked_coins` suben a 8M. Si pierde la puja, los 8M se desbloquean y vuelven al saldo disponible.
- **Monedas libres (`free_coins`)**: Es el dinero realmente disponible: `coins - locked_coins`.

### Transacciones Atómicas

Todas las operaciones económicas se ejecutan como **transacciones SQL atómicas**. Esto significa que si falla cualquier parte de la operación, todo se revierte (rollback). Ejemplo con una compra por clausulazo:

```
INICIO TRANSACCIÓN
  1. Verificar que el comprador tiene suficientes monedas
  2. Restar monedas al comprador
  3. Sumar monedas al vendedor
  4. Cambiar el owner de la carta (user_card)
  5. Si el jugador estaba en un equipo, actualizar team_id
SI TODO OK → COMMIT
SI ALGO FALLA → ROLLBACK (nada cambia)
```

Esto garantiza **cero errores de saldo**: el dinero nunca desaparece ni se duplica, y las cartas nunca cambian de manos sin que el dinero se transfiera correctamente.

---

## Arena PvP

### ¿Qué es la Arena?

La Arena es un modo de juego donde los usuarios pueden **enfrentar su equipo contra cualquier otro equipo de la plataforma** en una simulación. No es un enfrentamiento en tiempo real: el algoritmo simula el resultado basándose en las estadísticas y composición de ambos equipos.

### Motor de Simulación

El algoritmo de simulación sigue estos pasos:

1. **Selección de rival**: El sistema busca un equipo con un ELO similar al del usuario (±200 puntos) para crear un enfrentamiento equilibrado.

2. **Comparación por líneas**: Se comparan las tres líneas de ambos equipos:
   - **Ataque vs Defensa**: El poder de ataque del Equipo A se enfrenta a la defensa del Equipo B, y viceversa.
   - **Mediocampo vs Mediocampo**: El equipo con mejor mediocampo gana posesión, lo que da un bonus a su ataque.
   - **Portero vs Portero**: Se comparan directamente.

3. **Cálculo de poder por línea**: El poder de cada línea se calcula sumando el OVR de los jugadores en esa posición, aplicando los siguientes multiplicadores:
   - Formación (algunas formaciones dan bonus a líneas específicas)
   - Sinergias por club (jugadores del mismo club real dan +2% por cada par)
   - Sinergias por nacionalidad (misma nacionalidad da +1% por cada par)

4. **Simulación del resultado**: Se genera un marcador basado en la diferencia de poder entre líneas, con un factor de aleatoriedad del ±15% para crear emoción.

5. **Cálculo de ELO**: Se aplica la fórmula estándar de ELO:
   ```
   Expected_A = 1 / (1 + 10^((Rating_B - Rating_A) / 400))
   K = 32
   Si A gana: New_Rating_A = Rating_A + K × (1 - Expected_A)
   Si A pierde: New_Rating_A = Rating_A + K × (0 - Expected_A)
   ```

### Sistema de Tickets

Para evitar que los usuarios combatan infinitamente y escalen su ELO sin límite, se implementa un sistema de **tickets diarios**:

- **5 tickets por día**: Cada combate consume 1 ticket.
- **Reset diario**: Los tickets se restauran a 5 cada día a medianoche (gestionado por el scheduler).
- **Sin gasto de monedas**: Los combates son gratuitos, solo cuestan tickets.

### Recompensas

| Resultado | Recompensa |
|---|---|
| Victoria | +ELO (varía según diferencia de rating), +monedas bonus, +1 win |
| Empate | ±ELO mínimo, +monedas pequeñas, +1 draw |
| Derrota | -ELO (varía), +1 loss |

---

## Estructura del Proyecto

```
ProyectoFinCurso/
│
├── README.md                          ← Este archivo: documentación completa del proyecto
├── docker-compose.yml                 ← Orquestación Docker: define los 3 servicios (frontend, backend, db)
├── .env                               ← Variables de entorno: contraseñas, API keys, configuración SMTP
├── .gitignore                         ← Archivos a ignorar en git (node_modules, __pycache__, .env, etc.)
├── ultimate_fantasy_legends.sql       ← Schema completo de MySQL + datos iniciales (1000+ jugadores)
├── replace_logos.py                   ← Script Python para reemplazar imágenes de jugadores/logos
├── scratch_debug_player.py            ← Script de depuración para testing de jugadores
│
├── backend/                           ← CÓDIGO DEL BACKEND (FastAPI + Python)
│   ├── Dockerfile                     ← Definición de la imagen Docker del backend
│   ├── requirements.txt               ← Dependencias Python (fastapi, sqlalchemy, apscheduler, etc.)
│   │
│   ├── app/                           ← Código principal de la aplicación
│   │   ├── __init__.py                ← Hace que app sea un paquete Python
│   │   ├── main.py                    ← Entry point: crea la app FastAPI, monta routers, inicia scheduler
│   │   │                              ← Define CORS, middleware, eventos de startup/shutdown
│   │   │
│   │   ├── core/                      ← Configuración y utilidades del núcleo
│   │   │   ├── config.py              ← Lee variables de entorno con Pydantic Settings
│   │   │   ├── database.py            ← Crea el engine SQLAlchemy, sesión de BD, función get_db
│   │   │   └── scheduler.py           ← APScheduler: define las tareas programadas (subastas, precios, etc.)
│   │   │
│   │   ├── models/                    ← Modelos de base de datos (SQLAlchemy ORM)
│   │   │   ├── __init__.py
│   │   │   └── models.py              ← TODOS los modelos en un archivo: User, Player, Team, League,
│   │   │                              ←   UserCard, MarketAuction, AuctionSlot, Match, etc. (959 líneas)
│   │   │
│   │   ├── schemas/                   ← Schemas Pydantic para validar requests/responses
│   │   │                              ← Definen la estructura de datos que entra y sale de la API
│   │   │
│   │   ├── routers/                   ← Endpoints de la API organizados por dominio
│   │   │   ├── auth.py                ← POST /register, /login, /verify-email; GET /me, /search
│   │   │   ├── leagues.py             ← CRUD de ligas, invitaciones, membresía, códigos
│   │   │   ├── teams.py               ← Equipos: crear, editar, alineaciones, puntos por jornada
│   │   │   ├── players.py             ← Catálogo de jugadores, cartas del usuario, historial
│   │   │   ├── market.py              ← Lógica del mercado: subastas, pujas, clausulazos, blindajes
│   │   │   ├── arena.py               ← Simulación PvP, historial de batallas, leaderboard
│   │   │   ├── packs.py               ← Apertura de sobres de iconos
│   │   │   ├── admin.py               ← Panel admin: CRUD global, ajuste de economías
│   │   │   └── notifications.py       ← CRUD de notificaciones del sistema
│   │   │
│   │   └── services/                  ← Lógica de negocio (separada de los routers)
│   │       ├── auth_service.py        ← Verificación OTP, generación de tokens, hash de passwords
│   │       ├── scoring_calculator.py  ← Calcula puntos fantasy a partir de PlayerMatchStats
│   │       └── sportmonks_client.py   ← Cliente HTTP para la API de Sportmonks
│   │
│   ├── scripts/                       ← Scripts de utilidad y mantenimiento
│   │   ├── seed_db.py                 ← Población inicial de la BD (jugadores, equipos de ejemplo)
│   │   └── setup/
│   │       ├── init_db.py             ← Inicialización de la base de datos (crea tablas)
│   │       ├── master_migration.py    ← Migración completa del schema
│   │       ├── sistema_puntos_oficial.py ← Definición del sistema de puntuación
│   │       └── backfill_gw_points.py  ← Recalcular puntos de jornadas pasadas
│   │
│   ├── docs/                          ← Documentación técnica del backend
│   │   ├── complete_stats_documentation.md ← Documentación de todas las stats de Sportmonks
│   │   ├── fantasy_points_system.md  ← Explicación del sistema de puntuación
│   │   └── sistema_puntos_oficial_DOCS.md ← Docs oficial del sistema de puntos
│   │
│   └── data/                          ← Datos en formato CSV para importación
│       ├── football_icons.csv         ← Lista de jugadores legendarios/iconos
│       ├── EAFC26-Men.csv             ← Datos de jugadores estilo EAFC (FIFA)
│       └── sportmonks_players.csv     ← Exportación de jugadores desde Sportmonks
│
├── frontend/                          ← CÓDIGO DEL FRONTEND (React + Vite)
│   ├── Dockerfile                     ← Definición de la imagen Docker del frontend
│   ├── vite.config.js                 ← Config de Vite: proxy /api → localhost:8000, plugins React
│   ├── package.json                   ← Dependencias npm (react, axios, react-router-dom, sonner)
│   │
│   └── src/                           ← Código fuente de la aplicación React
│       ├── main.jsx                   ← Entry point: monta el componente App en el DOM
│       ├── App.jsx                    ← Router principal: define todas las rutas de la app
│       ├── index.css                  ← Estilos globales: reset CSS, tipografía, scrollbars
│       │
│       ├── styles/
│       │   └── variables.css          ← Design tokens: colores, fondos, bordes (26 líneas)
│       │                              ← --gold, --bg-base, --text-primary, --success, --danger
│       │
│       ├── context/
│       │   └── AuthContext.jsx        ← Contexto React para autenticación: user, login, logout,
│       │                              ←   activeLeagueId, refreshUser. Persiste en localStorage.
│       │
│       ├── services/
│       │   ├── api.js                 ← Configuración de Axios: baseURL, interceptores JWT
│       │                              ←   Añade token a cada request, maneja 401 → redirect login
│       │   └── endpoints.js           ← Funciones de API organizadas por módulo: authAPI, teamsAPI,
│       │                              ←   playersAPI, auctionAPI, arenaAPI, leaguesAPI, adminAPI
│       │
│       ├── utils/
│       │   └── mediaUrl.js            ← Resolución de URLs de imágenes: /static/ → backend,
│       │                              ←   fallback a ui-avatars.com si no hay imagen
│       │
│       ├── components/                ← Componentes reutilizables compartidos entre páginas
│       │   ├── AppLayout.jsx          ← Layout base: header con título, botón atrás, navegación
│       │   ├── PlayerDetailModal.jsx  ← Modal con detalle completo de un jugador (stats, precio,
│       │                              ←   opciones de clausulazo, blindaje, venta)
│       │   ├── FormationPitch.jsx     ← Campo de fútbol visual con posiciones de la formación
│       │   ├── PackOpeningModal.jsx   ← Animación de apertura de sobres con revelación de carta
│       │   ├── TeamCustomizerModal.jsx← Modal para personalizar nombre, escudo y colores del equipo
│       │   └── WelcomeTeamModal.jsx   ← Modal de bienvenida al unirse a una liga (muestra los 15
│       │                              ←   jugadores asignados)
│       │
│       └── pages/                     ← Páginas/rutas de la aplicación (una por vista)
│           ├── LoginPage.jsx          ← Login con email/password, panel de marca a la izquierda
│           ├── RegisterPage.jsx       ← Registro con username/email/password, validaciones
│           ├── VerifyEmailPage.jsx    ← Verificación OTP con código de 6 dígitos
│           ├── PendingVerificationPage.jsx ← Página intermedia mientras espera verificación
│           ├── Dashboard.jsx          ← Página principal post-login: resumen de equipo, accesos rápidos
│           ├── LeaguesPage.jsx        ← Gestión de ligas: crear, unirse, invitaciones, abandonar
│           ├── LeagueDetailPage.jsx   ← Detalle de una liga: clasificación, mercado, sobres, info
│           ├── TeamManagementPage.jsx ← Gestión de equipo: pitch, formaciones, alineación, banquillo
│           ├── MarketPage.jsx         ← Portal del mercado: tendencias, acceso a mercados de ligas
│           ├── ArenaPage.jsx          ← Arena PvP: selección de equipo, combate con animación, historial
│           ├── PvPArenaPage.jsx       ← Versión alternativa de la Arena (legacy)
│           ├── ProfilePage.jsx        ← Perfil del usuario: info, ligas, bandeja de invitaciones
│           ├── AdminDashboard.jsx     ← Panel admin: stats, CRUD de usuarios/ligas/jugadores/equipos
│           ├── CardDetailPage.jsx     ← Detalle de un jugador: carta, precio, rareza, equipo
│           ├── PriceAnalysisPage.jsx  ← Análisis de precio: current vs target, señales de compra/venta
│           └── CookiesPage.jsx        ← Política de cookies (obligatorio legalmente)
│
└── docs/                              ← Documentación adicional del proyecto
    ├── QUICKSTART.md                  ← Guía de inicio rápido: pasos para levantar el proyecto
    ├── DEPLOY_INSTRUCTIONS.md         ← Instrucciones para migrar a otro ordenador
    ├── GUIA_CONFIGURACION.md          ← Configuración del sistema de puntos: balanceo configs
    ├── BACKUP_DATABASE.ps1            ← Script PowerShell para backup de MySQL
    └── portable_deploy.ps1            ← Script PowerShell para despliegue portable en otro PC
```

---

## API Reference

La API REST está documentada interactivamente con **Swagger UI**. Al ejecutar el backend, puedes acceder a la documentación completa en `http://localhost:8000/docs` y probar cualquier endpoint directamente desde el navegador.

A continuación se listan todos los endpoints organizados por módulo:

### Autenticación (`/api/auth`)

Gestiona el ciclo de vida completo de la autenticación: registro, verificación, login y perfil.

| Método | Endpoint | Descripción | Body / Params | Respuesta |
|---|---|---|---|---|
| `POST` | `/api/auth/register` | Crea un nuevo usuario y envía OTP por email | `{username, email, password}` | `{user, message}` |
| `POST` | `/api/auth/login` | Autentica y devuelve JWT | `{email, password}` | `{access_token, user}` |
| `GET` | `/api/auth/me` | Obtiene el perfil del usuario autenticado | Token en header | `{user}` |
| `GET` | `/api/auth/verify-email` | Verifica email con token (link) | `?token=xxx` | `{message}` |
| `POST` | `/api/auth/verify-email` | Verifica email con OTP de 6 dígitos | `{email, code}` | `{access_token}` |
| `POST` | `/api/auth/resend-verification` | Reenvía el código OTP | `?email=xxx` | `{message}` |
| `GET` | `/api/auth/search` | Busca usuarios por username | `?q=xxx&limit=5` | `[users]` |
| `PUT` | `/api/auth/profile` | Actualiza el perfil del usuario | `{username, avatar_url}` | `{user}` |

### Ligas (`/api/leagues`)

Todo lo relacionado con la creación, gestión y participación en ligas.

| Método | Endpoint | Descripción | Body / Params | Respuesta |
|---|---|---|---|---|
| `POST` | `/api/leagues/` | Crea una nueva liga y asigna 15 jugadores iniciales | `{name, description, max_members}` | `{league, assigned_players}` |
| `GET` | `/api/leagues/` | Lista todas las ligas del usuario | — | `[leagues]` |
| `GET` | `/api/leagues/{id}` | Detalle completo de una liga con miembros y sus stats | — | `{league, members, invite_code}` |
| `POST` | `/api/leagues/join/{code}` | Se une a una liga por código de invitación | — | `{league, assigned_players}` |
| `POST` | `/api/leagues/{id}/invite` | Invita a un usuario por username o email | `{username}` o `{email}` | `{message}` |
| `DELETE` | `/api/leagues/{id}/leave` | Abandona la liga (elimina equipo y membresía) | — | `{message}` |
| `DELETE` | `/api/leagues/{id}/kick/{userId}` | Expulsa a un miembro (solo admin/propietario) | — | `{message}` |
| `GET` | `/api/leagues/invitations/pending` | Invitaciones pendientes del usuario | — | `[invitations]` |
| `POST` | `/api/leagues/invitations/{id}/accept` | Acepta una invitación | — | `{league, assigned_players}` |
| `POST` | `/api/leagues/invitations/{id}/reject` | Rechaza una invitación | — | `{message}` |

### Equipos (`/api/teams`)

Gestión de equipos, alineaciones y puntos por jornada.

| Método | Endpoint | Descripción | Body / Params | Respuesta |
|---|---|---|---|---|
| `GET` | `/api/teams/my` | Mis equipos (todos o filtrado por liga) | `?league_id=X` | `[teams]` |
| `GET` | `/api/teams/{leagueId}/user/{userId}` | Equipo de otro usuario (solo lectura) | — | `{team, players}` |
| `PUT` | `/api/teams/my` | Actualiza equipo (nombre, formación, escudo, colores) | `{name, formation, shield_url}` | `{team}` |
| `PUT` | `/api/teams/my/lineup` | Establece la alineación de 11 titulares | `{lineup_card_ids: [1,2,3...]}` | `{team}` |
| `POST` | `/api/teams/my/release/{cardId}` | Libera un jugador (recupera 50% del valor) | — | `{message, coins_refunded}` |
| `GET` | `/api/teams/active-gameweek` | Obtiene la jornada activa actual | — | `{gameweek}` |
| `GET` | `/api/teams/my/gameweek-points` | Puntos por jornada del equipo actual | `?league_id=X` | `{total_points, gameweek_points: [{gameweek_number, points_earned}]}` |
| `GET` | `/api/teams/{leagueId}/user/{userId}/gameweek-points` | Puntos por jornada de otro usuario | — | `{total_points, gameweek_points}` |

### Jugadores (`/api/players`)

Catálogo de jugadores y cartas del usuario.

| Método | Endpoint | Descripción | Body / Params | Respuesta |
|---|---|---|---|---|
| `GET` | `/api/players/` | Lista jugadores (con filtros: posición, rareza, equipo, leyenda) | `?position=GK&rarity=gold&is_legend=true&search=kyogo` | `{players, total}` |
| `GET` | `/api/players/{id}` | Detalle completo de un jugador | — | `{player, stats, price_change_pct}` |
| `GET` | `/api/players/{id}/history` | Historial de rendimiento del jugador en partidos | — | `[match_stats]` |
| `GET` | `/api/players/my-cards/all` | Todas las cartas del usuario en todas las ligas | — | `[user_cards]` |

### Mercado (`/api/market`)

Toda la lógica del mercado: subastas, ventas, clausulazos, blindajes.

| Método | Endpoint | Descripción | Body / Params | Respuesta |
|---|---|---|---|---|
| `GET` | `/api/market/{leagueId}/auction` | Subasta activa con slots y pujas del usuario | — | `{auction, slots, server_time}` |
| `POST` | `/api/market/{leagueId}/bid/{slotId}` | Pujar en un slot de subasta | `{amount}` | `{message, new_locked_coins}` |
| `DELETE` | `/api/market/{leagueId}/bid/{slotId}` | Retirar puja de un slot | — | `{message}` |
| `GET` | `/api/market/{leagueId}/listings` | Listados de venta activos en la liga | — | `[listings]` |
| `POST` | `/api/market/{leagueId}/list/{cardId}` | Publicar una carta en venta | `{asking_price}` | `{listing}` |
| `DELETE` | `/api/market/{leagueId}/list/{listingId}` | Cancelar un listado activo | — | `{message}` |
| `POST` | `/api/market/{leagueId}/listing-bid/{listingId}` | Pujar por un listado | `{amount}` | `{message}` |
| `POST` | `/api/market/{leagueId}/listing-accept/{listingId}/{bidId}` | Aceptar una puja de un listado | — | `{message}` |
| `POST` | `/api/market/{leagueId}/clause/{cardId}` | Clausulazo: comprar jugador rival | — | `{message, new_coins}` |
| `POST` | `/api/market/{leagueId}/protect/{cardId}` | Blindar jugador (aumentar cláusula) | `{amount}` | `{message, new_protected_value}` |
| `GET` | `/api/market/{leagueId}/my-offers` | Ofertas del sistema por mis cartas | — | `[system_offers]` |
| `POST` | `/api/market/{leagueId}/accept-offer/{offerId}` | Aceptar oferta del sistema | — | `{message}` |
| `GET` | `/api/market/global-trends` | Jugadores más fichados (tendencias globales) | — | `[players]` |

### Arena PvP (`/api/arena`)

Simulación de combates y rankings.

| Método | Endpoint | Descripción | Body / Params | Respuesta |
|---|---|---|---|---|
| `GET` | `/api/arena/status` | Estado del usuario: ELO, tickets, wins/losses | — | `{global_elo, arena_tickets, arena_wins, arena_losses}` |
| `POST` | `/api/arena/simulate` | Simular un combate con un rival aleatorio | `{team_id}` | `{battle_result, opponent, coins_rewarded, rating_change}` |
| `GET` | `/api/arena/history` | Historial de batallas del usuario | `?limit=20` | `[battles]` |
| `GET` | `/api/arena/leaderboard` | Ranking global de los 50 mejores equipos | `?limit=50` | `[entries]` |

### Sobres (`/api/packs`)

Apertura de sobres de iconos.

| Método | Endpoint | Descripción | Body / Params | Respuesta |
|---|---|---|---|---|
| `POST` | `/api/packs/open` | Abrir un sobre de iconos | `?league_id=X` | `{cards, remaining_coins, message}` |
| `GET` | `/api/packs/history` | Historial de sobres abiertos | `?league_id=X` | `[pack_openings]` |

### Notificaciones (`/api/notifications`)

Sistema de notificaciones del usuario.

| Método | Endpoint | Descripción | Body / Params | Respuesta |
|---|---|---|---|---|
| `GET` | `/api/notifications/` | Notificaciones (filtradas por liga) | `?league_id=3&unread_only=true` | `[notifications]` |
| `GET` | `/api/notifications/unread-count` | Contador no leídas (por liga) | `?league_id=3` | `{unread_count}` |
| `POST` | `/api/notifications/{id}/read` | Marcar como leída | — | `{message}` |
| `POST` | `/api/notifications/read-all` | Marcar todas como leídas (liga) | `?league_id=3` | `{message}` |
| `DELETE` | `/api/notifications/{id}` | Eliminar notificación | — | `{message}` |
| `DELETE` | `/api/notifications/clear-all` | Borrar todas (por liga) | `?league_id=3` | `{message}` |

### Admin (`/api/admin`)

Panel de administración para gestión global. Requiere rol `admin`.

| Método | Endpoint | Descripción | Body / Params | Respuesta |
|---|---|---|---|---|
| `GET` | `/api/admin/stats` | Estadísticas globales del sistema | — | `{total_users, total_leagues, total_players, total_teams}` |
| `GET` | `/api/admin/users` | Listar usuarios | `?search=xxx` | `[users]` |
| `DELETE` | `/api/admin/users/{userId}` | Eliminar usuario y todos sus datos | — | `{message}` |
| `GET` | `/api/admin/leagues` | Listar ligas | `?search=xxx` | `[leagues]` |
| `DELETE` | `/api/admin/leagues/{leagueId}` | Eliminar liga | — | `{message}` |
| `GET` | `/api/admin/players` | Listar jugadores con filtros avanzados | `?search=xxx&position=GK&rarity=gold&is_legend=true&team=Celtic&limit=600` | `{players, total, available_teams}` |
| `PUT` | `/api/admin/players/{playerId}` | Editar jugador completo | `{name, age, nationality, position, overall_rating, pace, shooting, passing, dribbling, defending, physical, base_rarity, current_price, current_team, is_legend, image_url}` | `{message}` |
| `GET` | `/api/admin/teams` | Listar equipos | `?search=xxx` | `[teams]` |
| `GET` | `/api/admin/users/{userId}/league-coins` | Ver monedas del usuario por liga | — | `{user, leagues: [{league_id, league_name, coins, locked_coins, free_coins}]}` |
| `PUT` | `/api/admin/users/{userId}/league-coins` | Ajustar monedas del usuario | `{league_id, coins, reconcile}` | `{message}` |

---

## Instalación y Despliegue

### Prerrequisitos

Antes de comenzar, asegúrate de tener instalados:

- **Docker Desktop** (incluye Docker Compose): [Descargar aquí](https://www.docker.com/products/docker-desktop)
- **Git** (opcional, para clonar el repositorio): [Descargar aquí](https://git-scm.com/)

Verifica la instalación:
```bash
docker --version        # Debe mostrar Docker version 20.x+
docker compose version  # Debe mostrar Docker Compose version v2.x+
```

### Despliegue con Docker (Recomendado)

Este método levanta toda la aplicación con un solo comando. No necesitas instalar Python, Node.js ni MySQL en tu máquina.

**Paso 1: Obtener el código**

```bash
# Opción A: Clonar el repositorio (si está en GitHub)
git clone <url-del-repo>
cd ProyectoFinCurso

# Opción B: Copiar la carpeta del proyecto desde otro lugar
cd C:\Users\abdul22\OneDrive\Escritorio\ProyectoFinCurso
```

**Paso 2: Configurar variables de entorno**

Edita el archivo `.env` en la raíz del proyecto. Este archivo contiene las credenciales y configuraciones sensibles:

```env
# Contraseña root de MySQL (puedes cambiarla)
MYSQL_ROOT_PASSWORD=tu_password_mysql_aqui

# API Key de Sportmonks (obtener en sportmonks.com)
SPORTMONKS_API_KEY=tu_api_key_aqui

# Clave secreta para JWT (generar con: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=tu_clave_secreta_aqui

# URL del frontend (para CORS)
FRONTEND_URL=http://localhost:3000

# SMTP para verificación de email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_app_password_de_gmail

# Saltar verificación de email en desarrollo (true/false)
BYPASS_EMAIL_VERIFICATION=false
```

> **Nota importante**: Para obtener un App Password de Gmail, ve a tu cuenta de Google → Seguridad → Verificación en dos pasos → Contraseñas de aplicaciones.

**Paso 3: Levantar los servicios**

```bash
docker compose up -d --build
```

Este comando:
1. Construye la imagen del backend (instala dependencias Python)
2. Construye la imagen del frontend (instala dependencias npm y compila)
3. Descarga la imagen de MySQL 8.0
4. Inicia los 3 contenedores en orden (primero DB, luego backend, luego frontend)
5. Ejecuta el script `ultimate_fantasy_legends.sql` para crear todas las tablas y datos iniciales

**Paso 4: Verificar que todo funciona**

```bash
# Ver el estado de los contenedores
docker compose ps

# Deberías ver 3 contenedores con status "Up":
# football-fantasy-db     (MySQL)
# football-fantasy-backend (FastAPI)
# football-fantasy-frontend (Nginx)

# Ver los logs del backend para confirmar que el scheduler inició
docker compose logs backend

# Deberías ver algo como:
# ✅ Tablas verificadas/creadas correctamente
# 📁 Carpeta static/players/ verificada
# 📅 Scheduler iniciado correctamente
```

**Paso 5: Acceder a la aplicación**

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Swagger UI (documentación interactiva)**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Desarrollo Local (sin Docker)

Si prefieres desarrollar sin Docker (para tener hot-reloading más rápido, depuración con breakpoints, etc.):

**Backend:**

```bash
cd backend

# Crear entorno virtual
python -m venv venv

# Activar
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Asegurarte de que MySQL está corriendo localmente
# y crear la base de datos:
mysql -u root -p -e "CREATE DATABASE ultimate_fantasy_legends;"

# Cargar el schema inicial
mysql -u root -p ultimate_fantasy_legends < ultimate_fantasy_legends.sql

# Iniciar el servidor
uvicorn app.main:app --reload
```

El servidor estará en `http://localhost:8000`.

**Frontend:**

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar el servidor de desarrollo
npm run dev
```

El frontend estará en `http://localhost:5173` (Vite redirige las peticiones `/api` al backend en `localhost:8000` automáticamente).

### Tabla Completa de Variables de Entorno

| Variable | Descripción | Obligatorio | Ejemplo |
|---|---|---|---|
| `MYSQL_ROOT_PASSWORD` | Contraseña del usuario root de MySQL | Sí | `tu_password_mysql` |
| `MYSQL_USER` | Usuario de la BD (por defecto root) | No | `root` |
| `MYSQL_PORT` | Puerto de MySQL (por defecto 3306) | No | `3306` |
| `MYSQL_DATABASE` | Nombre de la BD | Sí | `ultimate_fantasy_legends` |
| `SPORTMONKS_API_KEY` | API key de Sportmonks para datos reales | Sí (para sync) | `tu_api_key_aqui` |
| `SECRET_KEY` | Clave secreta para firmar JWTs | Sí | `tu_clave_secreta_aqui` |
| `FRONTEND_URL` | URL del frontend (para CORS) | No | `http://localhost:3000` |
| `SMTP_HOST` | Servidor SMTP para envío de emails | No | `smtp.gmail.com` |
| `SMTP_PORT` | Puerto SMTP | No | `587` |
| `SMTP_USER` | Cuenta de email para envíos | No | `tu_email@gmail.com` |
| `SMTP_PASSWORD` | App password del email | No | `tu_app_password_de_gmail` |
| `BYPASS_EMAIL_VERIFICATION` | Saltar verificación OTP en desarrollo | No | `false` |
| `ENVIRONMENT` | Entorno (development/production) | No | `development` |

### Solución de Problemas Comunes

**El contenedor de MySQL no arranca:**
```bash
# Ver los logs
docker compose logs db

# Si dice "Port already in use", otro servicio está usando el puerto 3306
# Solución: detén el servicio MySQL local o cambia el puerto en docker-compose.yml
```

**El backend no puede conectar a la BD:**
```bash
# Verifica que MySQL está healthy
docker compose ps db

# Intenta conectar manualmente
docker exec -it football-fantasy-db mysql -u root -ptu_password_mysql_aqui -e "SHOW DATABASES;"
```

**El frontend no encuentra la API:**
```bash
# Verifica que el proxy de Vite está configurado
cat frontend/vite.config.js
# Debe tener: proxy: { '/api': 'http://localhost:8000' }
```

**La base de datos no tiene datos:**
```bash
# Recargar el schema
docker exec -i football-fantasy-db mysql -u root -ptu_password_mysql_aqui ultimate_fantasy_legends < ultimate_fantasy_legends.sql
```

---

### Cuentas de Prueba

Para facilitar la demostración del proyecto, se incluye una cuenta pre-configurada con acceso completo a todas las funcionalidades:

| Email | Contraseña | Rol | Descripción |
|---|---|---|---|
| `user@user.com` | `123456` | Usuario (FREE) | Cuenta limpia sin datos. Ideal para simular el flujo completo de registro, creación de liga y fichajes desde cero. |

> **Nota**: Estas cuentas solo existen en entornos de desarrollo local. La contraseña `123456` es exclusivamente para pruebas y no debe usarse en producción.

---

## Capturas de Pantalla

> **Nota**: Las siguientes capturas son representaciones ASCII de la interfaz. Para ver la aplicación real, despliega el proyecto y accede a `http://localhost:3000`.

### 1. Pantalla de Login

Diseño de dos paneles: a la izquierda, branding con el logo de UFL y características clave; a la derecha, formulario de login.

```
┌──────────────────────────────────────────────────────────────┐
│  PANEL IZQUIERDO (Marca)        │  PANEL DERECHO (Formulario)│
│                                  │                            │
│  🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Premiership   │  Bienvenido de nuevo       │
│                                  │                            │
│       ┌──────────────┐           │  Email                     │
│       │   🏆 UFL     │           │  ┌────────────────────┐   │
│       │   Logo       │           │  │ tu@email.com       │   │
│       └──────────────┘           │  └────────────────────┘   │
│                                  │                            │
│  Ultimate Fantasy                │  Contraseña                │
│  Legends                         │  ┌────────────────────┐   │
│                                  │  │ ••••••••••    👁️   │   │
│  Construye tu equipo             │  └────────────────────┘   │
│  ideal, ficha estrellas          │                            │
│  en el mercado y compite         │  ┌────────────────────┐   │
│  en ligas privadas               │  │   Entrar al Juego  │   │
│                                  │  └────────────────────┘   │
│  ┌──────────────────────────┐   │                            │
│  │ 🏆 Ligas Privadas        │   │  ───── ¿nuevo aquí? ────── │
│  │ Compite contra amigos    │   │                            │
│  │                          │   │  ¿No tienes cuenta?        │
│  │ 💰 Mercado en Vivo       │   │  Regístrate gratis →       │
│  │ Subasta y ficha en real  │   │                            │
│  │                          │   │                            │
│  │ ⭐ Jugadores Icono       │   │                            │
│  │ Consigue leyendas        │   │                            │
│  └──────────────────────────┘   │                            │
└─────────────────────────────────┴────────────────────────────┘
```

### 2. Dashboard Principal

La página principal tras el login. Muestra un resumen del equipo del usuario y accesos rápidos a las funcionalidades principales.

```
┌──────────────────────────────────────────────────────────────┐
│  🔔 3              👤 Abdul              Cerrar Sesión       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────┐            │
│  │  ┌──────┐                                   │   [SPFL]   │
│  │  │   A  │  Liga de Amigos                   │   Logo     │
│  │  └──────┘                                   │            │
│  │                                              │            │
│  │  Bienvenido, Abdul                           │            │
│  │  Gestiona tu plantilla, ficha estrellas      │            │
│  │  y compite.                                  │            │
│  └─────────────────────────────────────────────┘            │
│                                                              │
│  Tu Club                                        Mis Ligas ›  │
│  ┌─────────────────────────────────────────────┐            │
│  │   ⭕ 78          🛡️                         │            │
│  │   OVR          FC Legends                    │    ›       │
│  │                                              │            │
│  │  ⚽ Liga de Amigos                            │            │
│  │  11 Titulares · 4-4-2 · 15 Jugadores         │            │
│  └─────────────────────────────────────────────┘            │
│                                                              │
│  Accesos Rápidos                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  💸      │ │  ⚔️      │ │  🏆      │ │  👤      │       │
│  │ Mercado  │ │ FootArena│ │ Ligas    │ │ Perfil   │       │
│  │ Subastas │ │ Combates │ │ Clasi.   │ │ Historial│       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 3. Gestión de Equipo (Pitch Interactivo)

La página de gestión de equipo muestra el campo de fútbol con los titulares en sus posiciones, el banquillo y las opciones de formación.

```
┌──────────────────────────────────────────────────────────────┐
│  ← Mi Equipo              💰 €45.2M     OVR 78.5            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ✏️ Personalizar                                             │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🏟️ JORNADA 12        Límite: 15/03 20:00             ││
│  │  ✅ Equipo guardado para esta jornada                   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  Formación: [4-4-2 ▼]              💾 Guardar               │
│                                                              │
│  ⚽ Titulares (11/11)                                       │
│                                                              │
│  ╔═══════════════════════════════════════════════════════╗  │
│  ║                                                       ║  │
│  ║                    ┌─────┐                            ║  │
│  ║                    │ GK  │  Onana  82                  ║  │
│  ║                    └─────┘                            ║  │
│  ║                                                       ║  │
│  ║         ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐              ║  │
│  ║         │ DEF │ │ DEF │ │ DEF │ │ DEF │              ║  │
│  ║         │ 75  │ │ 78  │ │ 80  │ │ 74  │              ║  │
│  ║         └─────┘ └─────┘ └─────┘ └─────┘              ║  │
│  ║                                                       ║  │
│  ║         ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐              ║  │
│  ║         │ MID │ │ MID │ │ MID │ │ MID │              ║  │
│  ║         │ 81  │ │ 76  │ │ 79  │ │ 73  │              ║  │
│  ║         └─────┘ └─────┘ └─────┘ └─────┘              ║  │
│  ║                                                       ║  │
│  ║              ┌─────┐ ┌─────┐                          ║  │
│  ║              │ FWD │ │ FWD │                          ║  │
│  ║              │ 85  │ │ 83  │  ← Kyogo                  ║  │
│  ║              └─────┘ └─────┘                          ║  │
│  ║                                                       ║  │
│  ╚═══════════════════════════════════════════════════════╝  │
│                                                              │
│  🪑 Banquillo (4)                                            │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                       │
│  │🃏 DEF│ │🃏 MID│ │🃏 FWD│ │🃏 MID│                       │
│  │ 72   │ │ 68   │ │ 74   │ │ 70   │                       │
│  └──────┘ └──────┘ └──────┘ └──────┘                       │
│                                                              │
│  📊 Puntos por Jornada                                       │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │ J1   │ │ J2   │ │ J3   │ │ J4   │ │ J5   │              │
│  │ 42.3 │ │ 55.1 │ │ 38.7 │ │ 61.2 │ │ 47.8 │              │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 4. Subasta de Mercado

La vista de subasta muestra los 12 jugadores disponibles, el tiempo restante y los controles de puja.

```
┌──────────────────────────────────────────────────────────────┐
│  🛍️ Mercado                              🪙 50.2M  🔒 12M   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  🎁 Comprar Sobres                                     │ │
│  │  Refuerza tu plantilla abriendo sobres de jugadores.   │ │
│  │                                  ›                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  🔥 En Tendencia Global                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ 🃏 Kyogo │ │ 🃏 Hatate│ │ 🃏 Maeda │  → scroll          │
│  │ 85 FWD   │ │ 82 MID   │ │ 79 FWD   │                    │
│  │ €18.5M   │ │ €12.3M   │ │ €9.8M    │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
│                                                              │
│  Mercados de Ligas                                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  🏆 Liga de Amigos · 6 miembros · Subastas activas  ›  │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  🏆 Liga Pro · 10 miembros · Subastas activas       ›  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘

DETALLE DE SUBASTA (dentro de una liga):

┌──────────────────────────────────────────────────────────────┐
│  ⏳ Subasta Diaria                                           │
│  Tiempo restante: 08h 23m 15s                               │
├──────────────────────────────────────────────────────────────┤
│  Jugador              Puja/Base           Acción            │
│  ─────────────────────────────────────────────────────────  │
│  🃏 Robertson DEF 85  €8.5M              [8.6M] [Pujar]     │
│     Celtic FC         3 pujas activas     [Retirar]         │
│  ─────────────────────────────────────────────────────────  │
│  🃏 Kyogo FWD 85     €18.5M              [     ] [Pujar]    │
│     Celtic FC         Sin participación                      │
│  ─────────────────────────────────────────────────────────  │
│  🃏 McGinn MID 82    €6.2M               [     ] [Pujar]    │
│     Aston Villa       Sin participación                      │
│  ─────────────────────────────────────────────────────────  │
│  🃏 Dykes FWD 78     €4.1M               [4.5M] [Actualizar]│
│     QPR               Mi puja: €4.5M      [Retirar]         │
│  ─────────────────────────────────────────────────────────  │
│  ... (8 jugadores más)                                      │
└──────────────────────────────────────────────────────────────┘
```

### 5. Arena PvP

La página de combate muestra el ELO del usuario, los tickets disponibles, la selección de equipo y el historial de batallas.

```
┌──────────────────────────────────────────────────────────────┐
│  ⚔️ FOOT ARENA                          ⚔️ TEMPORADA 25-26  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │
│  │ 1245   │ │   3    │ │   12   │ │   3    │ │   8    │    │
│  │ ELO    │ │ Tickets│ │ Vict.  │ │ Empat. │ │ Derrot.│    │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘    │
│                                                              │
│  Combate  │  Historial  │  Rankings                          │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  Selecciona el equipo que representarás en el combate        │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐                           │
│  │     🛡️     │  │     🛡️     │                           │
│  │ FC Legends  │  │ Rangers FC  │                           │
│  │ Liga Amigos │  │ Liga Pro    │                           │
│  │ OVR 78  ✓   │  │ OVR 82      │                           │
│  └─────────────┘  └─────────────┘                           │
│                                                              │
│  ─────────────── VS ───────────────                          │
│                                                              │
│  ┌─────────────────┐        ┌─────────────────┐             │
│  │    🛡️ FC Legends │        │      ❓          │             │
│  │    OVR 78       │   VS   │   Rival aleat.  │             │
│  │    Liga Amigos  │        │   Buscando...   │             │
│  └─────────────────┘        └─────────────────┘             │
│                                                              │
│              ┌──────────────────┐                           │
│              │  ⚔️ COMBATIR     │                           │
│              └──────────────────┘                           │
│              3 tickets disponibles · Consume 1 ticket        │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│  Historial de batallas                                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ VIT  3 - 1  vs Celtic FC        +15 ELO  12/03/2026   │ │
│  │ DER  0 - 2  vs Rangers FC       -12 ELO  11/03/2026   │ │
│  │ VIT  2 - 1  vs Aberdeen FC      +18 ELO  10/03/2026   │ │
│  │ EMP  1 - 1  vs Hearts FC        +2 ELO   09/03/2026   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Rankings (Top 50)                                           │
│  ┌─────┬──────────────────┬──────┬───┬───┬───┐              │
│  │ #   │ Jugador          │ ELO  │ V │ E │ D │              │
│  ├─────┼──────────────────┼──────┼───┼───┼───┤              │
│  │ 🥇  | xXProGamerXx     │ 1523 │25 │ 3 │ 5 │              │
│  │ 🥈  | ElManager        │ 1489 │22 │ 5 │ 6 │              │
│  │ 🥉  | FantasyKing      │ 1456 │20 │ 4 │ 8 │              │
│  │ #4  | Abdul (Tú)       │ 1245 │12 │ 3 │ 8 │              │
│  └─────┴──────────────────┴──────┴───┴───┴───┘              │
└──────────────────────────────────────────────────────────────┘
```

---

## Guía de Contribución

### Flujo de Trabajo con Git

El proyecto sigue un modelo de branching simple y efectivo:

```
main                    ← Rama principal: código estable, listo para producción
  │
  ├── feature/xxx       ← Nuevas funcionalidades (ej: feature/chat-ligas)
  ├── fix/xxx           ← Corrección de bugs (ej: fix/monedas-bloqueadas)
  ├── refactor/xxx      ← Mejoras de código sin cambio funcional
  └── docs/xxx          ← Actualización de documentación
```

**Reglas:**
- Nunca hacer push directo a `main`. Siempre crear una branch.
- Hacer merge a `main` solo a través de Pull Requests.
- Cada PR debe tener al menos una revisión de otro desarrollador.

### Cómo Contribuir Paso a Paso

**1. Fork y clonación**

```bash
# Fork el repositorio en GitHub, luego clona tu fork
git clone https://github.com/TU-USUARIO/ProyectoFinCurso.git
cd ProyectoFinCurso

# Añade el repo original como remoto upstream
git remote add upstream https://github.com/ORIGINAL/ProyectoFinCurso.git
```

**2. Crear una branch**

```bash
# Siempre partir de main actualizado
git checkout main
git pull upstream main

# Crear branch descriptiva
git checkout -b feature/nombre-de-la-funcionalidad
# Ejemplos:
#   feature/arena-leaderboard-pagination
#   feature/chat-entre-miembros-liga
#   fix/calcular-monedas-bloqueadas
#   refactor/optimizar-query-subastas
```

**3. Desarrollar y probar**

```bash
# Backend: ejecutar tests
cd backend
python -m pytest

# Frontend: verificar build
cd frontend
npm run build
```

**4. Commits descriptivos**

```bash
# Añadir archivos
git add .

# Commit con mensaje descriptivo
git commit -m "feat: añadir paginación al leaderboard de Arena

- Implementar paginación con offset/limit de 50 en 50
- Añadir scroll infinito en el componente frontend
- Actualizar endpoint GET /api/arena/leaderboard"

# Push al remoto
git push origin feature/arena-leaderboard-pagination
```

**5. Pull Request**

Abre un PR en GitHub con:
- **Título**: Usa el mismo formato del commit (`feat: descripción`)
- **Descripción**: Qué cambia y por qué
- **Capturas**: Si hay cambios visuales, incluye before/after
- **Tests**: Menciona los tests ejecutados

### Convenciones de Código

#### Backend (Python)

```python
# ✅ CORRECTO
from sqlalchemy.orm import Session

def calculate_fantasy_points(stats: PlayerMatchStats, position: str) -> float:
    """Calcula los puntos fantasy de un jugador según su posición y stats.
    
    Args:
        stats: Objeto PlayerMatchStats con las estadísticas del partido.
        position: Posición del jugador (GK, DEF, MID, FWD).
    
    Returns:
        Puntos fantasy totales como float.
    """
    points = 0.0
    # ... lógica
    return points

# ❌ INCORRECTO
def calc(stats, pos):
    p = 0
    # sin docstring, nombres crípticos
```

- **PEP 8**: Indentación con 4 espacios, líneas máximo 88 caracteres (Black), imports ordenados.
- **Type hints**: Obligatorio en funciones públicas.
- **Docstrings**: Obligatorio en todos los routers y funciones de servicios.
- **Naming**: `snake_case` para variables y funciones, `PascalCase` para clases.
- **Estructura**: Modelos en `models/`, schemas en `schemas/`, lógica de negocio en `services/`.

#### Frontend (React)

```jsx
// ✅ CORRECTO
export default function TeamManagementPage() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    try {
      const res = await teamsAPI.getMy();
      setTeams(res.data);
    } catch (error) {
      toast.error('Error al cargar equipos');
    } finally {
      setLoading(false);
    }
  };

  // ... return JSX
}

// ❌ INCORRECTO
const page = () => {
  const [data, setData] = React.useState([]);
  // class component, mixing styles, etc.
}
```

- **Componentes funcionales** con hooks (no class components).
- **Naming**: `PascalCase` para componentes (`TeamManagementPage`), `camelCase` para funciones y variables.
- **CSS**: Usar variables de `variables.css` para colores, no hardcodear valores.
- **Archivos**: Cada página tiene su `.jsx` y `.css` en `pages/`.
- **API calls**: Siempre a través de `endpoints.js`, nunca axios directo en componentes.

### Estándar de Commits (Conventional Commits)

| Prefijo | Cuándo usarlo | Ejemplo |
|---|---|---|
| `feat:` | Nueva funcionalidad visible para el usuario | `feat: añadir sistema de notificaciones push` |
| `fix:` | Corrección de un bug | `fix: corregir cálculo de monedas bloqueadas en subastas` |
| `refactor:` | Mejora de código sin cambio funcional | `refactor: extraer lógica de scoring a servicio separado` |
| `docs:` | Cambios en documentación | `docs: actualizar README con nuevos endpoints de Arena` |
| `style:` | Cambios de estilo visual | `style: ajustar colores del marketplace para mejor contraste` |
| `test:` | Añadir o modificar tests | `test: añadir tests unitarios al scoring calculator` |
| `chore:` | Mantenimiento, dependencias, configs | `chore: actualizar FastAPI a 0.104.1` |
| `perf:` | Mejoras de rendimiento | `perf: optimizar query de subastas con índice compuesto` |

---

## Trabajo Futuro

### Corto Plazo (1-3 meses)

| Feature | Descripción | Prioridad |
|---|---|---|
| **Notificaciones push** | Notificaciones en tiempo real (push del navegador) para clausulazos, resultados de subasta y ofertas del sistema. Usa la Web Push API. | Alta |
| **Auditoría de transacciones** | Registro completo de todas las operaciones económicas (compras, ventas, recompensas, clausulazos) con saldo anterior, saldo posterior y descripción. Tabla `transaction_log` consultable desde el perfil. | Alta |
| **WebSockets** | Reemplazar el polling de 10s en el mercado con WebSockets para actualizaciones en tiempo real. El backend emite eventos cuando cambia una subasta. | Alta |
| **Paginación** | Implementar paginación real (offset/limit) en el leaderboard de Arena y listados de mercado. Actualmente se cargan todos los datos de una vez. | Media |
| **Estadísticas avanzadas** | Gráficas de rendimiento por jornada para cada jugador (líneas de puntos, goles, asistencias). Integrar Chart.js o Recharts. | Media |
| **Chat de liga** | Canal de chat entre miembros de la misma liga. Mensajes con timestamp, username y opción de emoji. Almacenar en BD. | Media |

### Medio Plazo (3-6 meses)

| Feature | Descripción | Prioridad |
|---|---|---|
| **App móvil nativa** | Desarrollar app con React Native reutilizando la API actual. Mismos endpoints, interfaz adaptada a móvil. | Alta |
| **Expansión de ligas** | Añadir la Premier League, La Liga y Serie A al catálogo de jugadores. Permitir ligas multi-liga donde los usuarios eligen qué liga usar. | Alta |
| **Modo draft** | Al crear una liga, elegir modo "draft": los jugadores se seleccionan en orden snake (1-2-3-3-2-1) hasta completar las plantillas. Más estratégico que la asignación automática. | Media |
| **Transferencias entre ligas** | Permitir que un usuario transfiera jugadores de su equipo en una liga a otra liga del mismo usuario (con coste de monedas). | Media |
| **Sistema de logros** | Medallas desbloqueables: "Primer gol", "Subasta perfecta", "10 victorias en Arena", "Millonario". Mostrar en el perfil del usuario. | Baja |

### Largo Plazo (6+ meses)

| Feature | Descripción | Prioridad |
|---|---|---|
| **Eventos Live** | Durante partidos de alto voltaje (Old Firm: Celtic vs Rangers), activar bonificadores temporales: goles x2, asistencias x1.5, etc. El scheduler detecta estos partidos en tiempo real. | Media |
| **Modo Manager** | Modo Career: gestión de presupuesto salarial, fichajes libres, desarrollo de jóvenes, scouting. Más profundo que el fantasy actual. | Baja |
| **Machine Learning** | Modelo predictivo que analice datos históricos de jugadores y partidos para predecir rendimiento futuro. Útil para el análisis de precio. | Baja |
| **API pública** | Documentar y publicar la API para que desarrolladores externos puedan crear herramientas (dashboards, bots, estadísticas). Con rate limiting y API keys. | Baja |
| **Internacionalización** | Soporte multi-idioma (inglés, español, francés). Usar i18next en frontend y gettext en backend. | Baja |

---

## Licencia

Este proyecto está desarrollado como parte de un **Trabajo de Fin de Grado** con fines académicos y educativos. El código está disponible para su consulta, estudio y uso educativo.

---

> Desarrollado con pasión por la tecnología y el fútbol, buscando siempre la excelencia en el diseño de software y la experiencia de usuario. ⚽
