# 🛠️ Comandos Útiles para Azure CLI

## 🔐 Autenticación

```bash
# Login a Azure
az login

# Ver tu suscripción actual
az account show

# Listar todas tus suscripciones
az account list --output table

# Cambiar de suscripción (si tienes múltiples)
az account set --subscription "Azure for Students"
```

---

## 📊 Información del App Service

```bash
# Ver detalles del App Service
az webapp show --name motivapp-plan --resource-group motivapp-rg

# Ver el estado
az webapp show --name motivapp-plan --resource-group motivapp-rg --query state

# Ver la URL del sitio
az webapp show --name motivapp-plan --resource-group motivapp-rg --query defaultHostName

# Listar todas las web apps en el resource group
az webapp list --resource-group motivapp-rg --output table
```

---

## 🔧 Configuración de Variables de Entorno

```bash
# Ver todas las variables de entorno configuradas
az webapp config appsettings list --name motivapp-plan --resource-group motivapp-rg --output table

# Agregar/Actualizar una variable
az webapp config appsettings set --name motivapp-plan --resource-group motivapp-rg \
  --settings MI_VARIABLE="mi_valor"

# Agregar múltiples variables a la vez
az webapp config appsettings set --name motivapp-plan --resource-group motivapp-rg \
  --settings \
    DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require" \
    SECRET_KEY="tu-secret-key" \
    ALGORITHM="HS256"

# Eliminar una variable
az webapp config appsettings delete --name motivapp-plan --resource-group motivapp-rg \
  --setting-names MI_VARIABLE
```

---

## 📝 Logs y Monitoreo

```bash
# Ver logs en tiempo real (stream)
az webapp log tail --name motivapp-plan --resource-group motivapp-rg

# Descargar logs
az webapp log download --name motivapp-plan --resource-group motivapp-rg --log-file logs.zip

# Habilitar logging
az webapp log config --name motivapp-plan --resource-group motivapp-rg \
  --application-logging filesystem \
  --detailed-error-messages true \
  --failed-request-tracing true \
  --web-server-logging filesystem

# Ver métricas
az monitor metrics list --resource /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/motivapp-rg/providers/Microsoft.Web/sites/motivapp-plan
```

---

## 🚀 Despliegue y Control

```bash
# Reiniciar la aplicación
az webapp restart --name motivapp-plan --resource-group motivapp-rg

# Detener la aplicación
az webapp stop --name motivapp-plan --resource-group motivapp-rg

# Iniciar la aplicación
az webapp start --name motivapp-plan --resource-group motivapp-rg

# Desplegar desde un repositorio local
az webapp up --name motivapp-plan --resource-group motivapp-rg

# Ver el historial de despliegues
az webapp deployment list-publishing-profiles --name motivapp-plan --resource-group motivapp-rg
```

---

## 🗄️ Base de Datos PostgreSQL

```bash
# Ver información del servidor PostgreSQL
az postgres flexible-server show --name motivapp-db --resource-group motivapp-rg

# Ver el estado del servidor
az postgres flexible-server show --name motivapp-db --resource-group motivapp-rg --query state

# Listar bases de datos en el servidor
az postgres flexible-server db list --server-name motivapp-db --resource-group motivapp-rg --output table

# Reiniciar el servidor PostgreSQL (¡Cuidado! Causará downtime)
az postgres flexible-server restart --name motivapp-db --resource-group motivapp-rg

# Ver reglas de firewall
az postgres flexible-server firewall-rule list --name motivapp-db --resource-group motivapp-rg --output table

# Agregar una regla de firewall (para tu IP local)
az postgres flexible-server firewall-rule create \
  --resource-group motivapp-rg \
  --name motivapp-db \
  --rule-name AllowMyIP \
  --start-ip-address TU.IP.PUBLICA \
  --end-ip-address TU.IP.PUBLICA

# Permitir todos los servicios de Azure
az postgres flexible-server firewall-rule create \
  --resource-group motivapp-rg \
  --name motivapp-db \
  --rule-name AllowAllAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

---

## 🔍 Diagnóstico y Troubleshooting

```bash
# Ejecutar un comando en el contenedor
az webapp ssh --name motivapp-plan --resource-group motivapp-rg

# Ver el archivo de configuración
az webapp config show --name motivapp-plan --resource-group motivapp-rg

# Ver información de escalado
az appservice plan show --name ASP-motivapprg-a74a --resource-group motivapp-rg

# Verificar salud de la app
curl https://motivapp-api-h3eke6d2endmftfb.brazilsouth-01.azurewebsites.net/health

# Test de conexión rápido
curl -I https://motivapp-api-h3eke6d2endmftfb.brazilsouth-01.azurewebsites.net/
```

---

## 🎯 Comandos Específicos para Tu Configuración

```bash
# Configurar TODAS las variables de entorno necesarias
az webapp config appsettings set \
  --name motivapp-plan \
  --resource-group motivapp-rg \
  --settings \
    DATABASE_URL="postgresql://administrator_db:TU_CONTRASEÑA@motivapp-db.postgres.database.azure.com:5432/postgres?sslmode=require" \
    SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" \
    ALGORITHM="HS256" \
    ACCESS_TOKEN_EXPIRE_MINUTES="30" \
    PSYCHOLOGIST_INVITE_KEY="TU_CLAVE_AQUI"

