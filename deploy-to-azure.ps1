# Script para desplegar a Azure con las correcciones
# Ejecuta este script desde PowerShell en el directorio motivapp-backend

Write-Host "🚀 Iniciando despliegue corregido a Azure..." -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
$currentDir = Split-Path -Leaf (Get-Location)
if ($currentDir -ne "motivapp-backend") {
    Write-Host "⚠️ ADVERTENCIA: No estás en el directorio motivapp-backend" -ForegroundColor Yellow
    Write-Host "Cambiando al directorio correcto..." -ForegroundColor Yellow
    Set-Location "C:\Users\srdip\MetaMind\motivapp-backend"
}

Write-Host "📁 Directorio actual: $(Get-Location)" -ForegroundColor Green
Write-Host ""

# Paso 1: Agregar archivos al staging
Write-Host "📝 Paso 1: Agregando archivos al staging de Git..." -ForegroundColor Yellow
git add .deployment
git add web.config
git add .zipignore
git add requirements.txt
git add AZURE_DEPLOYMENT_FIX.md
git add -A

# Paso 2: Ver los cambios
Write-Host ""
Write-Host "📋 Archivos modificados:" -ForegroundColor Yellow
git status --short

# Paso 3: Confirmar con el usuario
Write-Host ""
$confirm = Read-Host "¿Deseas continuar con el commit y push? (S/N)"

if ($confirm -eq "S" -or $confirm -eq "s") {
    # Paso 4: Commit
    Write-Host ""
    Write-Host "💾 Paso 2: Haciendo commit..." -ForegroundColor Yellow
    git commit -m "Fix Azure deployment: disable compression for F1 plan memory limits"
    
    # Paso 5: Push
    Write-Host ""
    Write-Host "📤 Paso 3: Pushing a origin main..." -ForegroundColor Yellow
    git push origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ ¡Despliegue iniciado exitosamente!" -ForegroundColor Green
        Write-Host ""
        Write-Host "🔍 Ahora puedes monitorear el despliegue en:" -ForegroundColor Cyan
        Write-Host "   - Azure Portal: https://portal.azure.com" -ForegroundColor White
        Write-Host "   - Deployment Center en tu App Service" -ForegroundColor White
        Write-Host ""
        
        $viewLogs = Read-Host "¿Deseas ver los logs en tiempo real? (S/N)"
        if ($viewLogs -eq "S" -or $viewLogs -eq "s") {
            Write-Host ""
            Write-Host "📊 Abriendo logs en tiempo real... (Presiona Ctrl+C para salir)" -ForegroundColor Yellow
            Start-Sleep -Seconds 2
            az webapp log tail --name motivapp-plan --resource-group motivapp-rg
        }
        else {
            Write-Host ""
            Write-Host "💡 Para ver los logs más tarde, ejecuta:" -ForegroundColor Cyan
            Write-Host "   az webapp log tail --name motivapp-plan --resource-group motivapp-rg" -ForegroundColor White
            Write-Host ""
            Write-Host "🌐 Para verificar que funciona, prueba:" -ForegroundColor Cyan
            Write-Host "   https://motivapp-api-h3eke6d2endmftfb.brazilsouth-01.azurewebsites.net/health" -ForegroundColor White
        }
    }
    else {
        Write-Host ""
        Write-Host "❌ Error durante el push" -ForegroundColor Red
        Write-Host "Revisa los mensajes de error arriba" -ForegroundColor Yellow
    }
}
else {
    Write-Host ""
    Write-Host "❌ Despliegue cancelado por el usuario" -ForegroundColor Yellow
    Write-Host "Los archivos están en staging. Para revertir:" -ForegroundColor Cyan
    Write-Host "   git reset HEAD" -ForegroundColor White
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Gray
