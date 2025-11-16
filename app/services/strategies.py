"""
Banco de estrategias basadas en Task-Motivation Fit (Scholer & Miele, 2016)

Este módulo contiene estrategias concretas organizadas según:
- Enfoque Regulatorio (Promoción vs. Prevención)
- Nivel de Construcción (Abstracto vs. Concreto)
- Tipo de Tarea (según demandas específicas)

Referencias:
- Miele, D. B., & Scholer, A. A. (2016). The role of metamotivational monitoring in motivation regulation.
- Higgins, E. T. (1997). Beyond pleasure and pain. American Psychologist.
- Trope, Y., & Liberman, N. (2010). Construal-level theory of psychological distance.
"""

from typing import Dict, List, Optional
from enum import Enum


class EnfoqueRegulatorio(str, Enum):
    """Enfoque regulatorio según Higgins (1997)"""
    PROMOCION_EAGER = "promocion_eager"  # Orientación a logros, ganancias, crecimiento
    PREVENCION_VIGILANT = "prevencion_vigilant"  # Orientación a seguridad, evitar errores


class NivelConstruccion(str, Enum):
    """Nivel de construcción según Trope & Liberman (2010)"""
    ABSTRACTO = "↑"  # Alto nivel: "Por qué", visión global, propósito
    CONCRETO = "↓"  # Bajo nivel: "Cómo", detalles, pasos específicos


class TipoFit(str, Enum):
    """Tipos de ajuste tarea-motivación"""
    # Enfoque Regulatorio
    EAGER_CREATIVO = "eager_creativo"  # Tareas que requieren entusiasmo y pensamiento divergente
    VIGILANT_PRECISION = "vigilant_precision"  # Tareas que requieren cuidado y detección de errores
    
    # Nivel de Construcción
    ABSTRACTO_AUTOCONTROL = "abstracto_autocontrol"  # Tareas de autocontrol y metas a largo plazo
    CONCRETO_PRECISION_MOTORA = "concreto_precision_motora"  # Tareas de ejecución precisa
    
    # Autodeterminación
    AUTONOMA_ABIERTA = "autonoma_abierta"  # Tareas abiertas que requieren absorción
    CONTROLADA_CERRADA = "controlada_cerrada"  # Tareas cerradas con criterios estrictos


# ============================================================================
# ESTRATEGIAS SEGÚN ENFOQUE REGULATORIO
# ============================================================================

