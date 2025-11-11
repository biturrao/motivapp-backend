# API de Wellness (Bienestar) - Documentación

## Resumen
El módulo de Wellness permite a los usuarios gestionar su estado de energía metamotivacional (semáforo verde/ámbar/rojo), recibir recomendaciones de ejercicios de mindfulness y embodied cognition, y llevar un registro de su práctica.

## Base URL
```
/api/v1/wellness
```

## Autenticación
Todos los endpoints requieren autenticación JWT. Incluir en headers:
```
Authorization: Bearer {token}
```

---

## 📊 Endpoints de Estado de Energía

### 1. Guardar Estado de Energía
```http
POST /energy
```

Registra el estado actual del semáforo del usuario.

**Request Body:**
```json
{
  "energy_state": "verde|ambar|rojo",
  "notes": "Descripción opcional del estado"
}
```

**Response:** `201 Created`
```json
{
  "id": 123,
  "user_id": 1,
  "energy_state": "verde",
  "notes": "Me siento con energía y enfocado",
  "recorded_at": "2025-11-10T14:30:00"
}
```

### 2. Obtener Historial de Energía
```http
GET /energy/history?skip=0&limit=30
```

**Response:** `200 OK`
```json
[
  {
    "id": 123,
    "user_id": 1,
    "energy_state": "verde",
    "notes": "Me siento bien",
    "recorded_at": "2025-11-10T14:30:00"
  }
]
```

### 3. Obtener Registros de Energía de Hoy
```http
GET /energy/today
```

**Response:** `200 OK`
```json
[
  {
    "id": 123,
    "energy_state": "verde",
    "recorded_at": "2025-11-10T08:00:00"
  },
  {
    "id": 124,
    "energy_state": "ambar",
    "recorded_at": "2025-11-10T14:30:00"
  }
]
```

### 4. Estadísticas de Energía
```http
GET /energy/stats?days=30
```

**Response:** `200 OK`
```json
{
  "total_records": 45,
  "verde_count": 20,
  "ambar_count": 15,
  "rojo_count": 10,
  "verde_percentage": 44.4,
  "ambar_percentage": 33.3,
  "rojo_percentage": 22.3,
  "most_common_state": "verde"
}
```

---

## 🧘 Endpoints de Ejercicios

### 5. Obtener Recomendación de Ejercicio
```http
POST /exercises/recommend
```

Obtiene un ejercicio aleatorio basado en el estado del semáforo, con un resumen generado por IA.

**Request Body:**
```json
{
  "energy_state": "verde|ambar|rojo"
}
```

**Response:** `200 OK`
```json
{
  "exercise": {
    "id": 1,
    "name": "Pasos que Exhalan",
    "objective": "Descargar agitación coordinando pasos y exhalación",
    "context": "De pie/En movimiento",
    "duration_seconds": 90,
    "recommended_state": "rojo",
    "taxonomy": "Walking breathing; descarga motora regulada",
    "body_systems": "Patrón de marcha; respiración; propiocepción plantar",
    "steps": "[\"De pie, siente las plantas de los pies\", ...]",
    "voice_scripts": "[\"Explora de cabeza a pies...\", ...]",
    "measurement_notes": "Intensidad 0-10 pre/post",
    "ux_notes": "Círculo de progreso...",
    "safeguards": "Permitir saltar zonas si hay incomodidad"
  },
  "ai_summary": "Veo que estás en rojo, lo cual es completamente válido. Este ejercicio te ayudará a descargar esa agitación de forma suave y controlada. Es perfecto para tu momento actual.",
  "reason": "Este ejercicio es ideal para tu estado actual de calma y restauración"
}
```

**Errores:**
- `400`: Estado inválido
- `404`: No hay ejercicios disponibles para ese estado

### 6. Obtener Todos los Ejercicios
```http
GET /exercises?skip=0&limit=100
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Pasos que Exhalan",
    "objective": "Descargar agitación...",
    "duration_seconds": 90,
    "recommended_state": "rojo",
    ...
  }
]
```

