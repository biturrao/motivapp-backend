# app/services/ai_service.py

"""
Servicio de IA para Flou - Tutor Metamotivacional
Basado en Miele & Scholer (2016) y el modelo de Task-Motivation Fit
Usa Google Gemini 2.5 Pro para extracción de slots y generación de respuestas
"""

import logging
import re
import json
from typing import Optional, Dict, List, Tuple
import google.generativeai as genai

from app.core.config import settings
from app.schemas.chat import (
    SessionStateSchema, Slots, EvalResult,
    Sentimiento, TipoTarea, Fase, Plazo, TiempoBloque
)

logger = logging.getLogger(__name__)

# Configurar Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

# Nombre de la IA
AI_NAME = 'Flou'

# Modelo por defecto (exportado para compatibilidad con wellness.py)
model = genai.GenerativeModel('gemini-2.0-flash-exp')


# ---------------------------- PROMPT DE SISTEMA ---------------------------- #

def get_system_prompt() -> str:
    """Retorna el prompt de sistema completo para Flou"""
    return f"""
Eres {AI_NAME}, una tutora metamotivacional cercana y empática para estudiantes chilenos de educación superior.
Tu objetivo es ayudarles a encontrar el "ajuste perfecto" entre su tarea y su motivación del momento.

PERSONALIDAD Y TONO:
- Hablas como una amiga mayor que entiende la vida universitaria: cercana, validante, sin sermones
- Piensas en voz alta: "Uf, suena a que estás con el cerebro saturado..." / "Mmm, ¿sabes qué? creo que ese bloqueo viene de..."
- Celebras los pequeños logros: "¡Bacán! 🎉" / "Oye, eso que lograste no es poco..."
- Validas las emociones primero, luego ayudas: "Es súper válido sentirse así cuando..." 
- Usas lenguaje chileno natural: "bacán", "cacha", "penca", "brígido", emojis 😊🔥💪
- NO uses jerga académica ni símbolos técnicos (↑↓·) en tus respuestas
- Máximo 140 palabras, conversacional, viñetas solo cuando sea natural

ESCUCHA ACTIVA Y COMPRENSIÓN:
Cuando te cuenten algo, primero muestra que entendiste:
- "Entiendo, tienes [tarea] para [plazo] y te sientes [emoción]..."
- "Ya cacho, el tema es que [reformula su situación]..."
- Luego explica brevemente POR QUÉ se sienten así (conecta tarea con emoción)
- Recién después ofrece una micro-estrategia concreta

EXTRACCIÓN NATURAL DE INFO (no interrogues, conversa):
Necesitas saber: sentimiento, tipo_tarea, plazo, fase (ideación/planificación/ejecución/revisión), tiempo disponible
- Si falta algo crítico, pregúntalo natural: "¿Y para cuándo tienes que entregarlo?" / "¿En qué parte estás, empezando o revisando?"
- Si no responden, asume defaults razonables y avanza

ESTRATEGIAS METAMOTIVACIONALES (oculta la teoría, aplícala):
Clasifica mentalmente (NO muestres esto al usuario):
- Tareas creativas/abiertas (ensayos, esquemas, brainstorming) → enfoque "promoción": explora posibilidades, busca lo interesante
- Tareas analíticas/cerradas (revisión, problemas, código, MCQ) → enfoque "prevención": chequea errores, paso a paso seguro
- Fase temprana (ideación, planificación) → empieza por el "por qué" y criterios antes de ejecutar
- Fase tardía (ejecución, revisión) → modo "cómo": checklist concreto, urgencia controlada
- Aburrimiento → conecta con relevancia personal antes de hacer
- Ansiedad/frustración → divide en mini-pasos ultra-verificables, menos ambigüedad
- Dispersión/rumiación → acota alcance, tiempo cortito (10-12 min), tarea concretísima

FORMATO DE RESPUESTA (natural, no como formulario):
1. Validación empática + reformulación de lo que entendiste (1-2 líneas)
2. Mini-explicación del "por qué" se siente así (1 línea, conecta tarea↔emoción)
3. Estrategia concreta: UNA micro-tarea específica en 2-3 viñetas si es necesario, con tiempo sugerido (10-15 min)
4. Cierra con pregunta abierta: "¿Cómo te suena eso?" / "¿Quieres intentarlo?" / "¿Qué te hace más sentido?"

NO uses:
- ❌ "Ajuste inferido: A·↑·promoción/eager" (muy robot)
- ❌ "Mini-evaluación:" (suena a examen)
- ❌ Lenguaje técnico visible para el usuario
- ❌ Listas mecánicas sin contexto emocional

SÍ usa:
- ✅ "Creo que ese bloqueo viene de..."
- ✅ "Probemos algo: ¿qué tal si solo..."
- ✅ "Te propongo un mini-desafío de 12 min:"
- ✅ Emojis ocasionales para calidez 😊🔥💪

BUCLE ITERATIVO:
- Si hay progreso: celebra específicamente ("¡Bacán eso de [X]!") y pregunta qué sigue
- Sin progreso: ajusta la estrategia sin hacerlo obvio: "Uff, probemos desde otro ángulo..."
- Después de 3 intentos sin mejora: "Oye, ¿qué tal si antes hacemos una pausa de 3 min para [ejercicio emocional]? A veces el cerebro necesita resetear"

CRISIS (ideas suicidas, autolesión):
Si detectas riesgo vital, detén todo y di: "Oye, lo que me cuentas es muy importante. Por favor llama al 4141 (línea MINSAL), están 24/7 para ayudarte. No estás solx en esto 💙"
"""


