# 🧠 Flou - AI Metamotivational Tutor

> Sistema de chat inteligente basado en **Google Gemini 2.5 Pro** y el modelo científico de **Miele & Scholer** para acompañamiento metamotivacional de estudiantes.

## 🎯 ¿Qué es Flou?

**Flou** es un tutor de IA empático que ayuda a estudiantes de educación superior a lograr el **"ajuste Tarea–Motivación"** mediante ciclos breves y repetibles de:

```
Monitoreo → Evaluación → Control → Recalibración
```

### Concepto Clave: Task-Motivation Fit

No se trata de "tener más motivación", sino de tener **la motivación correcta para la tarea correcta**.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  AIChatScreen.tsx → sendChatMessage() → API Backend         │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                        BACKEND                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ POST /api/v1/ai-chat/send                           │   │
│  │  1. Guardar mensaje usuario → chat_messages         │   │
│  │  2. Recuperar SessionState → PostgreSQL             │   │
│  │  3. handle_user_turn():                             │   │
│  │     ├─ Detectar crisis → 4141                       │   │
│  │     ├─ Extraer slots con Gemini LLM                 │   │
│  │     ├─ Clasificar Q2/Q3/enfoque                     │   │
│  │     ├─ Validar datos                                │   │
│  │     ├─ Verificar recalibración                      │   │
│  │     └─ Generar estrategia                           │   │
│  │  4. Actualizar SessionState → PostgreSQL            │   │
│  │  5. Guardar respuesta IA → chat_messages            │   │
│  │  6. Retornar { user_message, ai_message, session } │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │   Gemini     │  │   PostgreSQL    │  │   Models     │  │
│  │  2.5 Pro     │  │  - chat_msgs    │  │  - User      │  │
│  │  (LLM)       │  │  - sessions     │  │  - Session   │  │
│  └──────────────┘  └─────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Clasificación Q2/Q3

### Q2: Tipo de Demanda

| Tipo | Descripción | Tareas | Enfoque |
|------|-------------|---------|---------|
| **A** | Creativa/Divergente | Ensayos, brainstorming, presentaciones | 🚀 Promoción (aspiraciones) |
| **B** | Analítica/Convergente | Proofreading, MCQ, código, precisión | 🛡️ Prevención (evitar errores) |

### Q3: Nivel de Abstracción

| Nivel | Descripción | Ideal para |
|-------|-------------|------------|
| **↑** | "Por qué" (abstracto) | Propósito, autocontrol, visión general |
| **↓** | "Cómo" (concreto) | Pasos específicos, ejecución, precisión |
| **mixto** | 2′ de ↑ + bloque de ↓ | Ensayos, proyectos complejos |

## 🔄 Flujo de Conversación

### Turno 1: Saludo Único
```
Flou: ¿Cómo está tu motivación hoy? Puedes elegir:
      Aburrimiento · Frustración · Ansiedad por error · 
      Dispersión · Baja autoeficacia · Otro
```

### Turno 2: Usuario Describe
```
Usuario: "Me siento frustrada. Tengo que hacer un ensayo 
          de Física para la próxima semana. Estoy en planificación."
```

### Turno 3: Flou Analiza y Responde
```
Flou: 
**Ajuste inferido:** A · mixto · promoción→prevención

**Estrategia:**
- 2′ ↑: escribe en 1 línea la pregunta central del ensayo.
- 12′ ↓: bosquejo con 5 bullets (tesis, 2 argumentos, contraargumento, cierre).
- Para la frustración: solo bosquejo (sin redacción fina).

- **Bloque:** 12 min.
- **Mini-evaluación:** ¿Tienes 5 bullets + tesis 1-línea? 
  ¿Cómo cambió la frustración (↓/=/↑)? ¿Hacemos otro bloque o recalibramos?
```

## 🛡️ Detección de Crisis

Si el usuario menciona:
- Suicidio
- Hacerse daño
- No querer vivir

→ **Flou detiene el flujo** y deriva:
```
"Escucho que estás en un momento muy difícil. 
Por favor, llama al 4141 (línea gratuita y confidencial del MINSAL). 
No estás sola/o."
```

## 🔁 Recalibración Inteligente

Tras **3 iteraciones sin mejora**, Flou ajusta:

1. **Cambia Q3** (↑↔↓)
2. **Reduce tarea** (más pequeña)
3. **Acorta bloque** (10-12 min)
4. **Deriva a regulación emocional**:
   - Ansiedad → Respiración 4-4-4 (2′)
   - Frustración → Anclaje 5-4-3-2-1 (3′)
   - Aburrimiento → Micro-relevancia (2′)

