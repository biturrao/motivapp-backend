# Script PowerShell para limpiar ejercicios en Azure PostgreSQL
# Ejecutar desde la carpeta motivapp-backend

# Variables (AJUSTA ESTOS VALORES)
$DB_SERVER = "motivapp-backend-server.postgres.database.azure.com"
$DB_NAME = "motivapp-backend-database"
$DB_USER = "motivappadmin"
$DB_PASSWORD = "TU_PASSWORD_AQUI"  # Reemplazar con tu password

Write-Host "🔄 Conectando a Azure PostgreSQL..." -ForegroundColor Cyan

# Método 1: Usando psql (si está instalado)
Write-Host "`n📌 Método 1: Usando psql" -ForegroundColor Yellow
Write-Host "Si tienes psql instalado, ejecuta:" -ForegroundColor Gray
Write-Host "psql ""host=$DB_SERVER port=5432 dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD sslmode=require"" -f clean_exercises_azure.sql" -ForegroundColor Green

# Método 2: Usando Azure CLI con extensión de PostgreSQL
Write-Host "`n📌 Método 2: Usando Azure CLI" -ForegroundColor Yellow
$ResourceGroup = "MetaMindApp"
$ServerName = "motivapp-backend-server"

# Verificar si Azure CLI está instalado
$azInstalled = Get-Command az -ErrorAction SilentlyContinue

if ($azInstalled) {
    Write-Host "✅ Azure CLI detectado" -ForegroundColor Green
    Write-Host "`nEjecutando comandos SQL..." -ForegroundColor Cyan
    
    # Login si es necesario
    Write-Host "Verificando sesión de Azure..." -ForegroundColor Gray
    az account show 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Iniciando sesión en Azure..." -ForegroundColor Yellow
        az login
    }
    
    # Ejecutar comandos SQL
    Write-Host "`n1. Eliminando completaciones de ejercicios antiguos..." -ForegroundColor Cyan
    az postgres flexible-server execute `
        --name $ServerName `
        --resource-group $ResourceGroup `
        --database-name $DB_NAME `
        --admin-user $DB_USER `
        --admin-password $DB_PASSWORD `
        --querytext "DELETE FROM exercise_completions WHERE exercise_id NOT IN (SELECT id FROM wellness_exercises WHERE name IN ('Pasos que Exhalan', 'Anclaje Corazón-Respira', 'Escaneo Amable 60'));"
    
    Write-Host "`n2. Eliminando todos los ejercicios..." -ForegroundColor Cyan
    az postgres flexible-server execute `
        --name $ServerName `
        --resource-group $ResourceGroup `
        --database-name $DB_NAME `
        --admin-user $DB_USER `
        --admin-password $DB_PASSWORD `
        --querytext "DELETE FROM wellness_exercises;"
    
    Write-Host "`n3. Verificando limpieza..." -ForegroundColor Cyan
    az postgres flexible-server execute `
        --name $ServerName `
        --resource-group $ResourceGroup `
        --database-name $DB_NAME `
        --admin-user $DB_USER `
        --admin-password $DB_PASSWORD `
        --querytext "SELECT COUNT(*) as total_exercises FROM wellness_exercises;"
    
    Write-Host "`n✅ Limpieza completada!" -ForegroundColor Green
    Write-Host "Ahora reinicia la aplicación en Azure para cargar los 3 nuevos ejercicios." -ForegroundColor Yellow
    
} else {
    Write-Host "❌ Azure CLI no está instalado" -ForegroundColor Red
    Write-Host "Instálalo desde: https://aka.ms/installazurecliwindows" -ForegroundColor Yellow
}

# Método 3: Usando el Portal de Azure
Write-Host "`n📌 Método 3: Portal de Azure (Manual)" -ForegroundColor Yellow
Write-Host "1. Ve a: https://portal.azure.com" -ForegroundColor Gray
Write-Host "2. Busca tu servidor PostgreSQL: $ServerName" -ForegroundColor Gray
Write-Host "3. En el menú lateral, selecciona 'Query editor' o 'Databases'" -ForegroundColor Gray
Write-Host "4. Copia y pega el contenido de 'clean_exercises_azure.sql'" -ForegroundColor Gray
Write-Host "5. Ejecuta las queries" -ForegroundColor Gray

Write-Host "`n🔄 Después de limpiar, reinicia la app:" -ForegroundColor Cyan
Write-Host "az webapp restart --name motivapp-backend --resource-group $ResourceGroup" -ForegroundColor Green