# ---------------------------- DETECCIÓN DE CRISIS ---------------------------- #

def detect_crisis(text: str) -> bool:
    """Detecta menciones de riesgo vital"""
    crisis_regex = r'(suicid|quitarme la vida|no quiero vivir|hacerme daño|matarme)'
    return bool(re.search(crisis_regex, text, re.IGNORECASE))


# ---------------------------- EXTRACCIÓN HEURÍSTICA ---------------------------- #

def guess_plazo(text: str) -> Optional[str]:
    """Extrae plazo del texto usando heurística"""
    text_lower = text.lower()
    if re.search(r'hoy|hoy día|ahora', text_lower):
        return "hoy"
    if re.search(r'mañana|24\s*h', text_lower):
        return "<24h"
    if re.search(r'próxima semana|la otra semana|esta semana', text_lower):
        return "esta_semana"
    if re.search(r'mes|semanas|>\s*1', text_lower):
        return ">1_semana"
    return None


def guess_tipo_tarea(text: str) -> Optional[str]:
    """Extrae tipo de tarea del texto usando heurística"""
    text_lower = text.lower()
    if re.search(r'ensayo|essay', text_lower):
        return "ensayo"
    if re.search(r'esquema|outline', text_lower):
        return "esquema"
    if re.search(r'borrador|draft', text_lower):
        return "borrador"
    if re.search(r'presentaci(ón|on)|slides', text_lower):
        return "presentacion"
    if re.search(r'proof|corregir|correcci(ón|on)|edita(r|ción)', text_lower):
        return "proofreading"
    if re.search(r'mcq|alternativa(s)?|test', text_lower):
        return "mcq"
    if re.search(r'protocolo|laboratorio|lab', text_lower):
        return "protocolo_lab"
    if re.search(r'problema(s)?|ejercicio(s)?|cálculo', text_lower):
        return "resolver_problemas"
    if re.search(r'lectura|paper|art[ií]culo', text_lower):
        return "lectura_tecnica"
    if re.search(r'resumen|sintetizar', text_lower):
        return "resumen"
    if re.search(r'c(ó|o)digo|bug|programa', text_lower):
        return "coding_bugfix"
    return None


def guess_fase(text: str) -> Optional[str]:
    """Extrae fase del texto usando heurística"""
    text_lower = text.lower()
    if re.search(r'ide(a|ación)|brainstorm', text_lower):
        return "ideacion"
    if re.search(r'plan', text_lower):
        return "planificacion"
    if re.search(r'escribir|redacci(ón|on)|hacer|resolver', text_lower):
        return "ejecucion"
    if re.search(r'revis(ar|ión)|editar|proof', text_lower):
        return "revision"
    return None


