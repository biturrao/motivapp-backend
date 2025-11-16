-- Migration: Actualizar schema de session_states
-- Fecha: 2025-11-16
-- Descripción: Migración para actualizar el esquema de session_states con nuevos campos

-- 1. Agregar nuevas columnas
ALTER TABLE session_states 
ADD COLUMN IF NOT EXISTS onboarding_complete BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE session_states 
ADD COLUMN IF NOT EXISTS strategy_given BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE session_states 
ADD COLUMN IF NOT EXISTS failed_attempts INTEGER NOT NULL DEFAULT 0;

-- 2. Eliminar la columna antigua last_eval_result (si existe)
ALTER TABLE session_states 
DROP COLUMN IF EXISTS last_eval_result;

-- Comentario: Esta migración es parte del cambio de arquitectura para:
-- - Usar onboarding_complete y strategy_given para control de flujo
-- - Usar failed_attempts en lugar del objeto complejo EvalResult
