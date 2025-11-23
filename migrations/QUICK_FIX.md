# SOLUCIÓN RÁPIDA: Añadir columna summary

## ❌ Error
```
psycopg2.errors.UndefinedColumn: column user_profiles.summary does not exist
```

## ✅ Solución Rápida (Azure Portal)

### Opción 1: Query Editor en Azure Portal (MÁS FÁCIL)

1. **Ve a Azure Portal** (https://portal.azure.com)
2. **Busca tu PostgreSQL Database**
3. **Click en "Query editor"** en el menú lateral
4. **Inicia sesión** con tus credenciales de admin
5. **Copia y pega este SQL:**

```sql
ALTER TABLE user_profiles ADD COLUMN summary TEXT NULL;
```

6. **Click en "Run"**
7. **¡Listo!** Ya puedes hacer deploy de la aplicación

### Opción 2: PowerShell (si tienes psql instalado)

```powershell
cd motivapp-backend
.\apply-migration.ps1
```

### Opción 3: Azure CLI

```bash
az postgres flexible-server execute \
  --name <tu-server-name> \
  --database-name <tu-database-name> \
  --admin-user <tu-username> \
  --admin-password <tu-password> \
  --querytext "ALTER TABLE user_profiles ADD COLUMN summary TEXT NULL;"
```

## 📝 ¿Qué hace este cambio?

- **Añade una columna `summary`** a la tabla `user_profiles`
- **Permite cachear** el resumen generado por IA
- **Ahorra tokens** al no regenerar el resumen cada vez que el usuario visita su perfil
- El resumen **se regenera automáticamente** cuando el usuario actualiza su perfil

## 🔄 Después de aplicar la migración

1. Espera unos segundos
2. Haz deploy de tu aplicación normalmente
3. El error debería desaparecer

## ⏪ Rollback (si necesitas revertir)

```sql
ALTER TABLE user_profiles DROP COLUMN IF EXISTS summary;
```