def guess_sentimiento(text: str) -> Optional[str]:
    """Extrae sentimiento del texto usando heurística"""
    text_lower = text.lower()
    if re.search(r'frustra', text_lower):
        return "frustracion"
    if re.search(r'ansiedad|miedo a equivocarme|nervios', text_lower):
        return "ansiedad_error"
    if re.search(r'aburri', text_lower):
        return "aburrimiento"
    if re.search(r'dispers|rumi', text_lower):
        return "dispersion_rumiacion"
    if re.search(r'autoeficacia baja|no puedo|no soy capaz', text_lower):
        return "baja_autoeficacia"
    return None


def guess_ramo(text: str) -> Optional[str]:
    """Extrae nombre del ramo usando regex"""
    match = re.search(r'para (el |la )?([A-Za-zÁÉÍÓÚáéíóúñÑ ]{3,30})', text, re.IGNORECASE)
    if match:
        return match.group(2).strip()
    return None


# ---------------------------- EXTRACCIÓN CON LLM ---------------------------- #

async def extract_slots_with_llm(free_text: str, current_slots: Slots) -> Slots:
    """
    Extrae slots estructurados del texto libre usando Gemini 2.5 Pro
    """
    try:
        llm_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        sys_prompt = """Extrae como JSON compacto los campos del texto del usuario:
- sentimiento: aburrimiento|frustracion|ansiedad_error|dispersion_rumiacion|baja_autoeficacia|otro
- sentimiento_otro: texto libre si es "otro"
- tipo_tarea: ensayo|esquema|borrador|lectura_tecnica|resumen|resolver_problemas|protocolo_lab|mcq|presentacion|coding_bugfix|proofreading
- ramo: nombre del ramo/materia
- plazo: hoy|<24h|esta_semana|>1_semana
- fase: ideacion|planificacion|ejecucion|revision
- tiempo_bloque: 10|12|15|25

Si un campo no aparece, usa null. Responde SOLO con JSON válido, sin texto adicional."""

        user_prompt = f"""Texto del usuario: "{free_text}"

Slots actuales: {current_slots.model_dump_json()}

JSON extraído:"""

        response = llm_model.generate_content(
            f"{sys_prompt}\n\n{user_prompt}",
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=500
            )
        )
        
        raw = response.text.strip()
        
        # Extraer JSON del texto
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            parsed = json.loads(json_match.group(0))
        else:
            parsed = json.loads(raw)
        
        # Construir Slots con fallback a valores actuales
        return Slots(
            sentimiento=parsed.get('sentimiento') or current_slots.sentimiento,
            sentimiento_otro=parsed.get('sentimiento_otro') or current_slots.sentimiento_otro,
            tipo_tarea=parsed.get('tipo_tarea') or current_slots.tipo_tarea,
            ramo=parsed.get('ramo') or current_slots.ramo,
            plazo=parsed.get('plazo') or current_slots.plazo,
            fase=parsed.get('fase') or current_slots.fase,
            tiempo_bloque=parsed.get('tiempo_bloque') or current_slots.tiempo_bloque
        )
        
    except Exception as e:
        logger.warning(f"Error en extracción LLM, usando heurística: {e}")
        # Fallback a heurística
        return extract_slots_heuristic(free_text, current_slots)


def extract_slots_heuristic(free_text: str, current_slots: Slots) -> Slots:
    """Extracción heurística de slots como fallback"""
    return Slots(
        sentimiento=guess_sentimiento(free_text) or current_slots.sentimiento,
        tipo_tarea=guess_tipo_tarea(free_text) or current_slots.tipo_tarea,
        ramo=guess_ramo(free_text) or current_slots.ramo,
        plazo=guess_plazo(free_text) or current_slots.plazo,
        fase=guess_fase(free_text) or current_slots.fase,
        tiempo_bloque=current_slots.tiempo_bloque or 12
    )


# ---------------------------- CLASIFICACIÓN Q2/Q3 ---------------------------- #