ESTRATEGIAS_PROMOCION_EAGER = {
    "lluvia_ideas_rapida": {
        "nombre": "Lluvia de Ideas Sin Filtro",
        "fit": TipoFit.EAGER_CREATIVO,
        "descripcion": "Genera todas las ideas que puedas sin juzgarlas",
        "nivel_recomendado": NivelConstruccion.ABSTRACTO,
        "tareas": ["ensayo", "borrador", "presentacion", "esquema"],
        "fases": ["ideacion", "planificacion"],
        "tiempo_minimo": 10,
        "template": """Perfecto, vamos a aprovechar esa energía. 🚀

**Tu misión (próximos {tiempo} min):**
1. Abre un documento en blanco
2. Escribe TODAS las ideas que se te ocurran sobre {tema}
3. No borres NADA - cantidad sobre calidad por ahora
4. Tip: Usa palabras clave sueltas, no frases perfectas

**¿Por qué funciona?** Tu cerebro en modo promoción es genial generando posibilidades. ¡Aprovéchalo!

¿Le damos? 💪"""
    },
    
    "avance_rapido_cantidad": {
        "nombre": "Avance Rápido: Prioriza Cantidad",
        "fit": TipoFit.EAGER_CREATIVO,
        "descripcion": "Escribe sin detenerte, ignorando errores temporalmente",
        "nivel_recomendado": NivelConstruccion.CONCRETO,
        "tareas": ["ensayo", "borrador", "lectura_tecnica"],
        "fases": ["ejecucion"],
        "tiempo_minimo": 15,
        "template": """Entiendo que quieres avanzar rápido. ¡Usemos eso! ⚡

**Tu bloque de {tiempo} min:**
1. Pon un timer (no lo mires hasta que suene)
2. Escribe sin parar - no corrijas NADA
3. Si te atascas, escribe "XXXX" y sigue
4. Meta: {cantidad} párrafos/páginas mínimo

**Regla de oro:** Los errores se corrigen DESPUÉS. Ahora solo avanza.

¿Listo/a? 🏃"""
    },
    
    "exploracion_divergente": {
        "nombre": "Exploración Multi-Perspectiva",
        "fit": TipoFit.EAGER_CREATIVO,
        "descripcion": "Explora múltiples ángulos de un problema sin comprometerte",
        "nivel_recomendado": NivelConstruccion.ABSTRACTO,
        "tareas": ["ensayo", "presentacion", "esquema"],
        "fases": ["ideacion", "planificacion"],
        "tiempo_minimo": 12,
        "template": """Vamos a abrir tu mente a todas las posibilidades. 🌟

**Ejercicio ({tiempo} min):**
- Pregunta: "¿Qué pasaría si...?" sobre {tema}
- Anota 3 perspectivas diferentes (no importa si son "locas")
- Para cada una, escribe 2-3 pros/cons rápidos
- No elijas nada todavía - solo explora

**¿Por qué?** Tu cerebro necesita jugar antes de decidir.

¿Te tinca? 🎨"""
    },
    
    "prototipo_imperfecto": {
        "nombre": "Prototipo Rápido e Imperfecto",
        "fit": TipoFit.EAGER_CREATIVO,
        "descripcion": "Crea una versión mínima funcional sin pulir",
        "nivel_recomendado": NivelConstruccion.CONCRETO,
        "tareas": ["presentacion", "esquema", "coding", "protocolo_lab"],
        "fases": ["ejecucion"],
        "tiempo_minimo": 15,
        "template": """Hagamos un "esqueleto" funcional ahora. 🦴

**En {tiempo} min, crea:**
- Estructura básica (títulos/secciones)
- 1 ejemplo o slide por sección
- Nada de formato bonito todavía
- Meta: Que se entienda la idea central

**Mantra:** "Hecho es mejor que perfecto (por ahora)."

¿Vamos? 💪"""
    }
}


