# 🚀 Guía de Despliegue en Azure

## 📋 Resumen de Configuración

El backend de MetaMotivation ha sido configurado para ejecutarse en **Azure App Service** con **Azure Database for PostgreSQL**.

## 🔧 Variables de Entorno Requeridas en Azure

Configura estas variables de entorno en tu Azure App Service:

### Variables de Base de Datos

**Opción 1: URL Completa (Recomendado)**
```
DATABASE_URL=postgresql://[usuario]:[contraseña]@motivapp-db.postgres.database.azure.com:5432/[nombre_db]?sslmode=require
```

**Opción 2: Variables Individuales**
```
DB_HOST=motivapp-db.postgres.database.azure.com
DB_NAME=postgres
DB_USER=administrator_db
DB_PASS=[tu_contraseña_segura]
```

### Variables de Seguridad JWT
```
SECRET_KEY=[tu_clave_secreta_muy_segura]
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Variables de Aplicación
```
PSYCHOLOGIST_INVITE_KEY=[tu_clave_de_invitacion]
```

### Variables Opcionales de Azure
```
SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

## 🗄️ Configuración de Azure PostgreSQL

### Información de tu Base de Datos (según las imágenes)

- **Servidor**: `motivapp-db.postgres.database.azure.com`
- **Endpoint de Conexión**: `motivapp-db.postgres.database.azure.com`
- **Usuario Admin**: `administrator_db`
- **Versión PostgreSQL**: 17.6
- **Ubicación**: Brazil South
- **Estado**: Ready

### ⚠️ Importante: Configuración de Firewall

Asegúrate de que el firewall de Azure PostgreSQL permita conexiones desde:

1. **Azure App Service**: En Azure Portal > PostgreSQL > Networking > Firewall rules
   - Habilita "Allow public access from any Azure service within Azure to this server"
   
2. **Tu IP local** (para desarrollo): Agrega tu IP pública en las reglas del firewall

## 📦 Configuración del Dockerfile

El `Dockerfile` está configurado para:
- Usar Python 3.11-slim
- Exponer el puerto 8000 (estándar de Azure)
- Ejecutar el script `startup.sh` con Gunicorn

## 🚀 Script de Inicio (startup.sh)

El archivo `startup.sh` ejecuta:
```bash
gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind=0.0.0.0:8000 \
    --timeout 600 \
    --log-level info
```

## 🔐 Conexión SSL

La aplicación está configurada para **requerir SSL** al conectarse a Azure PostgreSQL. Esto es obligatorio y ya está configurado en:

- `app/db/session.py`: `sslmode=require` en `connect_args`
- `app/core/config.py`: Agrega `?sslmode=require` automáticamente si usas variables individuales

## 🌐 CORS

El backend acepta peticiones de:
- localhost (para desarrollo)
- Tu dominio de Azure: `motivapp-api-h3eke6d2endmftfb.brazilsouth-01.azurewebsites.net`
- Otros servicios de Azure

**⚠️ En producción**, actualiza `app/main.py` para incluir solo los orígenes específicos de tu frontend.

## 📝 Endpoints Disponibles

- **Root**: `https://[tu-app].azurewebsites.net/`
- **Health Check**: `https://[tu-app].azurewebsites.net/health`
- **API Docs**: `https://[tu-app].azurewebsites.net/api/docs`
- **ReDoc**: `https://[tu-app].azurewebsites.net/api/redoc`
- **API v1**: `https://[tu-app].azurewebsites.net/api/v1/...`

## 🔍 Verificar el Despliegue

1. **Health Check**:
   ```bash
   curl https://motivapp-api-h3eke6d2endmftfb.brazilsouth-01.azurewebsites.net/health
   ```

2. **Ver Logs en Azure**:
   - Azure Portal > App Service > Log stream
   - O usa Azure CLI:
     ```bash
     az webapp log tail --name motivapp-plan --resource-group motivapp-rg
     ```

3. **Probar la API**:
   - Accede a: `https://[tu-app].azurewebsites.net/api/docs`

## 🐛 Troubleshooting

### Error de Conexión a la Base de Datos

1. Verifica que las variables de entorno estén configuradas correctamente en Azure
2. Confirma que el firewall de PostgreSQL permite conexiones desde Azure
3. Revisa los logs de la aplicación: Azure Portal > App Service > Log stream

### La aplicación no inicia

1. Verifica que `startup.sh` tenga permisos de ejecución
2. Revisa los logs de Azure para errores específicos
3. Confirma que todas las variables de entorno requeridas estén presentes

### Errores SSL

- Azure PostgreSQL **requiere** SSL. La configuración ya está incluida.
- Si ves errores relacionados con SSL, verifica que la URL incluya `?sslmode=require`

## 📞 Variables que Necesitas Proporcionar

Para completar la configuración, necesitas:

1. ✅ **SECRET_KEY**: Una clave secreta fuerte para JWT (mínimo 32 caracteres aleatorios)
2. ✅ **PSYCHOLOGIST_INVITE_KEY**: Clave para invitar a psicólogos
3. ✅ **DB_PASS**: La contraseña de tu base de datos Azure PostgreSQL

**Nota**: Las variables `DB_HOST`, `DB_NAME` y `DB_USER` ya están identificadas según tu configuración de Azure.

## 🔄 Próximos Pasos

1. Configura las variables de entorno en Azure Portal
2. Despliega el código actualizado a Azure
3. Verifica que el health check responda correctamente
4. Prueba los endpoints de la API
5. Actualiza el frontend para apuntar a la nueva URL de Azure

## 📚 Recursos Adicionales

- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure Database for PostgreSQL](https://docs.microsoft.com/en-us/azure/postgresql/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
