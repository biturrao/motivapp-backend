# 🧹 Limpieza de Ejercicios Antiguos en Azure

## Problema
Hay ejercicios antiguos (12) guardados en la base de datos de Azure que necesitan ser eliminados para que solo aparezcan los 3 nuevos ejercicios:
1. **Pasos que Exhalan** (ROJO)
2. **Anclaje Corazón-Respira** (AMBAR)
3. **Escaneo Amable 60** (VERDE)

## Soluciones Disponibles

### 🎯 Opción 1: Usando Python Script (RECOMENDADO)

```powershell
# 1. Instalar psycopg2 si no lo tienes
pip install psycopg2-binary

# 2. Configurar password de Azure
$env:DB_PASSWORD="TU_PASSWORD_AZURE_AQUI"

# 3. Ejecutar script
python clean_exercises_azure.py

# 4. Reiniciar app en Azure
az webapp restart --name motivapp-backend --resource-group MetaMindApp
```

### 🎯 Opción 2: Usando Portal de Azure

1. Ve a https://portal.azure.com
2. Busca tu servidor PostgreSQL: `motivapp-backend-server`
3. En el menú lateral, selecciona **"Databases"** > `motivapp-backend-database`
4. Haz clic en **"Query editor"** o **"Connect"**
5. Copia y pega el contenido de `clean_exercises_azure.sql`
6. Ejecuta las queries en este orden:
   ```sql
   -- 1. Limpiar completaciones
   DELETE FROM exercise_completions;
   
   -- 2. Limpiar ejercicios
   DELETE FROM wellness_exercises;
   
   -- 3. Verificar
   SELECT COUNT(*) FROM wellness_exercises;
   ```
7. Ve a **App Services** > `motivapp-backend` > **Restart**

### 🎯 Opción 3: Usando Azure CLI

```powershell
# Ejecutar el script PowerShell
.\clean_exercises_azure.ps1

# O manualmente:
az postgres flexible-server execute `
    --name motivapp-backend-server `
    --resource-group MetaMindApp `
    --database-name motivapp-backend-database `
    --admin-user motivappadmin `
    --admin-password "TU_PASSWORD" `
    --querytext "DELETE FROM exercise_completions; DELETE FROM wellness_exercises;"

# Reiniciar app
az webapp restart --name motivapp-backend --resource-group MetaMindApp
```

## ✅ Verificación

Después de limpiar y reiniciar la app, verifica que funcione:

```powershell
# Hacer una petición a la API
curl https://motivapp-backend.azurewebsites.net/api/v1/wellness/exercises

# Deberías ver solo 3 ejercicios en la respuesta
```

## 📝 Notas Importantes

- ⚠️ **Eliminar ejercicios también elimina las estadísticas de completación**
- 🔄 **Después de limpiar, DEBES reiniciar la app** para que `seed_wellness_exercises()` cargue los 3 nuevos
- 🎯 Los 3 ejercicios se cargarán automáticamente al iniciar la app (si la tabla está vacía)
- 📊 La nueva racha se calculará basada en el módulo de Bienestar, no en el Path

## 🐛 Troubleshooting

### Error: "Method Not Allowed"
- **Causa**: El endpoint `/wellness/exercises/complete` no existe o no se desplegó
- **Solución**: Asegúrate de hacer `git push` y que Azure haya actualizado el código

### Error: No se cargan los 3 ejercicios
- **Causa**: La función `seed_wellness_exercises()` no se ejecutó
- **Solución**: Verifica los logs de Azure, debe mostrar "Sembraron 3 ejercicios de bienestar exitosamente"

### Error de conexión a PostgreSQL
- **Causa**: Credenciales incorrectas o IP bloqueada
- **Solución**: Verifica que tu IP esté en la lista de IPs permitidas en Azure Portal

## 📚 Archivos Creados

- `clean_exercises.py` - Script local para testing
- `clean_exercises_azure.py` - Script para conectar directamente a Azure
- `clean_exercises_azure.sql` - Queries SQL directas
- `clean_exercises_azure.ps1` - Script PowerShell con Azure CLI
- `AZURE_EXERCISES_CLEANUP.md` - Este archivo

## 🔗 Links Útiles

- [Azure Portal](https://portal.azure.com)
- [Azure CLI Docs](https://docs.microsoft.com/en-us/cli/azure/)
- [PostgreSQL Flexible Server Docs](https://docs.microsoft.com/en-us/azure/postgresql/flexible-server/)