ESTRATEGIAS_PREVENCION_VIGILANT = {
    "checklist_revision": {
        "nombre": "Checklist de Revisión Sistemática",
        "fit": TipoFit.VIGILANT_PRECISION,
        "descripcion": "Revisa el trabajo punto por punto para evitar errores",
        "nivel_recomendado": NivelConstruccion.CONCRETO,
        "tareas": ["proofreading", "revision"],
        "fases": ["revision"],
        "tiempo_minimo": 10,
        "template": """Vamos a revisar con calma y asegurarnos de que todo esté bien. ✓

**Checklist ({tiempo} min):**
1. **Gramática:** Lee en voz alta, detecta errores
2. **Estructura:** ¿Tiene introducción/desarrollo/cierre?
3. **Coherencia:** ¿Las ideas fluyen?
4. **Formato:** ¿Cumple requisitos (fuente, márgenes)?

Usa un ✓ al completar cada paso. Ve lento, es normal.

¿Empezamos? 🔍"""
    },
    
    "lectura_anotada": {
        "nombre": "Lectura Anotada y Crítica",
        "fit": TipoFit.VIGILANT_PRECISION,
        "descripcion": "Lee cuidadosamente tomando notas de precisión",
        "nivel_recomendado": NivelConstruccion.CONCRETO,
        "tareas": ["lectura_tecnica", "resumen"],
        "fases": ["ejecucion"],
        "tiempo_minimo": 15,
        "template": """Vamos a leer con atención de detective. 🔎

**Protocolo de {tiempo} min:**
1. Lee UN párrafo a la vez
2. Subraya conceptos clave
3. Anota en el margen: "¿Qué dice esto?"
4. Si algo no queda claro, marca con "?"

**No avances si no entendiste.** Mejor poco bien hecho.

¿Te parece? 📚"""
    },
    
    "verificacion_doble": {
        "nombre": "Verificación Doble de Errores",
        "fit": TipoFit.VIGILANT_PRECISION,
        "descripcion": "Revisa dos veces con enfoques diferentes",
        "nivel_recomendado": NivelConstruccion.CONCRETO,
        "tareas": ["proofreading", "coding", "resolver_problemas"],
        "fases": ["revision"],
        "tiempo_minimo": 12,
        "template": """Doble verificación para estar seguro/a. 🛡️

**Ronda 1 ({mitad_tiempo} min):** Lee de corrido, marca errores obvios
**Ronda 2 ({mitad_tiempo} min):** Lee AL REVÉS (última oración primero), busca typos

**¿Por qué al revés?** Tu cerebro no "autocompleta", ve lo que REALMENTE dice.

¿Listo para el detective mode? 🕵️"""
    },
    
    "validacion_criterios": {
        "nombre": "Validación por Criterios de Rúbrica",
        "fit": TipoFit.VIGILANT_PRECISION,
        "descripcion": "Verifica cumplimiento punto por punto de criterios",
        "nivel_recomendado": NivelConstruccion.CONCRETO,
        "tareas": ["ensayo", "presentacion", "protocolo_lab"],
        "fases": ["revision"],
        "tiempo_minimo": 10,
        "template": """Vamos a verificar que cumples TODOS los requisitos. ✅

**Revisión de {tiempo} min:**
1. Abre la rúbrica/instrucciones del profe
2. Crea una tabla: Criterio | ¿Cumple? | Evidencia
3. Revisa UNO por uno (sin saltar)
4. Si falta algo, anótalo para después

**Meta:** Cero sorpresas en la evaluación.

¿Vamos? 📋"""
    },
    
    "deteccion_errores_comunes": {
        "nombre": "Detección de Errores Frecuentes",
        "fit": TipoFit.VIGILANT_PRECISION,
        "descripcion": "Busca errores que sueles cometer",
        "nivel_recomendado": NivelConstruccion.CONCRETO,
        "tareas": ["proofreading", "coding", "resolver_problemas"],
        "fases": ["revision"],
        "tiempo_minimo": 10,
        "template": """Vamos a buscar tus "errores favoritos". 🎯

**Cazando bugs ({tiempo} min):**
1. ¿Qué errores sueles cometer? (ej: "haber/a ver", punto y coma en código)
2. Usa "Buscar" (Ctrl+F) para cada uno
3. Revisa SOLO esos casos específicos
4. Corrígelos uno por uno

**Tip:** Crea tu lista personal de "errores a vigilar".

¿Le entramos? 🔧"""
    }
}


# ============================================================================
# ESTRATEGIAS SEGÚN NIVEL DE CONSTRUCCIÓN
# ============================================================================

