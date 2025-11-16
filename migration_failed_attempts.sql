-- Migration: Reemplazar last_eval_result con failed_attempts
-- Fecha: 2025-11-16
-- Descripción: Migración para actualizar el esquema de session_states

-- 1. Agregar nueva columna failed_attempts
ALTER TABLE session_states 
ADD COLUMN failed_attempts INTEGER NOT NULL DEFAULT 0;

-- 2. Eliminar la columna antigua last_eval_result
ALTER TABLE session_states 
DROP COLUMN last_eval_result;

-- Comentario: Esta migración es parte del cambio de arquitectura para usar
-- un contador simple (failed_attempts) en lugar del objeto complejo EvalResult