## 📦 Stack Tecnológico

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **LLM**: Google Gemini 2.5 Pro (`gemini-2.0-flash-exp`)
- **Database**: Azure PostgreSQL
- **ORM**: SQLAlchemy 2.0
- **Auth**: JWT (python-jose)

### Frontend
- **Framework**: React Native (Expo)
- **Language**: TypeScript
- **Navigation**: React Navigation
- **Styling**: StyleSheet + LinearGradient

## 🗄️ Modelos de Datos

### SessionState
```python
{
  "user_id": 123,
  "greeted": true,
  "iteration": 1,
  "slots": {
    "sentimiento": "frustracion",
    "tipo_tarea": "ensayo",
    "ramo": "Física",
    "plazo": "esta_semana",
    "fase": "planificacion",
    "tiempo_bloque": 12
  },
  "Q2": "A",
  "Q3": "mixto",
  "enfoque": "promocion_eager",
  "last_strategy": "...",
  "last_eval_result": {
    "exito": true,
    "cambio_sentimiento": "↓"
  }
}
```

### ChatMessage
```python
{
  "id": 1,
  "user_id": 123,
  "role": "user",  # o "model"
  "text": "Hola",
  "created_at": "2025-11-11T10:30:00Z"
}
```

## 🚀 Deployment

### Backend (Azure App Service)
```bash
# Configurar variables de entorno
az webapp config appsettings set \
  --name motivapp-api \
  --resource-group YourGroup \
  --settings GEMINI_API_KEY="your_key"

# Deploy
git push azure main
```

### Frontend (Expo)
```bash
# Build para producción
eas build --platform all

# Publish
eas submit
```

## 📚 Documentación

- 📘 [**FLOU_METAMOTIVATION_SYSTEM.md**](FLOU_METAMOTIVATION_SYSTEM.md) - Arquitectura completa
- 📗 [**MIGRATION_SUMMARY.md**](MIGRATION_SUMMARY.md) - Resumen de migración
- 📙 [**QUICKSTART.md**](QUICKSTART.md) - Guía de inicio rápido
- 📕 [**create_session_states_table.sql**](create_session_states_table.sql) - Script de migración

### Frontend
- 📱 [**CHAT_MIGRATION_GUIDE.md**](../motivapp-frontend/CHAT_MIGRATION_GUIDE.md) - Guía para devs frontend

## 🧪 Testing

### Backend
```bash
# Tests unitarios
pytest

# Test manual
curl -X POST http://localhost:8000/api/v1/ai-chat/send \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "Hola"}'
```

### Frontend
```bash
# Ejecutar app
npm start

# Test manual en simulador
# 1. Ir a pantalla Chat
# 2. Enviar "Hola"
# 3. Verificar respuesta de Flou
```

## 📊 Reglas del Sistema

| Regla | Descripción |
|-------|-------------|
| ≤140 palabras | Cada respuesta debe ser concisa |
| 1 estrategia | Una sola estrategia por turno (máx. 3 viñetas) |
| 1 saludo | Solo un saludo por sesión |
| Cierre con pregunta | Siempre terminar con acción o pregunta |
| Español de Chile | Idioma y modismos locales |
| Privacidad | Solo pedir datos necesarios |

## 📈 Métricas y Analítica (Futuro)

- ⬜ Tasa de éxito de estrategias (por Q2/Q3)
- ⬜ Tiempo promedio de recalibración
- ⬜ Sentimientos más frecuentes
- ⬜ Tipos de tarea más desafiantes
- ⬜ Efectividad de ejercicios emocionales

## 🎓 Referencias Científicas

- Miele, D. B., & Scholer, A. A. (2016). *The role of metamotivational monitoring in motivation regulation*. Educational Psychologist.
- Scholer, A. A., & Miele, D. B. (2016). *The role of metamotivation in creating task-motivation fit*. Motivation Science.
- Higgins, E. T. (1997). *Beyond pleasure and pain*. American Psychologist.
- Fujita, K., et al. (2018). *Construal levels and self-control*. JPSP.

## 🤝 Contribuir

1. Fork el proyecto
2. Crea tu branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es propiedad de **MetaMind**. Todos los derechos reservados.

## 👥 Equipo

- **Backend**: Sistema metamotivacional, integración Gemini
- **Frontend**: React Native, UX/UI
- **QA**: Testing, validación científica
- **Research**: Base teórica (Miele & Scholer)

---

**Desarrollado con ❤️ por el equipo MetaMind**  
**Basado en investigación científica de Miele & Scholer (2016)**

🚀 **v1.0.0** - Sistema metamotivacional completo con Gemini 2.5 Pro
