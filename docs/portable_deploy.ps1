# 🚀 Ultimate Fantasy Legends - One-Click Deploy
# Este script prepara el entorno y levanta los contenedores.

$ProjectRoot = Get-Location
$BackendEnv = Join-Path $ProjectRoot "backend\.env"
$DockerCompose = Join-Path $ProjectRoot "docker-compose.yml"

Write-Host "--- Iniciando Despliegue Portable ---" -ForegroundColor Cyan

# 1. Verificar Docker
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Error: Docker no está instalado o no está en el PATH." -ForegroundColor Red
    exit
}

# 2. Verificar .env
if (!(Test-Path $BackendEnv)) {
    Write-Host "📝 Creando archivo .env básico..." -ForegroundColor Yellow
    $DefaultEnv = "SPORTMONKS_API_KEY=tu_api_key_aqui`nMYSQ_ROOT_PASSWORD=fantasyleague2026"
    Set-Content -Path $BackendEnv -Value $DefaultEnv
    Write-Host "⚠️ Se ha creado un .env genérico en backend/.env. Por favor, edítalo con tu API Key." -ForegroundColor DarkYellow
}

# 3. Preparar Base de Datos (opcional)
# El docker-compose ya importa ultimate_fantasy_legends.sql si el volumen está vacío.
if (Test-Path "ultimate_fantasy_legends_latest.sql") {
    Write-Host "📦 Se ha detectado un volcado de base de datos reciente (ultimate_fantasy_legends_latest.sql)." -ForegroundColor Blue
    # Si quisieras forzar la importación, podrías hacerlo aquí, 
    # pero es mejor dejar que docker-compose init lo haga o usar el script de backup.
}

# 4. Levantar Contenedores
Write-Host "🏗️  Construyendo y levantando contenedores..." -ForegroundColor Green
docker-compose up -d --build

Write-Host "`n✅ ¡Despliegue completado!" -ForegroundColor Green
Write-Host "🌐 Frontend: http://localhost" -ForegroundColor Cyan
Write-Host "🔌 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 Docs: http://localhost:8000/docs" -ForegroundColor Gray
