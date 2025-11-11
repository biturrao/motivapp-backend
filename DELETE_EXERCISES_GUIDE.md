# Eliminación de Ejercicios - Guía de Uso

## 📋 Problema Resuelto

Anteriormente no existía una forma de eliminar ejercicios de bienestar que no querías. Ahora se ha agregado un endpoint DELETE y la funcionalidad completa para eliminar ejercicios.

## 🔧 Implementación

### Backend - Endpoint Agregado

**DELETE** `/api/v1/wellness/exercises/{exercise_id}`

- **Descripción**: Elimina un ejercicio específico por su ID
- **Autenticación**: Requiere token JWT
- **Status Code**: 204 No Content (éxito) o 404 Not Found (no existe)

### Características Importantes

1. **Eliminación en Cascada**: Cuando eliminas un ejercicio, automáticamente se eliminan todas las completaciones asociadas (gracias a `cascade="all, delete-orphan"` en el modelo)

2. **Validación**: El endpoint verifica que el ejercicio existe antes de intentar eliminarlo

3. **Seguridad**: Requiere autenticación (usuario debe estar logueado)

## 📝 Ejemplos de Uso

### Desde el Frontend (TypeScript/React Native)

```typescript
// En tu servicio API (wellness.ts o similar)
export const deleteExercise = async (exerciseId: number) => {
  const token = await getAuthToken();
  
  const response = await fetch(
    `${API_BASE_URL}/api/v1/wellness/exercises/${exerciseId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );
  
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Ejercicio no encontrado');
    }
    throw new Error('Error al eliminar ejercicio');
  }
  
  return true; // Eliminado exitosamente
};
```

### Desde Python (Script o Pruebas)

```python
from app.db.session import SessionLocal
from app.crud import crud_wellness

db = SessionLocal()

# Eliminar ejercicio por ID
exercise_id = 1
deleted = crud_wellness.delete_exercise(db, exercise_id)

if deleted:
    print("✅ Ejercicio eliminado exitosamente")
else:
    print("❌ Ejercicio no encontrado")

db.close()
```

### Desde cURL

```bash
# Obtener token primero
TOKEN="tu_jwt_token_aqui"

# Eliminar ejercicio con ID 5
curl -X DELETE \
  http://localhost:8000/api/v1/wellness/exercises/5 \
  -H "Authorization: Bearer $TOKEN"
```

## 🧪 Probar la Funcionalidad

1. **Ver ejercicios disponibles**:
   ```bash
   python test_delete_exercise.py
   ```

2. **Eliminar desde API**:
   - Primero obtén la lista de ejercicios: `GET /api/v1/wellness/exercises`
   - Identifica el ID del ejercicio a eliminar
   - Llama al endpoint DELETE con ese ID

## ⚠️ Consideraciones

1. **No hay "undo"**: Una vez eliminado, el ejercicio y sus completaciones se borran permanentemente de la base de datos

2. **Impacto en estadísticas**: Si un usuario había completado ese ejercicio, esas completaciones también se eliminarán, lo que afectará:
   - Racha de días consecutivos
   - Total de ejercicios completados
   - Historial de completaciones

3. **Recomendación**: En lugar de eliminar, considera:
   - Agregar un campo `active` o `deleted` para "soft delete"
   - Ocultar ejercicios en lugar de eliminarlos permanentemente
   - Mantener las completaciones históricas incluso si se elimina el ejercicio

## 🔄 Alternativa: Soft Delete (Recomendado para Producción)

Si prefieres mantener los datos históricos, puedes implementar un "soft delete":

### Modificar el modelo:
```python
# En app/models/wellness_exercise.py
is_active = Column(Boolean, default=True, nullable=False)
deleted_at = Column(DateTime, nullable=True)
```

### Modificar las queries:
```python
# Solo mostrar ejercicios activos
exercises = db.query(WellnessExercise).filter(
    WellnessExercise.is_active == True
).all()

# "Eliminar" marcando como inactivo
def soft_delete_exercise(db: Session, exercise_id: int):
    exercise = db.query(WellnessExercise).filter(
        WellnessExercise.id == exercise_id
    ).first()
    if exercise:
        exercise.is_active = False
        exercise.deleted_at = datetime.utcnow()
        db.commit()
        return True
    return False
```

## 📚 Referencias

- **Modelo**: `app/models/wellness_exercise.py`
- **CRUD**: `app/crud/crud_wellness.py` - función `delete_exercise()`
- **Endpoint**: `app/api/v1/endpoints/wellness.py` - `DELETE /exercises/{exercise_id}`
- **Script de prueba**: `test_delete_exercise.py`
