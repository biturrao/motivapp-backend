-- Script para crear la tabla session_states en Azure PostgreSQL
-- Ejecutar solo si no se pueden usar migraciones automáticas

-- Crear tabla session_states
CREATE TABLE IF NOT EXISTS session_states (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    greeted BOOLEAN NOT NULL DEFAULT FALSE,
    iteration INTEGER NOT NULL DEFAULT 0,
    sentimiento_inicial VARCHAR(100),
    sentimiento_actual VARCHAR(100),
    slots JSONB DEFAULT '{}'::jsonb,
    "Q2" VARCHAR(10),
    "Q3" VARCHAR(10),
    enfoque VARCHAR(50),
    tiempo_bloque INTEGER,
    last_strategy TEXT,
    last_eval_result JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    
    CONSTRAINT fk_session_state_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Crear índices
CREATE INDEX IF NOT EXISTS idx_session_states_user_id ON session_states(user_id);
CREATE INDEX IF NOT EXISTS idx_session_states_updated_at ON session_states(updated_at);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_session_state_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW() AT TIME ZONE 'utc';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_session_state_updated_at
    BEFORE UPDATE ON session_states
    FOR EACH ROW
    EXECUTE FUNCTION update_session_state_updated_at();

-- Verificar que la tabla fue creada correctamente
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'session_states'
ORDER BY ordinal_position;

-- Comentarios para documentación
COMMENT ON TABLE session_states IS 'Almacena el estado de la sesión metamotivacional de Flou para cada usuario';
COMMENT ON COLUMN session_states.user_id IS 'Referencia única al usuario (one-to-one)';
COMMENT ON COLUMN session_states.greeted IS 'Flag para evitar saludos repetidos en la sesión';
COMMENT ON COLUMN session_states.iteration IS 'Contador de ciclos del bucle metamotivacional (0-3)';
COMMENT ON COLUMN session_states.slots IS 'JSON con sentimiento, tipo_tarea, ramo, plazo, fase, tiempo_bloque';
COMMENT ON COLUMN session_states."Q2" IS 'Tipo de demanda: A (creativa) o B (analítica)';
COMMENT ON COLUMN session_states."Q3" IS 'Nivel de abstracción: ↑ (por qué), ↓ (cómo), o mixto';
COMMENT ON COLUMN session_states.enfoque IS 'Enfoque regulatorio: promocion_eager o prevencion_vigilant';
COMMENT ON COLUMN session_states.tiempo_bloque IS 'Duración del bloque de trabajo en minutos: 10, 12, 15 o 25';
COMMENT ON COLUMN session_states.last_strategy IS 'Última estrategia sugerida por Flou';
COMMENT ON COLUMN session_states.last_eval_result IS 'JSON con exito (bool) y cambio_sentimiento (↑/=/↓)';
