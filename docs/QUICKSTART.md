# 🚀 Quick Start: Flou AI Chat System

## Para Desarrolladores: Setup Rápido

### 1️⃣ Variables de Entorno

Crea/actualiza tu `.env` en `motivapp-backend/`:

```env
# Gemini AI
GEMINI_API_KEY=tu_clave_aqui

# Base de datos (Azure PostgreSQL)
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require

# O variables separadas
DB_HOST=your-server.postgres.database.azure.com
DB_NAME=motivapp
DB_USER=admin
DB_PASS=your_password

# JWT
SECRET_KEY=your_secret_key
```

### 2️⃣ Obtener Clave de Gemini

1. Ve a [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Crea una API Key
3. Copia y pega en `.env`

### 3️⃣ Instalación (Local)

```bash
cd motivapp-backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 4️⃣ Migración de Base de Datos

#### Opción A: Alembic (Recomendado)
```bash
alembic revision --autogenerate -m "Add session_states table"
alembic upgrade head
```

#### Opción B: SQL Manual
```bash
psql $DATABASE_URL < create_session_states_table.sql
```

### 5️⃣ Ejecutar Backend

```bash
uvicorn app.main:app --reload
# O con gunicorn (producción)
gunicorn app.main:app -k uvicorn.workers.UvicornWorker
```

### 6️⃣ Testing

#### Endpoint Health Check
```bash
curl http://localhost:8000/
```

#### Test AI Chat
```bash
curl -X POST http://localhost:8000/api/v1/ai-chat/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "Hola"}'
```

## 📱 Frontend (React Native)

### No Requiere Cambios

El frontend actual (`AIChatScreen.tsx`) funciona sin modificaciones:

```typescript
// Ya funciona ✅
const response = await sendChatMessage(userMessage.text);
```

### Testing Local

1. Asegúrate de que el backend esté corriendo
2. Actualiza la URL de API en `src/api/client.ts` si es necesario:
   ```typescript
   const API_URL = 'http://localhost:8000/api/v1';
   // o
   const API_URL = 'https://tu-backend-azure.azurewebsites.net/api/v1';
   ```

3. Ejecuta la app:
   ```bash
   cd motivapp-frontend
   npm start
   ```

## 🐛 Troubleshooting Rápido

### Error: "Module 'google.generativeai' not found"
```bash
pip install google-generativeai==0.8.3
```

### Error: "Table 'session_states' does not exist"
```bash
# Ejecutar migración
psql $DATABASE_URL < create_session_states_table.sql
```

### Error: "GEMINI_API_KEY not configured"
```bash
# Verificar que esté en .env
echo $GEMINI_API_KEY  # Linux/Mac
echo %GEMINI_API_KEY%  # Windows

# O en Python:
python -c "from app.core.config import settings; print(settings.GEMINI_API_KEY)"
```

### Backend no responde en Azure
```bash
# Ver logs
az webapp log tail --name motivapp-api --resource-group YourGroup

# O desde portal Azure:
# App Service → Log stream
```

### Frontend no conecta al backend
```typescript
// Verificar en src/api/client.ts
const API_URL = process.env.EXPO_PUBLIC_API_URL || 'https://tu-backend.azurewebsites.net/api/v1';
```

## 📊 Verificar que Funciona

### Backend

1. **Health Check**: `GET /` debe retornar `{"message": "MotivApp API is running"}`
2. **AI Chat**: `POST /api/v1/ai-chat/send` debe retornar respuesta de Flou
3. **History**: `GET /api/v1/ai-chat/history` debe retornar array de mensajes

### Frontend

1. Abrir pantalla de Chat
2. Enviar "Hola"
3. Flou debe responder: "¿Cómo está tu motivación hoy?..."
4. Enviar un sentimiento → Flou pregunta por la tarea
5. Describir tarea → Flou genera estrategia específica

## 🧪 Tests Manuales

### Test 1: Flujo Normal
```
1. "Hola" → Saludo + pregunta de motivación
2. "Frustración" → Pregunta por tarea
3. "Ensayo de Física, próxima semana, planificación" → Estrategia específica
4. "Sí, funcionó" → Consolida y avanza
```

### Test 2: Crisis
```
1. "No quiero vivir" → Deriva al 4141
```

### Test 3: Datos Incompletos
```
1. "Tengo que estudiar" → Pregunta específica por dato faltante
2. Responder → Continúa flujo
```

### Test 4: Recalibración
```
1. Completar 3 ciclos diciendo "No mejoró"
2. Flou debe ofrecer ejercicio de regulación emocional
```

## 📚 Documentación Completa

- **Backend**: `FLOU_METAMOTIVATION_SYSTEM.md`
- **Frontend**: `CHAT_MIGRATION_GUIDE.md`
- **Resumen**: `MIGRATION_SUMMARY.md`

## 🆘 Soporte

Si encuentras problemas:

1. Revisa los logs del backend
2. Verifica variables de entorno
3. Confirma que la tabla `session_states` existe
4. Revisa la documentación completa
5. Contacta al equipo de desarrollo

## 🎉 ¡Listo!

Si llegaste hasta aquí y todo funciona:
- ✅ Backend con Gemini 2.5 Pro
- ✅ Sistema metamotivacional Flou
- ✅ Persistencia en PostgreSQL
- ✅ Frontend compatible

---

**Happy Coding! 🚀**
