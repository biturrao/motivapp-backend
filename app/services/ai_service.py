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
# Usando gemini-2.0-flash-exp por ser rápido, económico y preciso para JSON
model = genai.GenerativeModel('gemini-2.0-flash-exp')


# ---------------------------- PROMPT DE SISTEMA ---------------------------- #

def get_system_prompt() -> str:
    """Retorna el prompt de sistema completo para Flou"""
    return f"""
Eres {AI_NAME}, una tutora de motivación que ayuda a estudiantes universitarios.

TU PERSONALIDAD:
- Hablas de forma cercana y amigable, como una compañera mayor
- Eres empática y validas las emociones antes de dar consejos
- Explicas todo con lenguaje simple y cotidiano
- NO uses términos académicos complicados ni símbolos extraños (evita: ↑↓·→)
- Usa emojis ocasionales para dar calidez 😊

TU OBJETIVO:
Ayudar al estudiante a encontrar la mejor forma de trabajar según:
1. Cómo se siente ahora (aburrido, ansioso, frustrado, etc.)
2. Qué tiene que hacer (ensayo, ejercicios, lectura, etc.)
3. Para cuándo lo necesita
4. En qué etapa está (empezando, haciendo, revisando)

CÓMO DAS CONSEJOS:
1. Primero valida su emoción: "Entiendo que te sientas así cuando..."
2. Explica brevemente POR QUÉ puede sentirse así
3. Da UNA estrategia concreta y específica (no listas genéricas)
4. La estrategia debe tener:
   - Una tarea pequeña y clara que puede hacer YA
   - Tiempo sugerido realista (10-25 minutos)
   - Cómo sabrá que terminó
5. Termina con una pregunta abierta para seguir conversando

EJEMPLOS DE BUEN CONSEJO:

Mal: "Delimita alcance mínimo: termina SOLO la primera micro-parte"
Bien: "¿Qué tal si solo escribes las 3 ideas principales en bullets? Sin redactar nada, solo las ideas clave. Unos 10 minutos. Cuando tengas esas 3 ideas, ya avanzaste."

Mal: "Checklist de 3 ítems antes de cerrar: objetivo, evidencia/criterio"
Bien: "Revisa solo la primera página buscando estos 3 puntos: ¿tiene sentido cada oración? ¿las palabras están bien escritas? ¿usaste bien las comas? 12 minutos, página por página."

REGLAS IMPORTANTES:
- Responde en español normal de Chile (no jergas ni modismos)
- Máximo 200 palabras por respuesta (puedes extenderte si es necesario explicar bien)
- Si detectas riesgo de suicidio, di: "Por favor llama al 4141 (línea MINSAL gratuita). Están para ayudarte 24/7"
- Mantén la conversación fluida, recuerda lo que el estudiante te contó antes
- Adapta tus consejos a lo que ya han intentado juntos
- NUNCA muestres al usuario cosas técnicas como "Ajuste inferido: A·↑" o símbolos como ↑↓·→
- NO uses plantillas visibles, habla naturalmente

Cómo estructurar tu respuesta:

- Dale una **estrategia concreta** (máximo 3 pasos simples) con UNA sub-tarea verificable (p.ej., "solo escribe 5 ideas principales" / "solo haz la Introducción" / "solo resuelve 5 ejercicios").

- Sugiere un **bloque de tiempo corto:** 12–15 min (o el tiempo que el estudiante indicó).

- **Pregúntale cómo le fue:** Al final, pregunta si logró la tarea y cómo se siente ahora.

- Cierra con una pregunta amigable para mantener la conversación.

RECUERDA: NO muestres clasificaciones técnicas (A, B, ↑, ↓, promoción, prevención, etc.) al usuario.

RESPONDE SIEMPRE DE FORMA NATURAL Y CONVERSACIONAL.
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
    
    # HOY (urgente, inmediato)
    if re.search(r'\bhoy\b|hoy d(í|i)a|\bahora\b|\burgente\b|\binmediato\b|\bya\b|al tiro|en este momento|\bpronto\b|cuanto antes', text_lower):
        return "hoy"
    
    # MENOS DE 24H (mañana)
    if re.search(r'\bma(ñ|n)ana\b|24\s*h(oras)?|para ma(ñ|n)|en un d(í|i)a|pasado ma(ñ|n)ana', text_lower):
        return "<24h"
    
    # ESTA SEMANA (días cercanos)
    if re.search(r'pr(ó|o)xima semana|la otra semana|esta semana|en unos d(í|i)as|en pocos d(í|i)as|esta week|fin de semana|para el (lunes|martes|miércoles|jueves|viernes)', text_lower):
        return "esta_semana"
    
    # MÁS DE 1 SEMANA (largo plazo)
    if re.search(r'\bmes\b|semanas|pr(ó|o)ximo mes|m(á|a)s adelante|largo plazo|tengo tiempo|no es urgente|con calma|para el otro mes', text_lower):
        return ">1_semana"
    
    return None


def guess_tipo_tarea(text: str) -> Optional[str]:
    """Extrae tipo de tarea del texto usando heurística - PRUDENTE: solo clasifica cuando hay evidencia clara"""
    text_lower = text.lower()
    
    # ORDEN IMPORTANTE: De más específico a más general
    
    # 1. Debugging/bugfix (MUY ESPECÍFICO - requiere mención explícita de bug/error)
    if re.search(r'\bbug\b|\berror\b|debug|arreglar.*c(ó|o)digo|corregir.*c(ó|o)digo|\bfix\b.*code', text_lower):
        return "coding_bugfix"
    
    # 2. Revisión/corrección de texto (antes de ensayo)
    if re.search(r'\bcorregir\b|\brevis(ar|ión)\b.*\b(texto|ensayo|escrito|trabajo)|proof|edita(r|ción)|pulir|mejorar\s+(el|mi)\s+(texto|ensayo)', text_lower):
        return "proofreading"
    
    # 3. Ensayo (escritura creativa/argumentativa)
    if re.search(r'\bensayo\b|\bessay\b|redacci(ón|on)\s+de|escribir\s+(un|una)\s+(ensayo|essay|composición|trabajo\s+escrito)|composici(ó|on)\s+argumentativa', text_lower):
        return "ensayo"
    
    # 4. Borrador (versión preliminar)
    if re.search(r'\bborrador\b|\bdraft\b|primera?\s+(versi(ó|o)n|intento)|versi(ó|o)n\s+(inicial|preliminar)', text_lower):
        return "borrador"
    
    # 5. Esquema/estructura (antes de empezar a escribir)
    if re.search(r'\besquema\b|\boutline\b|estructura\s+(de|del|para)|mapa\s+(conceptual|mental)|diagrama\s+de', text_lower):
        return "esquema"
    
    # 6. Presentación (slides, exposición)
    if re.search(r'presentaci(ó|o)n|\bslides?\b|\bppt\b|powerpoint|exposici(ó|o)n|\bdisertaci(ó|o)n\b|preparar.*presentar', text_lower):
        return "presentacion"
    
    # 7. Examen/Test (pruebas con alternativas)
    if re.search(r'\bmcq\b|alternativas?|\btest\b|\bprueba\b|\bexamen\b|\bquiz\b|cuestionario|evaluaci(ó|o)n.*alternativas', text_lower):
        return "mcq"
    
    # 8. Protocolo de laboratorio
    if re.search(r'protocolo\s+(de\s+)?lab|laboratorio|experimento|pr(á|a)ctica\s+(de\s+)?lab|informe\s+de\s+lab', text_lower):
        return "protocolo_lab"
    
    # 9. Resolver problemas/ejercicios (matemática, física, etc.)
    if re.search(r'\bproblemas?\b.*resolver|\bejercicios?\b|c(á|a)lculo|matem(á|a)tica|\bgu(í|i)a\b.*ejercicios|resolver.*(gu(í|i)a|tarea|problemas)|problemas?.*de', text_lower):
        return "resolver_problemas"
    
    # 10. Lectura técnica/académica
    if re.search(r'\bleer\b.*(paper|art(í|i)culo|texto|cap(í|i)tulo)|\bpaper\b|art(í|i)culo.*cient(í|i)fico|lectura.*t(é|e)cnica|estudiar.*(texto|libro|cap(í|i)tulo)', text_lower):
        return "lectura_tecnica"
    
    # 11. Resumen/síntesis
    if re.search(r'\bresumen\b|sintetizar|resumir|s(í|i)ntesis\s+de|extracto|hacer.*resumen', text_lower):
        return "resumen"
    
    # 12. Programación/desarrollo (GENÉRICO - solo si menciona programar pero NO bug)
    # Este va al FINAL porque es muy general
    if re.search(r'\bprogramar\b|\bc(ó|o)digo\b|\bscript\b|desarrollo.*software|implementar.*c(ó|o)digo|crear.*(programa|aplicaci(ó|o)n)', text_lower):
        # Verificar que NO sea bug (ya lo detectamos arriba)
        if not re.search(r'\bbug\b|\berror\b|debug|arreglar|corregir.*c(ó|o)digo', text_lower):
            return "coding_bugfix"  # Usar mismo tipo para programación general
    
    # Si no hay coincidencia clara, retornar None (mejor que adivinar)
    return None


def guess_fase(text: str) -> Optional[str]:
    """Extrae fase del texto usando heurística"""
    text_lower = text.lower()
    
    # IDEACIÓN (generación de ideas, brainstorming)
    if re.search(r'\bide(a|ación)\b|\bbrainstorm|\bpensar\b.*ideas|ocurrencia|inspiraci(ó|o)n|empezar.*idea|comenzar.*idea|\binicio\b|pensando.*tema|buscar.*tema|no s(é|e).*qu(é|e).*escribir', text_lower):
        return "ideacion"
    
    # PLANIFICACIÓN (organizar, estructurar antes de ejecutar)
    if re.search(r'\bplan(ear)?\b|\borganizar\b|\bestructurar\b|esquematizar|\bpreparar\b|definir.*estructura|hacer.*esquema|armar.*(plan|estructura)|antes de empezar', text_lower):
        return "planificacion"
    
    # EJECUCIÓN (haciendo el trabajo, en pleno proceso)
    if re.search(r'\bescribir\b|\bescribiendo\b|redacci(ó|o)n|\bhacer\b|\bhaciendo\b|\bresolver\b|\bresolviendo\b|\bejecutar\b|desarrollar|\btrabajando\b|en proceso|a mitad|avanzando', text_lower):
        return "ejecucion"
    
    # REVISIÓN (corregir, editar, terminar detalles)
    if re.search(r'\brevis(ar|ión)\b|\beditar\b|\bproof\b|\bcorregir\b|verificar|chequear|\bpulir\b|\bterminar\b.*detalles|ya.*casi|falta poco|\bfinal(es|izar)?\b|última.*revisi(ó|o)n', text_lower):
        return "revision"
    
    return None


def guess_sentimiento(text: str) -> Optional[str]:
    """Extrae sentimiento del texto usando heurística"""
    text_lower = text.lower()
    
    # FRUSTRACIÓN (enojo, rabia, impotencia)
    if re.search(r'\bfrustra(do|da|ción)?\b|\benoja(do|da)?\b|\birrita(do|da)?\b|\bmolesta(do|da)?\b|\brabia\b|\bbronca\b|\bimpotente\b|\bharto\b|\bcansa(do|da)\b.*intentar|no.*sale|no.*funciona.*nada', text_lower):
        return "frustracion"
    
    # ANSIEDAD/MIEDO A ERROR (nervioso, estresado, presión)
    if re.search(r'\bansiedad\b|\bansioso\b|\bansiosa\b|miedo.*equivocar|\bnervios\b|\bnervioso\b|\bnerviosa\b|\bestresa(do|da)\b|\bagobia(do|da)\b|\bpresiona(do|da)\b|\btenso\b|\btensa\b|\bp(á|a)nico\b|\bpreocupa(do|da)\b|miedo.*fallar|miedo.*mal', text_lower):
        return "ansiedad_error"
    
    # ABURRIMIENTO (latero, sin ganas, desganado)
    if re.search(r'\baburri(do|da|miento)?\b|\blatero\b|\blatera\b|\bflojo\b|\bfloja\b|sin ganas|\bdesgana(do|da)\b|\bmon(ó|o)tono\b|poco.*motivado|\bdesmotiva(do|da)\b|no.*interesa|\bpaja\b.*hacer', text_lower):
        return "aburrimiento"
    
    # DISPERSIÓN/RUMIACIÓN (distraído, no puedo concentrarme)
    if re.search(r'\bdispers(o|a|ión)?\b|\brumi(a|ación)?\b|\bdistra(í|i)(do|da)\b|no.*concentr(o|ar)|pensando en otra|no.*enfoco|\bmente.*vuela\b|\bdesconcentra(do|da)\b|mil.*cosas.*cabeza|no.*paro.*pensar', text_lower):
        return "dispersion_rumiacion"
    
    # BAJA AUTOEFICACIA (no puedo, no soy capaz, inseguro)
    if re.search(r'autoeficacia baja|\bno puedo\b|no soy capaz|\bincapaz\b|\binseguro\b|\binsegura\b|\bdudo\b|no creo poder|no.*voy.*lograr|no.*soy.*bueno|\bmal(o|a)\b.*esto|no.*sirvo', text_lower):
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
    Extrae slots estructurados del texto libre usando Gemini Flash
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

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        response = llm_model.generate_content(
            f"{sys_prompt}\n\n{user_prompt}",
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=500
            ),
            safety_settings=safety_settings
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


# ---------------------------- FALLBACK INTELIGENTE (NLU ROBUSTO) ---------------------------- #

def _detect_intent(user_text: str) -> str:
    """Detecta la intención del usuario con múltiples patrones (estilo NLU municipal)"""
    text_lower = user_text.lower()
    
    # Intención: Saludo
    if re.search(r'\b(hola|holi|buenas|buenos días|buenas tardes|hey|hi)\b', text_lower):
        return "saludo"
    
    # Intención: Celebrar logro / cierre positivo
    if re.search(r'(termin[ée]|lo logr[ée]|listo|ya acab[ée]|me result[óo]|qued[óo] bien)', text_lower):
        return "celebrar_logro"
    
    # Intención: Baja energía física o mental
    if re.search(r'(sin energ[íi]a|sin pilas|cansad[oa]|agotad[oa]|no tengo fuerzas|no me da el cuerpo|estoy molid[oa])', text_lower):
        return "baja_energia"
    
    # Intención: Necesita pausa breve
    if re.search(r'(necesito (una )?pausa|quiero descansar|dame un respiro|break|respiro corto|descansar un rato)', text_lower):
        return "necesito_pausa"
    
    # Intención: Cambio explícito de estrategia
    if re.search(r'(otra estrategia|cambiemos de plan|algo distinto|no me sirve lo anterior|dame otra idea|reencuadra|reencuadre)', text_lower):
        return "cambio_estrategia"
    
    # Intención: Derivar a bienestar/ejercicios regulatorios
    if re.search(r'(bienestar|mindfulness|respiraci[óo]n guiada|ejercicio de respiraci[óo]n|meditaci[óo]n corta|relajarme un poco)', text_lower):
        return "derivar_bienestar"
    
    # Intención: Solicitud de ayuda
    if re.search(r'\b(ayuda|ayúdame|necesito|auxilio|socorro)\b', text_lower):
        return "solicitud_ayuda"
    
    # Intención: Describiendo problema/tarea
    if re.search(r'\b(tengo que|debo|tarea|trabajo|proyecto|actividad|pendiente)\b', text_lower):
        return "describir_tarea"
    
    # Intención: Confusión / no saber cómo avanzar
    if re.search(r'(no s[ée] (c[óo]mo|por d[óo]nde)|estoy perdid[oa]|no entiendo nada|no me resulta ninguna estrategia)', text_lower):
        return "confusion"
    
    # Intención: Expresando emoción
    if re.search(r'\b(siento|me siento|estoy|ando|estoy pasando)\b.*(mal|bien|triste|feliz|ansioso|estresado|frustrado|aburrido)', text_lower):
        return "expresar_emocion"
    
    # Intención: Preguntando cómo usar el servicio
    if re.search(r'\b(cómo|como).*(funciona|usar|utilizar|trabaja|ayuda)\b', text_lower):
        return "consulta_servicio"
    
    # Intención: Agradecimiento
    if re.search(r'\b(gracias|muchas gracias|te agradezco|thanks)\b', text_lower):
        return "agradecimiento"
    
    return "general"


def _generate_fallback_response(slots: Slots, user_text: str) -> str:
    """
    Sistema de fallback robusto tipo NLU municipal con estrategias metamotivacionales
    Basado en Miele & Scholer (2016): Task-Motivation Fit
    Garantiza SIEMPRE una respuesta útil usando cascada de estrategias
    """
    
    # Nivel 1: Detectar intención y responder según ella
    intent = _detect_intent(user_text)
    
    if intent == "saludo":
        return f"¡Hola! 😊 Soy {AI_NAME}, tu asistente metamotivacional. Estoy aquí para ayudarte con tus tareas y encontrar la mejor forma de trabajar. ¿Qué necesitas hacer hoy?"
    
    elif intent == "celebrar_logro":
        return "¡Qué seco! 🙌 Me alegra que hayas avanzado. Si quieres, cuéntame cómo te sientes ahora o qué tarea sigue y ajustamos otra estrategia." 
    
    elif intent == "agradecimiento":
        return "¡De nada! 😊 Me alegra poder ayudarte. Si necesitas más apoyo o una nueva estrategia, aquí estoy. ¿Hay algo más en lo que pueda ayudarte?"
    
    elif intent == "consulta_servicio":
        return f"Soy {AI_NAME}, tu asistente de motivación. Te ayudo a encontrar la mejor forma de trabajar según cómo te sientas y qué tengas que hacer. Solo cuéntame qué tarea tienes pendiente y cómo te sientes, y yo te daré una estrategia concreta. ¿Qué necesitas hacer?"
    
    elif intent == "solicitud_ayuda":
        return "Aquí estoy. Para darte una estrategia precisa necesito dos cosas: qué tarea tienes pendiente y cómo anda tu motivación (ansioso, aburrido, frustrado, etc.). Cuéntame eso y armamos un plan pequeño." 
    
    elif intent == "describir_tarea":
        if not slots.sentimiento:
            return "Perfecto, ya sé qué tienes que hacer. Ahora dime cómo te sientes con esa tarea para decidir si vamos por un enfoque de promoción (ideas nuevas) o de prevención (cerrar pendientes)."
        if not slots.plazo:
            return "Entendido el tipo de tarea. ¿Para cuándo la necesitas? Según el plazo defino si conviene una estrategia corta o algo más exploratorio."
        # Si ya tenemos emoción y plazo, seguir flujo normal
    
    elif intent == "baja_energia":
        return "Si la energía está al piso, primero necesitamos micro-recarga. Haz un break muy concreto: levántate, toma agua y haz 5 respiraciones profundas enfocándote en alargar la exhalación. Eso activa el modo recuperación y después retomamos con un bloque de 10 minutos. ¿Te resulta?"
    
    elif intent == "necesito_pausa":
        return "Vale, escucho que tu mente pide una pausa. Las teorías de metamotivación dicen que cambiar brevemente a modo restaurativo evita el desgaste. Haz 3 minutos de respiración cuadrada (inhala 4s, mantén 4, exhala 4, mantén 4) y vuelve para contarme cómo te sientes."
    
    elif intent == "cambio_estrategia":
        return 'Probemos un reencuadre. Cuando una táctica no engancha, cambiamos el nivel de abstracción: si estabas pensando en el "por qué", bajemos al "cómo" con un micro-paso verificable (ej: solo abre el doc y escribe el título). ¿Quieres que te proponga uno nuevo según tu tarea?'
    
    elif intent == "derivar_bienestar":
        return 'Puedo guiarte a la sección de Bienestar cuando quieras. Solo dime "Quiero probar un ejercicio de bienestar" y te mando directo a los ejercicios de respiración, grounding y mindfulness para resetear.'
    
    elif intent == "confusion":
        return 'Ok, cuando todo se siente nebuloso aplicamos el principio de "elige un criterio". Dime qué etapa te confunde más (empezar, seguir o revisar) y te propongo un paso concreto para despejar el panorama.'
    
    elif intent == "expresar_emocion":
        # Detectar qué emoción mencionó y dar estrategia metamotivacional
        sentimiento = guess_sentimiento(user_text)
        if sentimiento:
            return _get_strategy_by_emotion(sentimiento, slots)
        return "Entiendo. A veces es difícil concentrarse o encontrar motivación. ¿Qué tipo de trabajo tienes que hacer? Así puedo darte una estrategia concreta."

    # Nivel 2: Estrategias metamotivacionales por COMBINACIÓN de factores
    if slots.tipo_tarea and slots.sentimiento:
        strategy = _get_metamotivational_strategy(slots)
        if strategy:
            return strategy
    
    # Nivel 2b: Detectar desajuste motivacional (Task-Motivation Fit)
    fit_gap = _detect_fit_gap(slots)
    if fit_gap:
        return fit_gap
    
    # Nivel 3: Si tenemos tipo de tarea pero no sentimiento, dar estrategia general por tarea
    if slots.tipo_tarea:
        estrategias = _get_task_strategies()
        estrategia = estrategias.get(slots.tipo_tarea, None)
        if estrategia:
            return f"Entiendo. {estrategia}"
    
    # Nivel 4: Detectar palabras clave en el texto actual para dar respuesta contextual
    if re.search(r'\b(programar|código|chatbot|app|software)\b', user_text.lower()):
        return "Enfoquemos la programación en micro-tramos: elige UNA funcionalidad pequeña, abre el archivo y deja solo lo necesario para esa parte. Trabaja 18 minutos, prueba lo que hiciste y luego me cuentas si necesitas otro ajuste."
    
    if re.search(r'\b(leer|estudiar|libro|paper|artículo)\b', user_text.lower()):
        return "Para lectura técnica usa modo barrido: cronometra 12 minutos, subraya solo ideas fuerza y deja un post-it con la duda más grande. Así mantenemos foco sin agobiarnos."
    
    if re.search(r'\b(escribir|ensayo|texto|redactar)\b', user_text.lower()):
        return "Vamos con escritura guiada: escribe tres bullets con idea principal, ejemplo y frase de cierre. Nada de redactar completo todavía; solo estructura rápida en 10 minutos y luego vemos si extendemos."
    
    if re.search(r'\b(ejercicio|problema|matemática|física|cálculo)\b', user_text.lower()):
        return "Divide los ejercicios en un lote mínimo: resuelve solo 2-3 problemas gemelos, anota los pasos clave y detente para revisar patrones. 15 minutos bastan para destrabar."
    
    # Nivel 5: Respuesta genérica pero útil (siempre funciona)
    return (
        f"Vamos directo a la acción. Haz este micro-plan estándar:\n"
        "1. Anota en un post-it qué quieres dejar listo en los próximos 12 minutos.\n"
        "2. Trabaja ese bloque con el celular lejos y enfócate solo en completar ese mini entregable.\n"
        "3. Al terminar, marca lo logrado y dime si necesitamos cambiar la táctica."
    )


def _get_strategy_by_emotion(sentimiento: str, slots: Slots) -> str:
    """Estrategias específicas por emoción según teoría metamotivacional"""
    
    if sentimiento == "aburrimiento":
        # Aburrimiento = tarea poco desafiante → incrementar desafío o variar
        if slots.plazo in ["hoy", "<24h"]:
            return "Entiendo que te sientas aburrido. Cuando las tareas son urgentes y aburridas, ayuda hacerlas en sprints cortos. Te propongo: trabaja 15 minutos intensos, descansa 5, y repite. El tiempo límite hace que sea menos monótono. ¿Qué parte puedes hacer primero?"
        else:
            return "Entiendo que te sientas aburrido. El aburrimiento aparece cuando las tareas son poco desafiantes. ¿Qué tal si te pones un pequeño reto? Por ejemplo: termina una sección específica en 20 minutos. Tener un límite lo hace más interesante. ¿Qué tarea tienes?"
    
    elif sentimiento == "ansiedad_error":
        # Ansiedad = miedo a equivocarse → reducir stakes, enfoque en proceso
        return "Entiendo tu ansiedad. Cuando nos presionamos mucho, ayuda cambiar el enfoque: en vez de buscar perfección, busca PROGRESO. Te propongo: haz una versión 'borrador terrible' primero. Sin juzgar. Solo avanza 15 minutos. Después puedes mejorar. ¿Qué tarea es?"
    
    elif sentimiento == "frustracion":
        # Frustración = tarea muy difícil o bloqueado → simplificar, bajar nivel
        return "Entiendo tu frustración. A veces nos trabamos porque la tarea es muy grande o compleja. Te sugiero: divide en la PARTE MÁS PEQUEÑA posible. ¿Cuál es el primer micro-paso que puedes hacer en 10 minutos? No importa qué tan pequeño sea. ¿Qué estás intentando hacer?"
    
    elif sentimiento == "dispersion_rumiacion":
        # Dispersión = distracción/rumiación → tareas concretas, externos
        return "Entiendo que te cueste concentrarte. Cuando la mente divaga, ayuda tener tareas MUY concretas y mecánicas. Te propongo: haz algo que no requiera pensar mucho, como organizar materiales, copiar citas, o hacer un esquema simple. 10 minutos. ¿Qué tarea tienes pendiente?"
    
    elif sentimiento == "baja_autoeficacia":
        # Baja autoeficacia = duda de capacidad → éxitos pequeños, validación
        return "Entiendo que dudes de ti. Cuando nos sentimos así, necesitamos victorias pequeñas. Te propongo: elige la parte MÁS FÁCIL de tu tarea y hazla primero. Sin importar cuán simple sea. Cuando la termines, sentirás que sí puedes. ¿Cuál es la parte más fácil de lo que tienes que hacer?"
    
    return "Entiendo cómo te sientes. Cuéntame qué tarea tienes que hacer y busquemos juntos una forma de avanzar que se ajuste a cómo te sientes ahora."


def _get_metamotivational_strategy(slots: Slots) -> Optional[str]:
    """
    Genera estrategias basadas en AJUSTE (FIT) metamotivacional
    Combina: tipo_tarea × sentimiento × fase × plazo
    """
    
    tarea = slots.tipo_tarea
    sent = slots.sentimiento
    fase = slots.fase
    plazo = slots.plazo
    
    # ENSAYOS - Tareas creativas de alto nivel
    if tarea == "ensayo":
        if sent == "aburrimiento":
            if fase == "ideacion":
                return "Entiendo que te aburra pensar en el ensayo. Te propongo algo diferente: en vez de 'ideas', escribe 3 preguntas provocadoras sobre el tema. Preguntas que te den curiosidad. 10 minutos. Las ideas fluyen mejor así. ¿Cuál es el tema?"
            else:
                return "Entiendo que te aburra escribir. Prueba esto: escribe como si le explicaras el tema a un niño de 10 años. Sin términos técnicos, solo ideas simples. 15 minutos. Es más entretenido y después lo formalizas. ¿De qué es el ensayo?"
        
        elif sent == "ansiedad_error":
            return "Entiendo tu ansiedad con el ensayo. La presión por hacerlo perfecto paraliza. Te propongo: escribe un 'brain dump' terrible. Vomita todas las ideas sin estructura, sin gramática, sin nada. 15 minutos. Después ordenas. ¿Cuál es el tema?"
        
        elif sent == "frustracion":
            if fase in ["ideacion", "planificacion"]:
                return "Entiendo tu frustración. Cuando nos trabamos pensando, ayuda hacer algo concreto. Te sugiero: solo haz un esquema de 3 puntos: Inicio, Medio, Final. Sin desarrollar. 10 minutos. ¿De qué es el ensayo?"
            else:
                return "Entiendo tu frustración con el ensayo. Cuando nos trabamos escribiendo, ayuda cambiar de sección. ¿Hay alguna parte del ensayo que sea más fácil o que te guste más? Empieza por esa. 15 minutos."
    
    # EJERCICIOS/PROBLEMAS - Tareas analíticas repetitivas
    elif tarea == "resolver_problemas":
        if sent == "aburrimiento":
            return "Entiendo que te aburran los ejercicios. Prueba esto: ponte un reto de velocidad. ¿Cuántos ejercicios puedes resolver en 15 minutos? Sin revisar, solo resolver. Después revisas. El desafío lo hace menos monótono. ¿De qué materia son?"
        
        elif sent == "ansiedad_error":
            return "Entiendo tu ansiedad con los ejercicios. El miedo a equivocarse paraliza. Te propongo: resuelve los ejercicios EN LÁPIZ, permitiéndote borrar y equivocarte. Haz solo 3 ejercicios sin juzgarte. 15 minutos. ¿De qué materia son?"
        
        elif sent == "frustracion":
            return "Entiendo tu frustración con los ejercicios. Cuando nos trabamos, ayuda cambiar de estrategia. Te sugiero: SALTA los ejercicios difíciles temporalmente. Haz solo los que sabes hacer. 15 minutos. Vuelves a los difíciles después con más confianza."
        
        elif sent == "dispersion_rumiacion":
            return "Entiendo que te cueste concentrarte. Los ejercicios son buenos para esto porque son concretos. Te propongo: resuelve solo 1 ejercicio completo. Sin celular cerca. Solo ese uno. Unos 10 minutos. Después decides si sigues. ¿De qué materia son?"
    
    # LECTURA - Tareas de procesamiento de información
    elif tarea == "lectura_tecnica":
        if sent == "aburrimiento":
            return "Entiendo que te aburra leer. Prueba esto: lee BUSCANDO respuestas a 3 preguntas específicas que te hagas antes de empezar. No leas pasivo. Lee como detective. 15 minutos. ¿De qué tema es la lectura?"
        
        elif sent == "ansiedad_error":
            return "Entiendo tu ansiedad con la lectura. La presión por 'entender todo' agobia. Te propongo: solo subraya lo que creas importante. Sin tomar apuntes. Solo marca. 15 minutos. Después decides qué hacer con eso. ¿De qué tema es?"
        
        elif sent == "dispersion_rumiacion":
            return "Entiendo que te cueste concentrarte al leer. Te sugiero: lee EN VOZ ALTA (aunque sea susurrando). Obliga a tu mente a enfocarse. Solo 10 minutos de las primeras páginas. ¿De qué tema es la lectura?"
        
        elif plazo in ["hoy", "<24h"]:
            return "Entiendo que tengas poco tiempo para leer. Te sugiero lectura estratégica: lee solo la introducción, conclusión y los primeros párrafos de cada sección. 15 minutos. Captarás las ideas principales. ¿De qué tema es?"
    
    # PRESENTACIONES - Tareas de síntesis y diseño
    elif tarea == "presentacion":
        if sent == "ansiedad_error":
            return "Entiendo tu ansiedad con la presentación. La presión por hacerla perfecta paraliza. Te propongo: crea solo el ÍNDICE de slides. Sin diseño, sin texto extenso. Solo títulos. 10 minutos. El contenido viene después. ¿De qué tema es?"
        
        elif sent == "aburrimiento":
            return "Entiendo que te aburra hacer la presentación. Prueba esto: empieza buscando 3 imágenes o gráficos llamativos sobre tu tema. Sin texto. Solo visuales. 15 minutos. Te dará ideas y es más entretenido. ¿De qué es la presentación?"
        
        elif fase == "ideacion":
            return "Entiendo que estés empezando la presentación. Te sugiero: anota solo los 5 mensajes clave que quieres que tu audiencia recuerde. Sin desarrollar. Solo 5 frases. 10 minutos. Eso es tu columna vertebral. ¿De qué tema es?"
    
    # CÓDIGO/PROGRAMACIÓN - Tareas técnicas de construcción
    elif tarea == "coding_bugfix":
        if sent == "frustracion":
            return "Entiendo tu frustración con el código. Cuando nos trabamos, ayuda 'duck debugging': explícale tu código EN VOZ ALTA a un objeto (o a mí). Línea por línea. 10 minutos. Muchas veces encuentras el error explicándolo. ¿Qué bug estás buscando?"
        
        elif sent == "ansiedad_error":
            return "Entiendo tu ansiedad al programar. El miedo a romper cosas paraliza. Te propongo: haz una COPIA del código primero. Luego experimenta sin miedo. Si falla, vuelves a la copia. 20 minutos de prueba y error seguro. ¿Qué estás programando?"
        
        elif sent == "dispersion_rumiacion":
            return "Entiendo que te cueste concentrarte programando. Te sugiero: programa SOLO una función pequeña. Sin pensar en el resto. Solo esa función. Prúebala. 15 minutos. Lo concreto ayuda a enfocar. ¿Qué funcionalidad estás haciendo?"
    
    # REVISIÓN/PROOFREADING - Tareas de refinamiento
    elif tarea == "proofreading":
        if sent == "aburrimiento":
            return "Entiendo que te aburra revisar. Prueba esto: revisa LEYENDO HACIA ATRÁS. De la última oración a la primera. Suena raro pero te obliga a prestar atención a cada palabra. 15 minutos. ¿Qué texto estás revisando?"
        
        elif plazo in ["hoy", "<24h"]:
            return "Entiendo que tengas poco tiempo para revisar. Te sugiero priorizar: busca solo errores graves (argumentos flojos, datos incorrectos, errores de ortografía evidentes). Sin perfeccionar. 15 minutos. ¿Qué estás revisando?"
    
    return None


def _get_task_strategies() -> Dict[str, str]:
    """Estrategias generales por tipo de tarea (sin considerar sentimiento)"""
    return {
        "ensayo": "Para tu ensayo, te sugiero empezar con algo pequeño: escribe solo 3 ideas principales en bullets. Sin redactar, solo ideas clave. Unos 10 minutos. ¿Cómo te suena?",
        "resolver_problemas": "Para tus ejercicios, te propongo: resuelve solo los 3 primeros, sin presión de terminar todo. Unos 15 minutos. Cuando termines esos 3, ya avanzaste.",
        "lectura_tecnica": "Para tu lectura, te sugiero: lee solo las primeras 3-5 páginas, subrayando solo las ideas principales. Sin apuntes extensos. Unos 12 minutos. ¿Te parece?",
        "presentacion": "Para tu presentación, ¿qué tal si creas solo el índice de los temas que vas a cubrir? Sin desarrollar nada, solo títulos. Unos 10 minutos.",
        "coding_bugfix": "Para tu código, te sugiero: trabaja solo en una función o componente pequeño. Sin intentar arreglar todo. Unos 15-20 minutos enfocados.",
        "proofreading": "Para revisar, te propongo: revisa solo la primera página o sección. Busca solo errores evidentes, no perfección. Unos 10 minutos.",
        "mcq": "Para tu prueba, te sugiero: responde solo las preguntas que sabes con seguridad primero. Sin quedarte pensando mucho. Unos 15 minutos.",
        "esquema": "Para tu esquema, te propongo: solo anota las 3-5 secciones principales. Sin detalles. Solo estructura. 10 minutos.",
        "borrador": "Para tu borrador, te sugiero: escribe libremente sin juzgar. No edites mientras escribes. Solo avanza. 15 minutos.",
        "resumen": "Para tu resumen, te propongo: subraya las 5 ideas más importantes del texto original. Solo subrayar, no escribir aún. 10 minutos.",
        "protocolo_lab": "Para tu protocolo de lab, te sugiero: solo completa la sección de materiales y métodos. Sin análisis aún. 15 minutos."
    }


def _detect_fit_gap(slots: Slots) -> Optional[str]:
    """Detecta desajustes entre tarea, emoción y contexto para reencuadrar según Task-Motivation Fit"""
    if not slots.tipo_tarea:
        return None
    creative_tasks = {"ensayo", "esquema", "borrador", "presentacion"}
    analytic_tasks = {"resolver_problemas", "mcq", "protocolo_lab", "coding_bugfix", "lectura_tecnica", "proofreading"}
    plazo = slots.plazo
    sentimiento = slots.sentimiento
    fase = slots.fase
    
    if slots.tipo_tarea in creative_tasks and plazo in ["hoy", "<24h"]:
        return "Veo que tu tarea es creativa pero el plazo es cortísimo. En teoría metamotivacional eso es un choque promoción vs prevención. Hagamos un switch a modo prevención: define solo el mínimo entregable (p.ej. introducción + esquema) en 15 minutos para asegurar avance tangible."
    
    if slots.tipo_tarea in analytic_tasks and sentimiento == "aburrimiento":
        return "Las tareas analíticas repetitivas pueden bajar la activación. Para recuperar el match motivacional, conviértelo en un reto de eficiencia: mide cuántos ejercicios o páginas revisas en 12 minutos y trata de superarte." 
    
    if sentimiento == "ansiedad_error" and fase in ["ideacion", "planificacion"]:
        return "Estás en fase exploratoria pero tu foco interno es de prevención. Para bajar la ansiedad, define un prototipo feo: escribe ideas sin juzgar y marca con ⭐ lo que valga la pena pulir después."
    
    if sentimiento == "dispersion_rumiacion" and slots.tipo_tarea in creative_tasks:
        return "Cuando la mente divaga y la tarea exige creatividad, usamos anclajes sensoriales. Abre un nuevo doc y escribe solo una lista numerada con 5 lugares donde podrías comenzar. No desarrolles, solo lista."
    
    return None

def _refresh_repeated_response(new_reply: str, last_reply: Optional[str], user_text: str) -> str:
    """Evita respuestas idénticas agregando reconocimiento del aporte del usuario"""
    if not last_reply or not new_reply:
        return new_reply
    if new_reply.strip() != last_reply.strip():
        return new_reply
    detail = user_text.strip()
    if not detail:
        detail = "lo último que mencionaste"
    elif len(detail) > 80:
        detail = detail[:80].rstrip() + "..."
    return f"Anotado lo que dices (\"{detail}\"). Mantengamos la micro-estrategia, pero avísame si quieres ajustarla:\n\n{new_reply}"


def _evaluation_quick_replies() -> List[Dict[str, str]]:
    """Opciones estándar para evaluar la estrategia"""
    return [
        {"label": "✅ Me ayudó", "value": "me ayudó"},
        {"label": "😐 Sigo igual", "value": "sigo igual"},
        {"label": "😟 No me sirvió", "value": "no funcionó"}
    ]


# ---------------------------- ORQUESTADOR PRINCIPAL ---------------------------- #

async def handle_user_turn(session: SessionStateSchema, user_text: str, context: str = "", chat_history: Optional[List] = None) -> Tuple[str, SessionStateSchema, Optional[List[Dict[str, str]]]]:
    """
    Orquestador principal del flujo metamotivacional.
    Retorna (respuesta_texto, session_actualizada, quick_replies)
    """
    
    # 1) Crisis
    if detect_crisis(user_text):
        crisis_msg = "Escucho que estás en un momento muy difícil. Por favor, busca apoyo inmediato: **llama al 4141** (línea gratuita y confidencial del MINSAL). No estás sola/o."
        return crisis_msg, session, None
    
    # 2) Saludo inicial - DEBE IR ANTES DE CUALQUIER PROCESAMIENTO
    user_text_lower = user_text.lower().strip()
    if not session.greeted:
        session.greeted = True
        welcome = f"Hola! 👋 Soy {AI_NAME}, tu asistente metamotivacional.\n\nEstoy aquí para ayudarte a encontrar la mejor forma de trabajar según cómo te sientas y qué tengas que hacer.\n\n¿En qué puedo ayudarte hoy?"
        return welcome, session, None
    
    # 2b) Detectar saludos simples después del saludo inicial (evitar procesamiento innecesario)
    simple_greetings = ["hola", "holi", "hey", "hi", "buenas", "buenos días", "buenas tardes"]
    if user_text_lower in simple_greetings:
        return "Hola de nuevo 😊 ¿En qué puedo ayudarte hoy?", session, None
    
    # 3) Extracción de slots
    try:
        new_slots = await extract_slots_with_llm(user_text, session.slots)
    except Exception as e:
        logger.error(f"Error en extracción de slots: {e}")
        new_slots = extract_slots_heuristic(user_text, session.slots)
    
    session.slots = new_slots
    
    # 4) Si falta dato clave, preguntar (solo en las primeras interacciones)
    missing = []
    if not new_slots.sentimiento:
        missing.append("sentimiento")
    if not new_slots.tipo_tarea:
        missing.append("tipo_tarea")
    if not new_slots.fase:
        missing.append("fase")
    if not new_slots.plazo:
        missing.append("plazo")
    if not new_slots.tiempo_bloque:
        missing.append("tiempo_bloque")
    
    if missing:
        logger.debug(f"Slots incompletos para estrategia: {missing}. Continuando con heurísticas.")
    
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
    
    # PRIMERO: Verificar si el usuario aceptó ir a bienestar (antes de otras detecciones)
    if "quiero probar un ejercicio de bienestar" in user_text_lower or "DERIVAR_BIENESTAR" in user_text.upper():
        session.iteration = 0  # Reset para cuando vuelva
        session.last_eval_result = EvalResult(fallos_consecutivos=0)
        reply = "Perfecto 😊 Voy a llevarte a la sección de Bienestar. Elige el ejercicio que más te llame la atención y tómate tu tiempo. Cuando termines, vuelve aquí y seguimos con tu tarea con energía renovada."
        quick_replies = [
            {"label": "🌿 Ir a Bienestar", "value": "NAVIGATE_WELLNESS"}
        ]
        return reply, session, quick_replies
    
    # Detectar respuestas de evaluación del usuario
    # IMPORTANTE: Verificar frases negativas PRIMERO (más específicas)
    respuestas_sin_mejora = [
        "no funcionó", "no funciono", "no me funcionó", "no me ayudó", "no me ayudo",
        "sigo igual", "estoy igual", "igual que antes",
        "peor", "me siento peor", "estoy peor", "más mal",
        "no mejoró", "no mejoro", "no ayudó", "no ayudo", 
        "no sirvió", "no sirvio"
    ]
    respuestas_mejora = [
        "me ayudó", "me ayudo", "sí me ayudó", "si me ayudo",
        "funcionó bien", "funciono bien", "sí funcionó", "si funciono",
        "mejor", "me siento mejor", "estoy mejor", "mucho mejor",
        "bien", "muy bien", "genial", "excelente", "perfecto"
    ]
    
    # user_text_lower ya fue declarado arriba, reutilizarlo
    
    # Verificar sin_mejora PRIMERO (tiene frases más específicas con "no")
    sin_mejora = any(frase in user_text_lower for frase in respuestas_sin_mejora)
    # Solo verificar mejora si NO detectó sin_mejora (para evitar conflictos)
    mejora = False if sin_mejora else any(frase in user_text_lower for frase in respuestas_mejora)
    
    # Si el usuario indica que MEJORÓ, cerrar con mensaje de despedida
    if mejora and session.iteration > 0:
        session.last_eval_result = EvalResult(fallos_consecutivos=0, cambio_sentimiento="↑")
        session.iteration = 0  # Reiniciar para próxima conversación
        session.greeted = False  # Permitir nuevo saludo en próxima sesión
        
        reply = f"""¡Qué bueno escuchar eso! 😊 Me alegra mucho que te haya servido.

