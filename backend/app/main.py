"""
FastAPI Main Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importaremos los routers cuando los creemos
# from app.routers import players, teams, market, auth

app = FastAPI(
    title="Ultimate Fantasy Legends API",
    description="API para plataforma de Fantasy Football con mecánicas de FIFA y Pokémon",
    version="0.1.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Configuración de CORS (para que React pueda conectarse)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # URL del frontend Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Endpoint raíz - Verificación de que la API está funcionando
    """
    return {
        "message": "⚽ Bienvenido a Ultimate Fantasy Legends API",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint - Útil para monitoreo
    """
    return {
        "status": "healthy",
        "database": "pending_connection"  # Lo actualizaremos cuando conectemos MySQL
    }


# Cuando creemos los routers, los incluiremos así:
# app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
# app.include_router(players.router, prefix="/api/players", tags=["Jugadores"])
# app.include_router(teams.router, prefix="/api/teams", tags=["Equipos"])
# app.include_router(market.router, prefix="/api/market", tags=["Mercado"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