ESTRATEGIAS_ABSTRACTO_ALTO_NIVEL = {
    "vision_proposito": {
        "nombre": "Conectar con el Propósito Superior",
        "fit": TipoFit.ABSTRACTO_AUTOCONTROL,
        "descripcion": "Reflexiona sobre el 'por qué' de la tarea",
        "enfoque_recomendado": EnfoqueRegulatorio.PROMOCION_EAGER,
        "tareas": ["ensayo", "presentacion", "lectura_tecnica"],
        "fases": ["ideacion", "planificacion"],
        "tiempo_minimo": 5,
        "template": """Antes de ponerte a trabajar, conéctate con el "por qué". 🎯

**Reflexión ({tiempo} min):**
- ¿Por qué es importante este trabajo PARA TI?
- ¿Qué vas a aprender/lograr con esto?
- ¿Cómo se conecta con tus metas más grandes?

Escribe 2-3 frases sobre esto. Cuando te distraigas, vuelve a leerlas.

¿Te hace sentido? 🌟"""
    },
    
    "mapa_mental_global": {
        "nombre": "Mapa Mental de Visión Global",
        "fit": TipoFit.ABSTRACTO_AUTOCONTROL,
        "descripcion": "Visualiza la estructura completa antes de detalles",
        "enfoque_recomendado": EnfoqueRegulatorio.PROMOCION_EAGER,
        "tareas": ["ensayo", "esquema", "presentacion"],
        "fases": ["ideacion", "planificacion"],
        "tiempo_minimo": 10,
        "template": """Vamos a ver el "bosque completo" antes de los árboles. 🌲🌳

**Mapa mental ({tiempo} min):**
1. En el centro: Idea principal
2. Ramas grandes: 3-4 temas principales
3. Sub-ramas: Ideas secundarias (opcional)
4. NO escribas oraciones - solo conceptos

**Meta:** Entender la arquitectura general.

¿Vamos a dibujarlo? 🎨"""
    },
    
    "objetivo_futuro": {
        "nombre": "Visualización del Yo Futuro",
        "fit": TipoFit.ABSTRACTO_AUTOCONTROL,
        "descripcion": "Imagina cómo te sentirás al completar la tarea",
        "enfoque_recomendado": EnfoqueRegulatorio.PROMOCION_EAGER,
        "tareas": ["cualquiera"],
        "fases": ["cualquiera"],
        "tiempo_minimo": 3,
        "template": """Hagamos un ejercicio rápido de visualización. ✨

**Imaginación guiada ({tiempo} min):**
Cierra los ojos. Imagínate:
- Ya terminaste {tarea}
- ¿Cómo te sientes? (orgullo, alivio, satisfacción)
- ¿Qué puedes hacer ahora que terminaste?
- Visualiza ese momento con detalle

Abre los ojos. AHORA trabajemos para llegar allá.

¿Listo/a? 🚀"""
    }
}


ESTRATEGIAS_CONCRETO_BAJO_NIVEL = {
    "pasos_micro": {
        "nombre": "Desglose en Micro-Pasos",
        "fit": TipoFit.CONCRETO_PRECISION_MOTORA,
        "descripcion": "Divide la tarea en acciones específicas y pequeñas",
        "enfoque_recomendado": EnfoqueRegulatorio.PREVENCION_VIGILANT,
        "tareas": ["cualquiera"],
        "fases": ["ejecucion"],
        "tiempo_minimo": 10,
        "template": """Vamos a hacer esto súper simple, paso a paso. 🪜

**Tu plan de {tiempo} min:**
1. {paso_1}
2. {paso_2}
3. {paso_3}

**Importante:** Haz UNO a la vez. Cuando termines uno, táchalo. No pienses en el siguiente hasta terminar el actual.

¿Empezamos por el paso 1? ⬜→✅"""
    },
    
    "protocolo_rigido": {
        "nombre": "Protocolo Paso a Paso Riguroso",
        "fit": TipoFit.CONCRETO_PRECISION_MOTORA,
        "descripcion": "Sigue un algoritmo fijo sin desviaciones",
        "enfoque_recomendado": EnfoqueRegulatorio.PREVENCION_VIGILANT,
        "tareas": ["protocolo_lab", "coding", "resolver_problemas"],
        "fases": ["ejecucion"],
        "tiempo_minimo": 15,
        "template": """Vamos a seguir un protocolo estricto. 🧪

**Instrucciones de {tiempo} min:**
Paso 1: {paso_1_detallado}
Paso 2: {paso_2_detallado}
Paso 3: {paso_3_detallado}

**REGLAS:**
- No saltes pasos
- No improvises
- Si algo falla, anótalo y sigue

¿Entendido el protocolo? 🔬"""
    },
    
    "checklist_micro": {
        "nombre": "Checklist de Tareas Mínimas",
        "fit": TipoFit.CONCRETO_PRECISION_MOTORA,
        "descripcion": "Lista de tareas pequeñas y verificables",
        "enfoque_recomendado": EnfoqueRegulatorio.PREVENCION_VIGILANT,
        "tareas": ["cualquiera"],
        "fases": ["ejecucion", "revision"],
        "tiempo_minimo": 10,
        "template": """Aquí está tu checklist ultra-específico. ☑️

**En {tiempo} min, completa:**
☐ {item_1}
☐ {item_2}
☐ {item_3}

Marca cada ☐ cuando termines. Siente la satisfacción de cada "✓".

¿Vamos por el primero? 📝"""
    }
}