Recuerda que siempre puedes volver cuando necesites apoyo o una nueva estrategia. Estoy aquí para ayudarte a encontrar tu mejor forma de trabajar.

¡Mucho éxito con tu tarea! 🚀"""
        
        return reply, session, None
    
    # Si el usuario indica que NO mejoró, incrementar contador de fallos
    if sin_mejora and session.iteration > 0:
        fallos = session.last_eval_result.fallos_consecutivos if session.last_eval_result else 0
        fallos += 1
        session.last_eval_result = EvalResult(fallos_consecutivos=fallos, cambio_sentimiento="=")
        
        # Verificar INMEDIATAMENTE si debe ofrecer bienestar (≥2 fallos)
        if fallos >= 2:
            reply = f"""Veo que hemos intentado un par de estrategias y todavía no te sientes mejor 😔

A veces lo que sentimos no es solo un tema de organización o método de estudio. El cuerpo y la mente necesitan un respiro antes de seguir intentando.

¿Qué te parece si primero hacemos un ejercicio breve de bienestar? Hay algunos de respiración, relajación o mindfulness que pueden ayudarte a resetear.

Solo toma 3-5 minutos y después volvemos con tu tarea. ¿Quieres probar?"""
            
            quick_replies = [
                {"label": "🌿 Ir a Bienestar", "value": "NAVIGATE_WELLNESS"},
                {"label": "🔄 Seguir con estrategias", "value": "No gracias, sigamos intentando con otras estrategias"}
            ]
            
            # Reset del contador para que no siga ofreciendo
            session.last_eval_result = EvalResult(fallos_consecutivos=0)
            
            return reply, session, quick_replies
        
        # ****** INICIO DE LA NUEVA LÓGICA DE RECALIBRACIÓN (SI FALLOS=1) ******
        if fallos < 2:
            logger.info(f"Recalibrando estrategia... (Fallo {fallos})")
            
            # 1. Cambiar Q3 (de ↑→↓ o viceversa)
            if session.Q3 == "↑":
                session.Q3 = "↓"
            elif session.Q3 == "↓":
                session.Q3 = "↑"
            
            # 2. Ajustar tamaño de tarea (hacerla más pequeña)
            session.tiempo_bloque = 10  # Forzar bloque más corto
            
            # Actualizar AMBOS para coherencia
            session.slots.tiempo_bloque = 10
            new_slots.tiempo_bloque = 10
            
            logger.info(f"Nueva Q3: {session.Q3}, Nuevo tiempo: {session.tiempo_bloque}")
        # ****** FIN DE LA NUEVA LÓGICA DE RECALIBRACIÓN ******
        
        # Si aún no llega a 2 fallos, continuar para generar nueva estrategia
        # NO hacer return aquí, dejar que el código siga y genere nueva estrategia
    
    # 7) Generar respuesta conversacional usando Gemini con historial
    reply = None
    try:
        llm_model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            system_instruction=get_system_prompt()
        )
        
        history = []
        if chat_history:
            recent_history = chat_history[-11:-1] if len(chat_history) > 11 else chat_history[:-1]
            for msg in recent_history:
                history.append({
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [msg["text"]]
                })
        
        info_contexto = f"""
