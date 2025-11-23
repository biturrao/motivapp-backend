# Database Migrations

Este directorio contiene los scripts de migración SQL para aplicar cambios en la base de datos de producción.

## Cómo aplicar migraciones en Azure

### Opción 1: Desde Azure Portal

1. Ve a Azure Portal → Tu PostgreSQL Database
2. Ve a "Query editor" o "pgAdmin"
3. Conéctate con las credenciales de admin
4. Ejecuta el script SQL correspondiente

### Opción 2: Desde CLI local

```bash
# Conectarse a la base de datos de Azure
psql -h <your-server>.postgres.database.azure.com -U <username> -d <database-name>

# Ejecutar la migración
\i migrations/001_add_summary_column.sql
```

### Opción 3: Usar Azure CLI

```bash
az postgres flexible-server execute \
  --name <server-name> \
  --database-name <database-name> \
  --admin-user <username> \
  --admin-password <password> \
  --file-path migrations/001_add_summary_column.sql
```

## Migraciones disponibles

- `001_add_summary_column.sql` - Añade columna `summary` a `user_profiles` para cachear resúmenes de IA

## Rollback

Si necesitas revertir una migración, ejecuta:

```sql
-- Rollback 001_add_summary_column.sql
ALTER TABLE user_profiles DROP COLUMN IF EXISTS summary;
```
