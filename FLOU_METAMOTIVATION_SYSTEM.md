# Sistema de Chat IA: Flou - Tutor Metamotivacional

## 📋 Descripción General

El sistema de chat ha sido completamente migrado desde OpenAI a **Google Gemini 2.5 Pro** (actualmente usando `gemini-2.0-flash-exp`), implementando un tutor metamotivacional basado en el modelo de Miele & Scholer.

**Flou** es un tutor empático que ayuda a estudiantes de educación superior a lograr el "ajuste Tarea–Motivación" (task–motivation fit) mediante ciclos breves y repetibles.

## 🎯 Concepto Clave: Task-Motivation Fit

No se trata de "tener más motivación", sino de tener **la motivación adecuada para la tarea adecuada**. La motivación que te hace brillar en una tarea creativa puede ser perjudicial para una tarea de precisión.

## 🔄 Ciclo Metamotivacional

```
Monitoreo → Evaluación → Control (Estrategia) → Evaluación de Implementación
```

1. **Monitoreo**: Identificar el estado motivacional actual (usando "sentimientos metamotivacionales")
2. **Evaluación**: Definir la demanda de la tarea
3. **Control**: Sugerir estrategia específica
4. **Recalibración**: Ajustar según resultados

## 🏗️ Arquitectura del Sistema

### Modelos de Datos

#### 1. `SessionState` (PostgreSQL)
Persiste el estado de la sesión metamotivacional por usuario:
- `greeted`: Flag de saludo único
- `iteration`: Contador de ciclos (0-3)
- `slots`: JSON con sentimiento, tipo_tarea, ramo, plazo, fase, tiempo_bloque
- `Q2`, `Q3`, `enfoque`: Clasificaciones inferidas
- `last_strategy`, `last_eval_result`: Historial de estrategias

#### 2. `ChatMessage` (PostgreSQL)
Almacena el historial de conversación:
- `role`: 'user' o 'model'
- `text`: Contenido del mensaje
- `created_at`: Timestamp

### Schemas Pydantic

#### Tipos Enumerados
```python
Sentimiento = Literal["aburrimiento", "frustracion", "ansiedad_error", 
                      "dispersion_rumiacion", "baja_autoeficacia", "otro"]

TipoTarea = Literal["ensayo", "esquema", "borrador", "lectura_tecnica", 
                    "resumen", "resolver_problemas", "protocolo_lab", 
                    "mcq", "presentacion", "coding_bugfix", "proofreading"]

Fase = Literal["ideacion", "planificacion", "ejecucion", "revision"]

Plazo = Literal["hoy", "<24h", "esta_semana", ">1_semana"]
```

#### `Slots`
Información extraída del texto libre del usuario:
- sentimiento
- tipo_tarea
- ramo
- plazo
- fase
- tiempo_bloque (10, 12, 15, 25 minutos)

## 🤖 Servicio de IA (`ai_service.py`)

### Funciones Principales

#### 1. `handle_user_turn(session, user_text, context)`
Orquestador principal del flujo metamotivacional:
- Detecta crisis (derivación al 4141)
- Extrae slots del texto libre
- Infiere Q2/Q3 y enfoque regulatorio
- Genera estrategia personalizada
- Maneja recalibración

#### 2. `extract_slots_with_llm(free_text, current_slots)`
Usa Gemini 2.5 Pro para extracción estructurada de slots:
- Temperatura: 0.2 (precisión)
- Max tokens: 500
- Fallback a heurística si falla

#### 3. `infer_q2_q3(slots)`
Clasifica la tarea según dos dimensiones:

**Q2 (Tipo de Demanda)**:
- **A (Creativa/Divergente)**: ensayo, brainstorming, planificación
- **B (Analítica/Convergente)**: proofreading, MCQ, precisión

**Q3 (Nivel de Abstracción)**:
- **↑ (Por qué)**: ideación, propósito, autocontrol
- **↓ (Cómo)**: ejecución, detalles, precisión
- **mixto**: 2′ de ↑ + bloque principal en ↓

**Enfoque Regulatorio**:
- Q2=A → promoción/eager (aspiraciones)
- Q2=B → prevención/vigilant (deberes, evitar errores)

#### 4. `render_estrategia(slots, Q2, Q3)`
Genera viñetas de estrategia específicas según clasificación:
- Máximo 3 viñetas
- Una sub-tarea verificable
- Técnicas concretas (timers, checklists, etc.)

#### 5. `emotional_fallback(sentimiento)`
Derivación a regulación emocional tras 3 iteraciones sin progreso:
- **Ansiedad**: Respiración 4-4-4
- **Frustración/Rumiación**: Anclaje 5-4-3-2-1
- **Aburrimiento**: Micro-relevancia + activación conductual

### Detección de Crisis

Palabras clave: suicidio, quitarme la vida, hacerme daño, matarme
→ Detiene el flujo y deriva al **4141** (línea gratuita MINSAL Chile)

### Reglas Duras

1. ✅ Español de Chile
2. ✅ ≤140 palabras por turno
3. ✅ Una sola estrategia por turno
4. ✅ Cierre con pregunta o acción
5. ✅ Saludo único por sesión
6. ✅ Privacidad (solo datos necesarios)

## 📡 API Endpoints