# ============================================================================
# ESTRATEGIAS MIXTAS (COMBINACIONES ESPECÍFICAS)
# ============================================================================

ESTRATEGIAS_MIXTAS = {
    # Promoción + Concreto = Velocidad con estructura
    "sprint_estructurado": {
        "nombre": "Sprint Estructurado",
        "enfoque": EnfoqueRegulatorio.PROMOCION_EAGER,
        "nivel": NivelConstruccion.CONCRETO,
        "descripcion": "Avance rápido con pasos claros",
        "tareas": ["coding", "resolver_problemas", "borrador"],
        "fases": ["ejecucion"],
        "tiempo_minimo": 15,
        "template": """Vamos a combinar velocidad con estructura. ⚡📋

**Sprint de {tiempo} min:**
1. Timer activado (sin distracciones)
2. Sigue esta secuencia EXACTA:
   - {paso_1} (5 min)
   - {paso_2} (5 min)
   - {paso_3} (5 min)
3. Si terminas antes, empieza el siguiente
4. Meta: Completar los 3 pasos

¿Listo para el sprint? 🏃‍♀️"""
    },
    
    # Prevención + Abstracto = Reflexión cautelosa
    "reflexion_cautelosa": {
        "nombre": "Reflexión Cautelosa Pre-Acción",
        "enfoque": EnfoqueRegulatorio.PREVENCION_VIGILANT,
        "nivel": NivelConstruccion.ABSTRACTO,
        "descripcion": "Planificación estratégica para evitar errores",
        "tareas": ["ensayo", "presentacion", "protocolo_lab"],
        "fases": ["planificacion"],
        "tiempo_minimo": 10,
        "template": """Antes de actuar, planifiquemos con cuidado. 🤔

**Reflexión estratégica ({tiempo} min):**
1. ¿Qué podría salir mal en este trabajo?
2. ¿Qué requisitos NO debo olvidar?
3. ¿Qué recursos necesito tener a mano?
4. Plan B si algo falla: ___

**¿Por qué esto?** Prevenir es mejor que corregir.

¿Te hace sentido? 🛡️"""
    }
}


# ============================================================================
# FUNCIONES DE SELECCIÓN DE ESTRATEGIAS
# ============================================================================