def infer_q2_q3(slots: Slots) -> Tuple[str, str, str]:
    """
    Infiere Q2 (A/B), Q3 (↑/↓/mixto) y enfoque (promocion/prevencion)
    """
    # Q2: Demanda creativa (A) vs analítica (B)
    A_tasks = ["ensayo", "esquema", "borrador", "presentacion"]
    B_tasks = ["proofreading", "mcq", "protocolo_lab", "resolver_problemas", 
               "coding_bugfix", "lectura_tecnica", "resumen"]
    
    Q2 = "A"
    if slots.tipo_tarea in B_tasks:
        Q2 = "B"
    if slots.fase == "revision" or slots.plazo in ["hoy", "<24h"]:
        Q2 = "B"
    if slots.fase in ["ideacion", "planificacion"]:
        Q2 = "A"
    
    # Q3: Nivel de abstracción (↑ por qué / ↓ cómo)
    Q3 = "↓"
    if slots.fase in ["ideacion", "planificacion"]:
        Q3 = "↑"
    if slots.fase == "revision" or slots.plazo in ["hoy", "<24h"]:
        Q3 = "↓"
    
    # Mixto: ensayos suelen necesitar ambos
    if slots.tipo_tarea == "ensayo" and slots.fase in ["planificacion", "ejecucion"]:
        Q3 = "mixto"
    
    # Enfoque regulatorio
    enfoque = "promocion_eager" if Q2 == "A" else "prevencion_vigilant"
    
    return Q2, Q3, enfoque


# ---------------------------- RENDER DE ESTRATEGIA ---------------------------- #

def render_estrategia(slots: Slots, Q2: str, Q3: str) -> List[str]:
    """Genera las viñetas de estrategia según Q2/Q3"""
    bullets = []
    bloque = slots.tiempo_bloque or 12
    
    if Q2 == "B" and (Q3 == "↓" or Q3 == "mixto"):
        # Analítica/precisión
        tipo = "párrafo" if slots.tipo_tarea == "proofreading" else "sección"
        bullets.append(f"Objetivo del bloque: '0 errores' en una parte pequeña ({tipo}).")
        bullets.append(f"Checklist ({bloque - 2} min): cifras/unidades · criterios de pauta · puntuación/consistencia.")
        bullets.append("Técnica anti-ansiedad: lectura en voz alta + dedo en línea (ritmo estable).")
        return bullets
    
    if Q3 == "mixto":
        bullets.append("2′ de propósito (↑): escribe en 1 línea la pregunta central/criterio.")
        bullets.append(f"{bloque - 2}′ de 'cómo' (↓): bosquejo con 5 bullets (tesis, 2 argumentos, contraargumento, cierre).")
        bullets.append("Micro-tarea verificable: SOLO bosquejo, sin redacción fina.")
        return bullets
    
    if Q3 == "↑":
        bullets.append("2′ define el 'por qué': meta/criterio de calidad en 1 línea (foto/nota visible).")
        bullets.append(f"{bloque - 2}′ plan en 4 pasos: qué harás primero, luego, después, cierre.")
        bullets.append("Evita distracciones: temporizador + pantalla completa (sin pestañas).")
        return bullets
    
    # Q3 = "↓" genérico
    bullets.append("Delimita alcance mínimo: termina SOLO la primera micro-parte (p.ej., 1 párrafo / 5 ítems).")
    bullets.append("Checklist de 3 ítems antes de cerrar: objetivo, evidencia/criterio, revisión rápida.")
    bullets.append("Marca progreso con ✔ y detente al sonar el temporizador.")
    return bullets


def limit_words(text: str, max_words: int = 140) -> str:
    """Limita el texto a N palabras"""
    words = text.split()
    if len(words) <= max_words:
        return text
    return ' '.join(words[:max_words]) + '…'


def render_tutor_turn(session: SessionStateSchema) -> str:
    """
    Ya no renderiza la plantilla técnica visible. 
    El LLM genera respuestas naturales y conversacionales siguiendo el nuevo system prompt.
    Esta función queda como placeholder para mantener compatibilidad.
    """
    # La estrategia ahora la genera directamente el LLM de forma conversacional
    # No mostramos el formato técnico al usuario
    return ""


# ---------------------------- DERIVACIÓN EMOCIONAL ---------------------------- #

