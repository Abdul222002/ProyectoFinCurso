"""
FastAPI Main Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Routers
from app.routers.auth import router as auth_router
from app.routers.leagues import router as leagues_router
from app.routers.teams import router as teams_router
from app.routers.players import router as players_router
from app.routers.market import router as market_router
from app.routers.arena import router as arena_router
from app.routers.packs import router as packs_router
from app.routers.admin import router as admin_router

from contextlib import asynccontextmanager
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from app.core.config import settings
# Database
from app.core.database import engine
from app.models.models import Base
from app.core.scheduler import start_scheduler, stop_scheduler

app = FastAPI(
    title="Ultimate Fantasy Legends API",
    description="API para plataforma de Fantasy Football con mecánicas de FIFA y Pokémon",
    version="0.2.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Configuración de CORS
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if settings.ENVIRONMENT == "production" else ["*"],
    allow_origin_regex="https?://.*\.railway\.app" if settings.ENVIRONMENT == "production" else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# STARTUP — Crear tablas nuevas si no existen
# ==========================================

@app.on_event("startup")
async def on_startup():
    """Crea tablas que falten y garantiza que la carpeta de estáticos existe"""
    import os
    # Garantizar que la carpeta existe antes de montar StaticFiles
    os.makedirs("static/players", exist_ok=True)
    # Montar archivos estáticos (imágenes de jugadores)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas verificadas/creadas correctamente")
    print("📁 Carpeta static/players/ verificada")
    start_scheduler()


@app.on_event("shutdown")
async def on_shutdown():
    stop_scheduler()
    print("🛑 Tareas en segundo plano detenidas.")


@app.get("/")
async def root():
    """Endpoint raíz — Verificación de que la API está funcionando"""
    return {
        "message": "⚽ Bienvenido a Ultimate Fantasy Legends API",
        "version": "0.2.0",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}


# ==========================================
# ROUTERS
# ==========================================

app.include_router(auth_router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(leagues_router, prefix="/api/leagues", tags=["Ligas"])
app.include_router(teams_router, prefix="/api/teams", tags=["Equipos"])
app.include_router(players_router, prefix="/api/players", tags=["Jugadores"])
app.include_router(market_router, prefix="/api/market", tags=["Mercado"])
app.include_router(arena_router, prefix="/api/arena", tags=["Arena PvP"])
app.include_router(packs_router, prefix="/api/packs", tags=["Sobres"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

