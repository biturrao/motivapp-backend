-- Script SQL para limpiar ejercicios antiguos en Azure PostgreSQL
-- y permitir que los 3 nuevos ejercicios se carguen correctamente

-- IMPORTANTE: Ejecutar en este orden

-- 1. Primero, eliminar las completaciones de ejercicios antiguos
-- (para evitar violaciones de foreign key)
DELETE FROM exercise_completions 
WHERE exercise_id NOT IN (
    SELECT id FROM wellness_exercises 
    WHERE name IN ('Pasos que Exhalan', 'Anclaje Corazón-Respira', 'Escaneo Amable 60')
);

-- 2. Luego, eliminar todos los ejercicios EXCEPTO los 3 nuevos (si existen)
DELETE FROM wellness_exercises 
WHERE name NOT IN ('Pasos que Exhalan', 'Anclaje Corazón-Respira', 'Escaneo Amable 60');

-- 3. Finalmente, eliminar TODOS los ejercicios para permitir recarga completa
-- (solo si quieres empezar desde cero)
DELETE FROM exercise_completions;
DELETE FROM wellness_exercises;

-- 4. Verificar que la tabla esté vacía
SELECT COUNT(*) as total_exercises FROM wellness_exercises;
SELECT COUNT(*) as total_completions FROM exercise_completions;

-- NOTA: Después de ejecutar este script, reinicia la aplicación en Azure
-- para que seed_wellness_exercises() cargue los 3 nuevos ejercicios automáticamente.

-- ALTERNATIVA: Si quieres mantener las estadísticas de completación:
-- Solo ejecuta los pasos 1 y 2, no el paso 3.