def emotional_fallback(sentimiento: Optional[str]) -> str:
    """Genera respuesta de derivación a regulación emocional"""
    if sentimiento == "ansiedad_error":
        bullets = [
            "Respiración 4-4-4 durante 2′ (inhalar 4, sostener 4, exhalar 4).",
            "Define un puente de retorno: reanuda con 1 micro-parte concreta (p.ej., primer párrafo).",
            "Programa un bloque de 10–12 min con la sub-tarea mínima."
        ]
    elif sentimiento in ["frustracion", "dispersion_rumiacion"]:
        bullets = [
            "Anclaje 5-4-3-2-1 (3′) para bajar rumiación.",
            "Reformula sub-meta en 1 línea (resultado observable).",
            "Reinicia con bloque 10–12 min en la sub-tarea más pequeña."
        ]
    else:
        bullets = [
            "Micro-relevancia: escribe en 1 línea '¿para qué me sirve esto hoy?'.",
            "Activación conductual: empieza 2′ cronometrados (cualquier avance cuenta).",
            "Sigue con bloque 10–12 min acotado."
        ]
    
    head = "**Derivación a regulación emocional (3 ciclos sin progreso)**"
    estrategia = '\n'.join([f"- {b}" for b in bullets])
    tail = "- **Mini-evaluación:** ¿Se movió tu sensación (↑, =, ↓)? Retomamos la tarea con el plan propuesto."
    
    return limit_words(f"{head}\n\n{estrategia}\n{tail}", 140)


# ---------------------------- ORQUESTADOR PRINCIPAL ---------------------------- #

async def handle_user_turn(session: SessionStateSchema, user_text: str, context: str = "") -> Tuple[str, SessionStateSchema]:
    """
    Orquestador principal del flujo metamotivacional.
    Retorna (respuesta_texto, session_actualizada)
    """
    
    # 1) Crisis
    if detect_crisis(user_text):
        crisis_msg = "Escucho que estás en un momento muy difícil. Por favor, busca apoyo inmediato: **llama al 4141** (línea gratuita y confidencial del MINSAL). No estás sola/o."
        return crisis_msg, session
    
    # 2) Saludo único
    if not session.greeted:
        session.greeted = True
        welcome = f"¿Cómo está tu motivación hoy? Puedes elegir un sentimiento o describirlo con tus palabras:\n\n" \
                  f"Aburrimiento/desconexión · Frustración/atasco · Ansiedad por error · Dispersión/rumiación · Baja autoeficacia · Otro"
        return welcome, session
    
    # 3) Extracción de slots
    try:
        new_slots = await extract_slots_with_llm(user_text, session.slots)
    except Exception as e:
        logger.error(f"Error en extracción de slots: {e}")
        new_slots = extract_slots_heuristic(user_text, session.slots)
    
    session.slots = new_slots
    
    # 4) Si falta dato clave, preguntar
    missing = []
    if not new_slots.fase:
        missing.append("fase")
    if not new_slots.plazo:
        missing.append("plazo")
    if not new_slots.tiempo_bloque:
        missing.append("tiempo_bloque")
    
    if missing:
        priority = ["fase", "plazo", "tiempo_bloque"]
        want = next((k for k in priority if k in missing), None)
        
        if want == "fase":
            q = "Para ajustar bien la estrategia, ¿en qué fase estás: ideación, planificación, ejecución/redacción o revisión?"
        elif want == "plazo":
            q = "¿Para cuándo es? hoy, <24 h, esta semana o >1 semana?"
        else:
            q = "¿Cuánto bloque quieres hoy: 10, 12, 15 o 25 minutos?"
        
        return q, session
    
    # Defaults prudentes
    if not new_slots.tiempo_bloque:
        new_slots.tiempo_bloque = 12
        session.slots.tiempo_bloque = 12
    
    # 5) Inferir Q2, Q3, enfoque
    Q2, Q3, enfoque = infer_q2_q3(new_slots)
    session.Q2 = Q2
    session.Q3 = Q3
    session.enfoque = enfoque
    session.tiempo_bloque = new_slots.tiempo_bloque
    
    if not session.sentimiento_inicial and new_slots.sentimiento:
        session.sentimiento_inicial = new_slots.sentimiento
    
    session.sentimiento_actual = new_slots.sentimiento or session.sentimiento_actual
    
    # 6) Derivación emocional si ≥3 iteraciones sin progreso
    if session.iteration >= 3:
        if session.last_eval_result and session.last_eval_result.cambio_sentimiento != "↓":
            reply = emotional_fallback(new_slots.sentimiento)
            session.iteration = 0  # Reset
            return reply, session
    
    # 7) Generar respuesta conversacional con el LLM
    # El LLM tiene toda la info en el system prompt para generar respuestas naturales
    try:
        llm_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Construir contexto para el LLM
        contexto_interno = f"""
Info de la sesión (NO muestres esto al usuario, úsalo para entender):
- Sentimiento: {new_slots.sentimiento or 'no especificado'}
- Tarea: {new_slots.tipo_tarea or 'sin especificar'} ({new_slots.ramo or 'sin ramo'})
- Plazo: {new_slots.plazo or 'sin especificar'}
- Fase: {new_slots.fase or 'sin especificar'}
- Tiempo disponible: {new_slots.tiempo_bloque or 12} min
- Clasificación interna: Q2={Q2}, Q3={Q3}, enfoque={enfoque}
- Iteración: {session.iteration + 1}
- Contexto adicional: {context if context else 'ninguno'}

Usuario dice: "{user_text}"

Responde de forma natural, empática y conversacional siguiendo las instrucciones del system prompt.
"""
        
        chat = llm_model.start_chat(history=[])
        response = chat.send_message(contexto_interno)
        reply = response.text.strip()
        
        # Limitar palabras
        reply = limit_words(reply, 140)
        
    except Exception as e:
        logger.error(f"Error generando respuesta conversacional: {e}")
        # Fallback simple
        reply = f"Entiendo que te sientes {new_slots.sentimiento or 'complicadx'} con esto. ¿Me cuentas un poco más de qué necesitas hacer?"
    
    session.iteration += 1
    session.last_strategy = reply
    
    return reply, session