# Reiniciar después de configurar
az webapp restart --name motivapp-plan --resource-group motivapp-rg

# Ver logs en tiempo real para verificar
az webapp log tail --name motivapp-plan --resource-group motivapp-rg

# Test completo de la API
echo "Testing health endpoint..."
curl https://motivapp-api-h3eke6d2endmftfb.brazilsouth-01.azurewebsites.net/health
echo ""
echo "Testing root endpoint..."
curl https://motivapp-api-h3eke6d2endmftfb.brazilsouth-01.azurewebsites.net/
```

---

## 📦 Backup y Restore

```bash
# Crear un backup de la base de datos
az postgres flexible-server backup list --name motivapp-db --resource-group motivapp-rg

# Crear un snapshot de la configuración
az webapp config appsettings list --name motivapp-plan --resource-group motivapp-rg > config_backup.json
```

---

## 🔐 Seguridad

```bash
# Habilitar HTTPS only
az webapp update --name motivapp-plan --resource-group motivapp-rg --https-only true

# Ver configuración de SSL
az webapp config ssl list --resource-group motivapp-rg

# Ver identidad administrada (si la usas)
az webapp identity show --name motivapp-plan --resource-group motivapp-rg
```

---

## 💰 Costos y Recursos

```bash
# Ver el plan de App Service
az appservice plan show --name ASP-motivapprg-a74a --resource-group motivapp-rg --output table

# Ver SKU actual
az appservice plan show --name ASP-motivapprg-a74a --resource-group motivapp-rg --query sku

# Ver todos los recursos en el grupo
az resource list --resource-group motivapp-rg --output table
```

---

## 🔄 Scripts Útiles (PowerShell)

### Script para verificar todo rápidamente:

```powershell
# check-azure-status.ps1
Write-Host "🔍 Verificando estado de Motivapp en Azure..." -ForegroundColor Cyan

Write-Host "`n📊 Estado del App Service:" -ForegroundColor Yellow
az webapp show --name motivapp-plan --resource-group motivapp-rg --query "{State:state, URL:defaultHostName}" -o table

Write-Host "`n🗄️ Estado de PostgreSQL:" -ForegroundColor Yellow
az postgres flexible-server show --name motivapp-db --resource-group motivapp-rg --query "{State:state, Version:version, Location:location}" -o table

Write-Host "`n🌐 Testing health endpoint..." -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "https://motivapp-api-h3eke6d2endmftfb.brazilsouth-01.azurewebsites.net/health" -UseBasicParsing
Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
Write-Host "Response: $($response.Content)" -ForegroundColor Green

Write-Host "`n✅ Verificación completada!" -ForegroundColor Green
```

### Script para desplegar y verificar:

```powershell
# deploy-and-verify.ps1
Write-Host "🚀 Iniciando despliegue..." -ForegroundColor Cyan

# Reiniciar la app
Write-Host "`n🔄 Reiniciando App Service..." -ForegroundColor Yellow
az webapp restart --name motivapp-plan --resource-group motivapp-rg

# Esperar un poco
Start-Sleep -Seconds 10

# Verificar
Write-Host "`n✅ Verificando despliegue..." -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "https://motivapp-api-h3eke6d2endmftfb.brazilsouth-01.azurewebsites.net/health" -UseBasicParsing
if ($response.StatusCode -eq 200) {
    Write-Host "✅ Despliegue exitoso!" -ForegroundColor Green
} else {
    Write-Host "❌ Posible problema en el despliegue" -ForegroundColor Red
}
```

---

## 📚 Recursos Adicionales

- **Azure CLI Reference**: https://docs.microsoft.com/en-us/cli/azure/
- **App Service CLI**: https://docs.microsoft.com/en-us/cli/azure/webapp
- **PostgreSQL CLI**: https://docs.microsoft.com/en-us/cli/azure/postgres

---

## 💡 Tips Rápidos

```bash
# Alias útiles para tu perfil de PowerShell (~\Documents\PowerShell\Profile.ps1)
function motivapp-logs { az webapp log tail --name motivapp-plan --resource-group motivapp-rg }
function motivapp-restart { az webapp restart --name motivapp-plan --resource-group motivapp-rg }
function motivapp-status { az webapp show --name motivapp-plan --resource-group motivapp-rg --query state }
function motivapp-health { curl https://motivapp-api-h3eke6d2endmftfb.brazilsouth-01.azurewebsites.net/health }
```

Después de agregar estos alias, recarga tu perfil:
```powershell
. $PROFILE
```

Y podrás usar:
```powershell
motivapp-logs      # Ver logs en tiempo real
motivapp-restart   # Reiniciar la app
motivapp-status    # Ver el estado
motivapp-health    # Probar el health check
```