### 7. Obtener Ejercicio Específico
```http
GET /exercises/{exercise_id}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Pasos que Exhalan",
  "objective": "Descargar agitación coordinando pasos y exhalación",
  "context": "De pie/En movimiento",
  "duration_seconds": 90,
  "recommended_state": "rojo",
  ...
}
```

**Errores:**
- `404`: Ejercicio no encontrado

### 8. 🗑️ Eliminar Ejercicio (NUEVO)
```http
DELETE /exercises/{exercise_id}
```

Elimina un ejercicio específico por su ID. También elimina todas las completaciones asociadas.

**Response:** `204 No Content`

**Errores:**
- `404`: Ejercicio no encontrado

**⚠️ Advertencia:** Esta acción es permanente y eliminará:
- El ejercicio de la base de datos
- Todas las completaciones de usuarios asociadas a este ejercicio
- Afectará las estadísticas de usuarios que lo completaron

**Ejemplo cURL:**
```bash
curl -X DELETE \
  http://localhost:8000/api/v1/wellness/exercises/5 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## ✅ Endpoints de Completaciones

### 9. Completar Ejercicio Directo
```http
POST /exercises/complete
```

Crea un registro de completación con mediciones pre y post en un solo paso.

**Request Body:**
```json
{
  "exercise_id": 1,
  "intensity_pre": 8,
  "intensity_post": 4,
  "notes": "Me sentí mucho mejor después"
}
```

**Response:** `201 Created`
```json
{
  "id": 456,
  "user_id": 1,
  "exercise_id": 1,
  "intensity_pre": 8,
  "intensity_post": 4,
  "notes": "Me sentí mucho mejor después",
  "started_at": "2025-11-10T15:00:00",
  "completed_at": "2025-11-10T15:01:30",
  "completed": true
}
```

### 10. Iniciar Ejercicio (Dos Pasos)
```http
POST /completions
```

Crea un registro de inicio de ejercicio (primer paso).

**Request Body:**
```json
{
  "exercise_id": 1,
  "intensity_pre": 7
}
```

**Response:** `201 Created`
```json
{
  "id": 456,
  "user_id": 1,
  "exercise_id": 1,
  "intensity_pre": 7,
  "intensity_post": null,
  "started_at": "2025-11-10T15:00:00",
  "completed_at": null,
  "completed": false
}
```

### 11. Completar Ejercicio Iniciado
```http
PATCH /completions/{completion_id}
```

Actualiza un ejercicio iniciado con las mediciones post.

**Request Body:**
```json
{
  "intensity_post": 3,
  "notes": "Ejercicio completado",
  "completed_at": true
}
```

**Response:** `200 OK`
```json
{
  "id": 456,
  "user_id": 1,
  "exercise_id": 1,
  "intensity_pre": 7,
  "intensity_post": 3,
  "notes": "Ejercicio completado",
  "completed": true,
  "completed_at": "2025-11-10T15:02:00"
}
```

**Errores:**
- `404`: Completación no encontrada
- `403`: No tienes permiso (no es tu completación)

### 12. Obtener Historial de Completaciones
```http
GET /completions?skip=0&limit=50
```

**Response:** `200 OK`
```json
[
  {
    "id": 456,
    "user_id": 1,
    "exercise_id": 1,
    "intensity_pre": 7,
    "intensity_post": 3,
    "started_at": "2025-11-10T15:00:00",
    "completed_at": "2025-11-10T15:02:00",
    "completed": true
  }
]
```

### 13. Obtener Completaciones de Hoy
```http
GET /completions/today
```

**Response:** `200 OK`
```json
[
  {
    "id": 456,
    "exercise_id": 1,
    "intensity_pre": 7,
    "intensity_post": 3,
    "completed": true,
    "started_at": "2025-11-10T08:30:00"
  }
]
```

---

## 📈 Endpoints de Estadísticas

### 14. Estadísticas Generales de Wellness
```http
GET /stats
```

**Response:** `200 OK`
```json
{
  "streak": 7,
  "total_completions": 42,
  "last_completion": "2025-11-10T15:00:00"
}
```

### 15. Estadísticas de Ejercicios
```http
GET /stats/exercises?days=30
```

**Response:** `200 OK`
```json
{
  "total_completions": 20,
  "exercises_by_state": {
    "verde": 8,
    "ambar": 7,
    "rojo": 5
  },
  "most_completed_exercise": {
    "id": 1,
    "name": "Pasos que Exhalan",
    "count": 10
  },
  "average_intensity_reduction": 4.2
}
```

### 16. Obtener Racha de Días
```http
GET /stats/streak
```

**Response:** `200 OK`
```json
{
  "streak_days": 7
}
```

---

## 🔄 Flujos de Uso Comunes

### Flujo 1: Usuario Registra Estado y Hace Ejercicio
1. Usuario selecciona estado: `POST /energy` → `{ "energy_state": "ambar" }`
2. Pide recomendación: `POST /exercises/recommend` → `{ "energy_state": "ambar" }`
3. Inicia ejercicio: `POST /completions` → `{ "exercise_id": 2, "intensity_pre": 6 }`
4. Completa ejercicio: `PATCH /completions/123` → `{ "intensity_post": 3, "completed_at": true }`

### Flujo 2: Usuario Completa Ejercicio Directo
1. Usuario selecciona estado: `POST /energy` → `{ "energy_state": "verde" }`
2. Pide recomendación: `POST /exercises/recommend` → `{ "energy_state": "verde" }`
3. Completa en un paso: `POST /exercises/complete` → `{ "exercise_id": 3, "intensity_pre": 5, "intensity_post": 2 }`

### Flujo 3: Admin Elimina Ejercicio No Deseado
1. Ver ejercicios: `GET /exercises`
2. Identificar ID del ejercicio a eliminar
3. Eliminar: `DELETE /exercises/5`

---

## 🔒 Consideraciones de Seguridad

1. **Autenticación Requerida**: Todos los endpoints requieren JWT válido
2. **Autorización**: Los usuarios solo pueden ver/modificar sus propios datos
3. **Validación**: Todos los estados del semáforo son validados (verde/ambar/rojo)
4. **Soft Delete Recomendado**: Para producción, considera implementar soft delete en lugar de DELETE permanente

---

## 📊 Schemas de Datos

### MetamotivationEnergy
```typescript
{
  id: number
  user_id: number
  energy_state: "verde" | "ambar" | "rojo"
  notes?: string
  recorded_at: datetime
}
```

### WellnessExercise
```typescript
{
  id: number
  name: string
  objective: string
  context: string
  duration_seconds: number
  recommended_state: "verde" | "ambar" | "rojo" | "cualquiera"
  taxonomy: string
  body_systems: string
  steps: string  // JSON array
  voice_scripts: string  // JSON array
  measurement_notes?: string
  ux_notes?: string
  safeguards?: string
}
```

### ExerciseCompletion
```typescript
{
  id: number
  user_id: number
  exercise_id: number
  intensity_pre: number  // 0-10
  intensity_post?: number  // 0-10
  notes?: string
  started_at: datetime
  completed_at?: datetime
  completed: boolean
}
```

---

## 🐛 Códigos de Error Comunes

| Código | Descripción |
|--------|-------------|
| 400 | Bad Request - Estado inválido o datos incorrectos |
| 401 | Unauthorized - Token JWT inválido o expirado |
| 403 | Forbidden - No tienes permiso para este recurso |
| 404 | Not Found - Ejercicio o completación no encontrada |
| 500 | Internal Server Error - Error del servidor |

---

## 📚 Referencias

- **Modelos**: `app/models/wellness_exercise.py`, `app/models/exercise_completion.py`
- **CRUD**: `app/crud/crud_wellness.py`, `app/crud/crud_energy.py`, `app/crud/crud_completion.py`
- **Endpoints**: `app/api/v1/endpoints/wellness.py`
- **Guía de Eliminación**: `DELETE_EXERCISES_GUIDE.md`
