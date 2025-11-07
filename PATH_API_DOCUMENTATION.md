# API de Path (Ruta de Aprendizaje)

## Resumen
El sistema de Path permite a los usuarios seguir un recorrido de aprendizaje personalizado a través de diferentes secciones, cada una con contenidos teóricos (videos, audio, texto) y lecciones prácticas. El progreso del usuario se guarda en la nube.

## Estructura de Datos

### Secciones (Sections)
Las 4 secciones principales en orden:
1. **Iniciar** - Fundamentos del entrenamiento de la mente
2. **Autoregulación** - Habilidades de autorregulación
3. **Creencias** - Exploración y modificación de creencias
4. **Señales Internas** - Identificación de señales internas

### Contenidos (Contents)
- Materiales teóricos: VIDEO, AUDIO, TEXT
- Cada contenido tiene un orden dentro de su sección
- Incluye título, descripción, URL y duración

### Lecciones (Lessons)
- Ejercicios prácticos ordenados
- Similar estructura a contenidos
- Progreso independiente de contenidos

### Progreso del Usuario (User Progress)
- **UserContentProgress**: Seguimiento de contenidos completados
- **UserLessonProgress**: Seguimiento de lecciones completadas
- **UserSectionProgress**: Posición actual en cada sección

## Endpoints de la API

### 1. Obtener Resumen del Path
```
GET /api/v1/path/overview
```
**Respuesta:**
```json
{
  "total_sections": 4,
  "completed_sections": 1,
  "current_section_id": 2,
  "current_section_name": "Autoregulación",
  "overall_progress_percentage": 25.0
}
```

### 2. Obtener Todas las Secciones con Progreso
```
GET /api/v1/path/sections
```
**Respuesta:**
```json
[
  {
    "id": 1,
    "name": "Iniciar",
    "description": "Fundamentos...",
    "order": 1,
    "icon_name": "compass",
    "contents": [
      {
        "id": 1,
        "section_id": 1,
        "title": "Introducción a Iniciar",
        "description": "Contenido teórico...",
        "content_type": "video",
        "content_url": "https://...",
        "duration_minutes": 5,
        "order": 1,
        "completed": true,
        "last_accessed": "2025-11-07T12:00:00"
      }
    ],
    "lessons": [
      {
        "id": 1,
        "section_id": 1,
        "title": "Lección 1: Primeros pasos",
        "description": "Primera lección...",
        "content_url": "https://...",
        "duration_minutes": 15,
        "order": 1,
        "completed": false,
        "last_accessed": null
      }
    ],
    "completed_contents": 2,
    "total_contents": 2,
    "completed_lessons": 1,
    "total_lessons": 2,
    "current_content_order": 1,
    "current_lesson_order": 2,
    "is_completed": false
  }
]
```

### 3. Obtener una Sección Específica con Progreso
```
GET /api/v1/path/sections/{section_id}
```
Retorna la misma estructura que arriba pero para una sección específica.

### 4. Actualizar Progreso de Contenido
```
POST /api/v1/path/content/progress
```
**Body:**
```json
{
  "content_id": 1,
  "completed": true
}
```

### 5. Actualizar Progreso de Lección
```
POST /api/v1/path/lesson/progress
```
**Body:**
```json
{
  "lesson_id": 1,
  "completed": true
}
```

### 6. Actualizar Progreso de Sección
```
POST /api/v1/path/section/progress
```
**Body:**
```json
{
  "section_id": 1,
  "current_content_order": 2,
  "current_lesson_order": 3,
  "completed": false
}
```

## Modelos de Base de Datos

### Tabla: sections
- id (PK)
- name (string)
- description (text)
- order (integer) - Orden en el path
- icon_name (string) - Nombre del icono para el frontend

### Tabla: contents
- id (PK)
- section_id (FK)
- title (string)
- description (text)
- content_type (enum: video, audio, text)
- content_url (string)
- duration_minutes (integer)
- order (integer) - Orden dentro de la sección

### Tabla: lessons
- id (PK)
- section_id (FK)
- title (string)
- description (text)
- content_url (string)
- duration_minutes (integer)
- order (integer)

### Tabla: user_content_progress
- id (PK)
- user_id (FK)
- content_id (FK)
- completed (boolean)
- completed_at (datetime)
- last_accessed (datetime)

### Tabla: user_lesson_progress
- id (PK)
- user_id (FK)
- lesson_id (FK)
- completed (boolean)
- completed_at (datetime)
- last_accessed (datetime)

### Tabla: user_section_progress
- id (PK)
- user_id (FK)
- section_id (FK)
- current_content_order (integer)
- current_lesson_order (integer)
- completed (boolean)
- completed_at (datetime)

## Características Clave

1. **Progreso Individual**: Cada usuario tiene su propio progreso guardado en la nube
2. **Tracking Granular**: Se rastrea el progreso de contenidos, lecciones y secciones
3. **Orden Secuencial**: Los elementos están ordenados para guiar el aprendizaje
4. **Timestamps**: Se guardan fechas de completación y último acceso
5. **Dashboard Ready**: Los datos están estructurados para facilitar reportes y análisis

## Flujo de Uso

1. Usuario inicia sesión
2. Frontend obtiene `/api/v1/path/sections` para mostrar todo el path
3. Usuario selecciona una sección
4. Usuario completa contenidos/lecciones
5. Frontend actualiza progreso con POST a `/content/progress` o `/lesson/progress`
6. Sistema actualiza automáticamente el progreso de la sección
7. Dashboard puede consultar progreso para análisis

## Datos Iniciales

El sistema crea automáticamente:
- 4 secciones (Iniciar, Autoregulación, Creencias, Señales Internas)
- 2 contenidos de ejemplo por sección
- 2 lecciones de ejemplo por sección

Estos son datos de ejemplo que debes reemplazar con contenido real.
