# 🔐 Variables de Entorno para Azure App Service

## Cómo Configurar las Variables en Azure Portal

### Método 1: Azure Portal (Interfaz Web)

1. Ve a [Azure Portal](https://portal.azure.com)
2. Navega a tu App Service: **motivapp-plan** (F1: 1)
3. En el menú lateral, selecciona **Configuration** (Configuración)
4. En la pestaña **Application settings**, haz clic en **+ New application setting**
5. Agrega cada variable de la lista a continuación

### Método 2: Azure CLI

```bash
# Login a Azure
az login

# Establecer las variables (reemplaza los valores con los tuyos)
az webapp config appsettings set --name motivapp-plan --resource-group motivapp-rg --settings \
  DATABASE_URL="postgresql://administrator_db:TU_CONTRASEÑA@motivapp-db.postgres.database.azure.com:5432/postgres?sslmode=require" \
  SECRET_KEY="TU_SECRET_KEY_MUY_SEGURA" \
  ALGORITHM="HS256" \
  ACCESS_TOKEN_EXPIRE_MINUTES="30" \
  PSYCHOLOGIST_INVITE_KEY="TU_CLAVE_DE_INVITACION"
```

---

## 📝 Lista de Variables a Configurar

### 1. DATABASE_URL (REQUERIDO)
**Nombre**: `DATABASE_URL`  
**Valor de ejemplo**:
```
postgresql://administrator_db:TU_CONTRASEÑA_AQUI@motivapp-db.postgres.database.azure.com:5432/postgres?sslmode=require
```

**⚠️ Importante**: Reemplaza `TU_CONTRASEÑA_AQUI` con la contraseña real de tu base de datos Azure PostgreSQL.

---

### 2. SECRET_KEY (REQUERIDO)
**Nombre**: `SECRET_KEY`  
**Descripción**: Clave secreta para firmar tokens JWT  
**Valor**: Una cadena aleatoria de al menos 32 caracteres

**Generar una SECRET_KEY segura** (ejecuta en tu terminal):

**Windows PowerShell**:
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

**Python**:
```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Linux/Mac**:
```bash
openssl rand -hex 32
```

**Ejemplo de valor**: `8f42a73054b1749e5b2f1d7c9e4a2b6d3f5e7a9c1d3e5f7a9b1c3d5e7f9a1b3c`

---

### 3. ALGORITHM (REQUERIDO)
**Nombre**: `ALGORITHM`  
**Valor**: `HS256`

---

### 4. ACCESS_TOKEN_EXPIRE_MINUTES (REQUERIDO)
**Nombre**: `ACCESS_TOKEN_EXPIRE_MINUTES`  
**Valor**: `30`  
**Descripción**: Tiempo de expiración del token en minutos

---

### 5. PSYCHOLOGIST_INVITE_KEY (REQUERIDO)
**Nombre**: `PSYCHOLOGIST_INVITE_KEY`  
**Descripción**: Clave que los psicólogos deben usar para registrarse  
**Valor**: Una clave que tú definas (puede ser cualquier string)

**Ejemplo**: `InvitePsycho2025!`

---

## 🔍 Verificar las Variables

### En Azure Portal:
1. Ve a **Configuration** en tu App Service
2. Verifica que todas las 5 variables estén listadas
3. Asegúrate de que no haya espacios extra o caracteres invisibles

### Desde tu aplicación:
Una vez desplegada, puedes verificar que las variables se estén leyendo correctamente revisando los logs.

---

## ✅ Checklist de Configuración

- [ ] `DATABASE_URL` configurada con la contraseña correcta
- [ ] `SECRET_KEY` generada de forma segura y configurada
- [ ] `ALGORITHM` establecido como `HS256`
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` establecido como `30`
- [ ] `PSYCHOLOGIST_INVITE_KEY` configurada con tu clave personalizada
- [ ] Verificado que el firewall de PostgreSQL permite conexiones desde Azure
- [ ] Reiniciado el App Service después de configurar las variables

---

## 🔄 Reiniciar el App Service

Después de configurar las variables, **debes reiniciar** el App Service:

### Azure Portal:
1. Ve a tu App Service
2. Haz clic en **Restart** en la barra superior

### Azure CLI:
```bash
az webapp restart --name motivapp-plan --resource-group motivapp-rg
```

---

## 🚨 Seguridad

**⚠️ NUNCA**:
- Subas estas variables a Git
- Compartas tu `SECRET_KEY` o `DATABASE_URL` públicamente
- Uses contraseñas débiles o predecibles

**✅ SIEMPRE**:
- Usa secretos generados aleatoriamente
- Mantén las credenciales en Azure Key Vault para producción
- Rota las claves periódicamente

---

## 📞 ¿Necesitas Ayuda?

Si encuentras algún error al configurar las variables:

1. Verifica que no haya espacios al inicio o final de las variables
2. Confirma que la contraseña de la base de datos sea correcta
3. Revisa los logs del App Service para mensajes de error específicos
4. Asegúrate de haber reiniciado el App Service después de los cambios
