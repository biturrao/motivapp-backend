# Script para aplicar migración de base de datos en Azure PostgreSQL
# Uso: .\apply-migration.ps1

param(
    [Parameter(Mandatory=$false)]
    [string]$MigrationFile = "migrations\001_add_summary_column.sql"
)

Write-Host "🔧 Aplicando migración: $MigrationFile" -ForegroundColor Cyan

# Leer variables de entorno del archivo .env si existe
if (Test-Path ".env") {
    Write-Host "📄 Leyendo configuración desde .env..." -ForegroundColor Yellow
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

# Obtener credenciales de base de datos
$DB_HOST = $env:DATABASE_HOST
$DB_NAME = $env:DATABASE_NAME
$DB_USER = $env:DATABASE_USER
$DB_PASSWORD = $env:DATABASE_PASSWORD

if (-not $DB_HOST -or -not $DB_NAME -or -not $DB_USER) {
    Write-Host "❌ Error: Faltan variables de entorno de base de datos" -ForegroundColor Red
    Write-Host "   Asegúrate de tener configurado:" -ForegroundColor Yellow
    Write-Host "   - DATABASE_HOST" -ForegroundColor Yellow
    Write-Host "   - DATABASE_NAME" -ForegroundColor Yellow
    Write-Host "   - DATABASE_USER" -ForegroundColor Yellow
    Write-Host "   - DATABASE_PASSWORD" -ForegroundColor Yellow
    exit 1
}

Write-Host "🔗 Conectando a: $DB_HOST/$DB_NAME" -ForegroundColor Green

# Verificar si psql está instalado
$psqlPath = Get-Command psql -ErrorAction SilentlyContinue

if (-not $psqlPath) {
    Write-Host "❌ Error: psql no está instalado" -ForegroundColor Red
    Write-Host "   Descarga PostgreSQL desde: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    Write-Host "" -ForegroundColor Yellow
    Write-Host "   Alternativa: Aplica manualmente el SQL desde Azure Portal:" -ForegroundColor Cyan
    Write-Host "   1. Ve a Azure Portal → Tu PostgreSQL Database" -ForegroundColor White
    Write-Host "   2. Ve a 'Query editor'" -ForegroundColor White
    Write-Host "   3. Copia y pega el contenido de: $MigrationFile" -ForegroundColor White
    Write-Host "" -ForegroundColor White
    Write-Host "   Contenido del archivo:" -ForegroundColor Cyan
    Write-Host "   ======================" -ForegroundColor Cyan
    Get-Content $MigrationFile | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
    exit 1
}

# Aplicar migración
Write-Host "⚡ Aplicando migración..." -ForegroundColor Cyan

$env:PGPASSWORD = $DB_PASSWORD

try {
    & psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f $MigrationFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Migración aplicada exitosamente" -ForegroundColor Green
    } else {
        Write-Host "❌ Error al aplicar la migración" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
} finally {
    Remove-Item env:PGPASSWORD -ErrorAction SilentlyContinue
}

Write-Host "" -ForegroundColor White
Write-Host "🎉 ¡Listo! Ahora puedes hacer deploy de la aplicación" -ForegroundColor Green