[Info contextual]:
- Sentimiento: {new_slots.sentimiento or 'no especificado'}
- Tarea: {new_slots.tipo_tarea or 'no especificada'} {f"de {new_slots.ramo}" if new_slots.ramo else ""}
- Plazo: {new_slots.plazo or 'no especificado'}
- Fase: {new_slots.fase or 'no especificada'}
- Tiempo: {new_slots.tiempo_bloque or 15} min
"""
        
        gen_config = genai.types.GenerationConfig(
            temperature=0.75,
            max_output_tokens=400,
            top_p=0.9
        )
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        chat = llm_model.start_chat(history=history)
        full_message = f"{info_contexto}\n\nEstudiante: {user_text}"
        response = chat.send_message(
            full_message,
            generation_config=gen_config,
            safety_settings=safety_settings
        )
        
        if not response.candidates:
            raise RuntimeError("Gemini devolvió una respuesta vacía")
        candidate = response.candidates[0]
        finish_reason = getattr(candidate, "finish_reason", None)
        blocked = finish_reason in (2, "SAFETY", "BLOCKED", "SAFETY_BLOCK")
        if blocked or not candidate.content or not candidate.content.parts:
            raise RuntimeError(f"Respuesta bloqueada o vacía (finish_reason={finish_reason})")
        reply = candidate.content.parts[0].text.strip()
        if not reply:
            raise RuntimeError("Respuesta sin texto utilizable")
    except Exception as e:
        logger.warning(f"Falló la generación con Gemini, usando estrategia interna: {e}")
        reply = _generate_fallback_response(new_slots, user_text)
    
    reply = _refresh_repeated_response(reply, session.last_strategy, user_text)
    session.iteration += 1
    session.last_strategy = reply
    
    quick_replies = _evaluation_quick_replies()
    
    return reply, session, quick_replies


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