### POST `/api/v1/ai-chat/send`
Envía mensaje y obtiene respuesta:
```json
Request:
{
  "message": "Me siento frustrada. Ensayo para Física, próxima semana."
}

Response:
{
  "user_message": { "id": 1, "role": "user", "text": "...", ... },
  "ai_message": { "id": 2, "role": "model", "text": "...", ... },
  "session_state": { "Q2": "A", "Q3": "mixto", ... }
}
```

**Flujo interno**:
1. Guardar mensaje del usuario en BD
2. Recuperar `SessionState` de PostgreSQL
3. Llamar `handle_user_turn()` con contexto del usuario
4. Actualizar `SessionState` en BD
5. Guardar respuesta de la IA en BD
6. Retornar ambos mensajes

### GET `/api/v1/ai-chat/history`
Obtiene historial completo de mensajes del usuario.

### DELETE `/api/v1/ai-chat/history`
Elimina historial y **reinicia la sesión metamotivacional**.

## 🔐 Configuración

### Variables de Entorno
```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://...
```

### Modelo Actual
```python
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')
```

**Nota**: Para usar Gemini 2.5 Pro, cambiar a `'gemini-2.5-pro'` cuando esté disponible.

## 🗄️ Migraciones de Base de Datos

Después de implementar estos cambios, ejecutar:

```bash
# En producción (Azure)
# La migración se ejecutará automáticamente al desplegar

# En desarrollo local
alembic revision --autogenerate -m "Add session_state table for metamotivational tutor"
alembic upgrade head
```

O crear manualmente la tabla:

```sql
CREATE TABLE session_states (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    greeted BOOLEAN NOT NULL DEFAULT FALSE,
    iteration INTEGER NOT NULL DEFAULT 0,
    sentimiento_inicial VARCHAR,
    sentimiento_actual VARCHAR,
    slots JSONB DEFAULT '{}',
    "Q2" VARCHAR,
    "Q3" VARCHAR,
    enfoque VARCHAR,
    tiempo_bloque INTEGER,
    last_strategy TEXT,
    last_eval_result JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_session_states_user_id ON session_states(user_id);
```

## 🎨 Ejemplo de Conversación

### Turno 1 (Sistema)
```
¿Cómo está tu motivación hoy? Puedes elegir un sentimiento:
Aburrimiento · Frustración · Ansiedad por error · Dispersión · Baja autoeficacia · Otro
```

### Turno 2 (Usuario)
```
"Me siento frustrada. Tengo que hacer un ensayo para Física para la próxima semana 
y estoy en la etapa de planificación."
```

### Turno 3 (Flou)
```
**Ajuste inferido:** A · mixto · promoción→prevención

**Estrategia:**
- 2′ ↑: escribe en 1 línea la pregunta central del ensayo.
- 12′ ↓: bosquejo con 5 bullets (tesis, 2 argumentos, contraargumento, cierre).
- Para la frustración: solo bosquejo (sin redactar fino).

- **Bloque:** 12 min.
- **Mini-evaluación:** ¿Tienes 5 bullets + tesis 1-línea? 
  ¿Cómo cambió la frustración (↓/=/↑)? ¿Hacemos un segundo bloque o recalibramos?
```

## 🔄 Flujo de Recalibración

Si tras **3 iteraciones** no hay progreso:

1. Cambiar Q3 (↑↔↓)
2. Reducir tamaño de tarea
3. Acortar tiempo_bloque (10-12 min)
4. Si persiste: derivar a ejercicio de regulación emocional

Tras ejercicio:
- Reset `iteration = 0`
- Reintentar con sub-tarea mínima

## 📚 Referencias Teóricas

- Miele, D. B., & Scholer, A. A. (2016). *The role of metamotivational monitoring in motivation regulation*
- Scholer, A. A., & Miele, D. B. (2016). *The role of metamotivation in creating task-motivation fit*
- Fujita, K., et al. (2018). *Construal levels and self-control*

## 🚀 Próximos Pasos

1. ✅ Migrar a Gemini 2.5 Pro cuando esté disponible en producción
2. ⬜ Implementar chips en UI para edición de etiquetas inferidas
3. ⬜ Agregar botón "Iniciar bloque" con temporizador
4. ⬜ Formulario de mini-evaluación visual al cerrar bloque
5. ⬜ Analíticas de efectividad de estrategias

## 🛠️ Troubleshooting

### Error: "Slot extraction failed"
- Fallback automático a heurística regex
- Verificar formato de respuesta de Gemini

### Error: "Session state not found"
- Se crea automáticamente con `get_or_create_session()`
- Verificar foreign key a `users.id`

### Respuestas muy largas
- Sistema limita a 140 palabras con `limit_words()`
- Ajustar en `render_tutor_turn()` si es necesario

## 📄 Archivos Modificados

```
motivapp-backend/
├── app/
│   ├── models/
│   │   ├── session_state.py          # NUEVO
│   │   ├── user.py                    # MODIFICADO (relación)
│   │   └── __init__.py                # MODIFICADO (import)
│   ├── schemas/
│   │   └── chat.py                    # MODIFICADO (nuevos schemas)
│   ├── crud/
│   │   └── crud_session.py            # NUEVO
│   ├── services/
│   │   └── ai_service.py              # REESCRITO COMPLETAMENTE
│   └── api/v1/endpoints/
│       └── ai_chat.py                 # MODIFICADO (usa SessionState)
└── FLOU_METAMOTIVATION_SYSTEM.md      # NUEVO (este archivo)
```

---

**Desarrollado con ❤️ por el equipo de MetaMind**  
**Basado en investigación científica de Miele & Scholer**