def seleccionar_estrategia(
    enfoque: EnfoqueRegulatorio,
    nivel: NivelConstruccion,
    tipo_tarea: str,
    fase: str,
    tiempo_disponible: int,
    sentimiento: Optional[str] = None
) -> Dict:
    """
    Selecciona la estrategia más apropiada según el contexto.
    
    Args:
        enfoque: Enfoque regulatorio (promoción/prevención)
        nivel: Nivel de construcción (abstracto/concreto)
        tipo_tarea: Tipo de tarea académica
        fase: Fase del trabajo (ideacion/planificacion/ejecucion/revision)
        tiempo_disponible: Minutos disponibles
        sentimiento: Sentimiento actual (opcional, para ajustes)
    
    Returns:
        Dict con la estrategia seleccionada
    """
    # Prioridad 1: Ajustar por sentimiento (regla de seguridad)
    if sentimiento in ["ansiedad_error", "baja_autoeficacia"]:
        # Forzar Prevención + Concreto para reducir ansiedad
        enfoque = EnfoqueRegulatorio.PREVENCION_VIGILANT
        nivel = NivelConstruccion.CONCRETO
    
    # Prioridad 2: Buscar en estrategias mixtas
    for key, estrategia in ESTRATEGIAS_MIXTAS.items():
        if (estrategia["enfoque"] == enfoque and 
            estrategia["nivel"] == nivel and
            tipo_tarea in estrategia["tareas"] and
            fase in estrategia["fases"] and
            tiempo_disponible >= estrategia["tiempo_minimo"]):
            return estrategia
    
    # Prioridad 3: Buscar por enfoque + compatibilidad de nivel
    if enfoque == EnfoqueRegulatorio.PROMOCION_EAGER:
        estrategias_candidatas = ESTRATEGIAS_PROMOCION_EAGER
    else:
        estrategias_candidatas = ESTRATEGIAS_PREVENCION_VIGILANT
    
    for key, estrategia in estrategias_candidatas.items():
        if (tipo_tarea in estrategia["tareas"] and
            fase in estrategia["fases"] and
            tiempo_disponible >= estrategia["tiempo_minimo"] and
            estrategia.get("nivel_recomendado") == nivel):
            return estrategia
    
    # Prioridad 4: Buscar por nivel de construcción
    if nivel == NivelConstruccion.ABSTRACTO:
        estrategias_nivel = ESTRATEGIAS_ABSTRACTO_ALTO_NIVEL
    else:
        estrategias_nivel = ESTRATEGIAS_CONCRETO_BAJO_NIVEL
    
    for key, estrategia in estrategias_nivel.items():
        if (tipo_tarea in estrategia["tareas"] or "cualquiera" in estrategia["tareas"]) and \
           (fase in estrategia["fases"] or "cualquiera" in estrategia["fases"]) and \
           tiempo_disponible >= estrategia["tiempo_minimo"]:
            return estrategia
    
    # Fallback: Estrategia genérica
    return {
        "nombre": "Estrategia Genérica",
        "template": """Entiendo cómo te sientes. Vamos a trabajar en esto juntos/as.

**En los próximos {tiempo} min:**
{accion_especifica}

¿Te parece bien empezar? 💪"""
    }


def obtener_ejemplos_estrategias(enfoque: EnfoqueRegulatorio, nivel: NivelConstruccion) -> str:
    """
    Retorna ejemplos de estrategias para el prompt del LLM.
    Ayuda a Gemini a generar respuestas más alineadas con el framework.
    """
    if enfoque == EnfoqueRegulatorio.PROMOCION_EAGER and nivel == NivelConstruccion.ABSTRACTO:
        return """
EJEMPLOS DE ESTRATEGIAS (Modo: Entusiasta + Abstracto):
- "Piensa en todas las posibilidades, sin limitarte"
- "Visualiza el resultado final que quieres lograr"
- "Conecta esto con tus metas más grandes"
- "¿Qué lograrías si esto sale genial?"
"""
    elif enfoque == EnfoqueRegulatorio.PROMOCION_EAGER and nivel == NivelConstruccion.CONCRETO:
        return """
EJEMPLOS DE ESTRATEGIAS (Modo: Entusiasta + Concreto):
- "Escribe lo más rápido que puedas, sin parar"
- "Haz 10 ejercicios en 15 minutos, cantidad es la meta"
- "Avanza aunque esté imperfecto, después pulimos"
- "Timer activado: ve cuánto avanzas en 10 min"
"""
    elif enfoque == EnfoqueRegulatorio.PREVENCION_VIGILANT and nivel == NivelConstruccion.ABSTRACTO:
        return """
EJEMPLOS DE ESTRATEGIAS (Modo: Vigilante + Abstracto):
- "¿Qué errores debes evitar en este tipo de trabajo?"
- "Reflexiona: ¿Qué requisitos son críticos?"
- "Piensa en qué podría salir mal y cómo prevenirlo"
- "¿Qué necesitas asegurar antes de empezar?"
"""
    else:  # Prevención + Concreto
        return """
EJEMPLOS DE ESTRATEGIAS (Modo: Vigilante + Concreto):
- "Paso 1: Lee la instrucción. Paso 2: Subraya palabras clave..."
- "Revisa línea por línea, sin saltar nada"
- "Usa un checklist: ☐ Gramática ☐ Formato ☐ Referencias"
- "Lee dos veces: una de corrido, otra al revés"
"""