# ---------------------------- FUNCIONES AUXILIARES ---------------------------- #

async def generate_chat_response(user_message: str, context: Optional[str] = None) -> str:
    """
    LEGACY: Mantiene compatibilidad con código anterior.
    No usa el sistema metamotivacional completo.
    """
    logger.warning("Usando generate_chat_response legacy - considera migrar a handle_user_turn")
    
    try:
        llm_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        full_prompt = get_system_prompt() + "\n\n"
        if context:
            full_prompt += f"{context}\n\n"
        full_prompt += f"El usuario pregunta: \"{user_message}\""
        
        response = llm_model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=300
            )
        )
        
        return response.text
        
    except Exception as error:
        logger.error(f"Error en la llamada a Gemini: {error}")
        return "Lo siento, tuve un problema para procesar tu solicitud. Por favor, intenta de nuevo."


async def generate_profile_summary(profile: dict) -> str:
    """Genera un resumen del perfil del usuario usando Gemini"""
    try:
        llm_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        summary_prompt = f"""
### Rol
Eres {AI_NAME}, un asistente de IA empático y perspicaz. Tu objetivo es analizar los datos del perfil de un usuario y generar un resumen breve (2-3 frases), positivo y constructivo.

### Tarea
Basado en los siguientes datos del perfil en formato JSON, crea un resumen que destaque sutilmente sus fortalezas o áreas de autoconocimiento, sin sonar clínico ni crítico. El tono debe ser de apoyo, como una reflexión amigable. No menciones los datos directamente, sino la idea que transmiten.

### Ejemplo
- Si el usuario trabaja y tiene responsabilidades familiares, podrías decir: "Veo que gestionas múltiples responsabilidades, lo que habla de tu gran capacidad de organización y compromiso."
- Si el usuario menciona seguimiento en salud mental, podrías decir: "Es valiente y muy positivo que te ocupes activamente de tu bienestar emocional."

### Datos del Perfil del Usuario:
{json.dumps(profile, indent=2, ensure_ascii=False)}

### Tu Resumen:
"""
        
        response = llm_model.generate_content(
            summary_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=200
            )
        )
        
        return response.text
        
    except Exception as error:
        logger.error(f"Error al generar el resumen del perfil: {error}")
        return ""

