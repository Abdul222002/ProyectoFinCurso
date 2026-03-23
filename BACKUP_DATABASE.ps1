# 📦 Ultimate Fantasy Legends - Database Backup
# Exporta el estado actual de la base de datos a un archivo portable.

$BackupFile = "ultimate_fantasy_legends_latest.sql"
Write-Host "--- Iniciando Respaldo de Base de Datos ---" -ForegroundColor Cyan

# 1. Verificar si el contenedor está corriendo
$ContainerID = docker ps -qf "name=football-fantasy-db"
if (!$ContainerID) {
    Write-Host "❌ Error: El contenedor de base de datos no está corriendo." -ForegroundColor Red
    exit
}

# 2. Exportar con mysqldump
Write-Host "🔋 Exportando base de datos a $BackupFile..." -ForegroundColor Yellow
docker exec football-fantasy-db mysqldump -u root -pfantasyleague2026 ultimate_fantasy_legends > $BackupFile

if (Test-Path $BackupFile) {
    Write-Host "✅ Base de datos respaldada con éxito en $BackupFile" -ForegroundColor Green
    Write-Host "💡 Copia este archivo a tu otro ordenador para mantener el progreso." -ForegroundColor Cyan
} else {
    Write-Host "❌ Error al generar el respaldo." -ForegroundColor Red
}
