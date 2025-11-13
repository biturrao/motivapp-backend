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
- Eres empática y validates las emociones antes de dar consejos
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
            return "coding_bugfix"  # Usamos el mismo tipo pero con intención de desarrollo
    
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
    
    # 2) Saludo único
    if not session.greeted:
        session.greeted = True
        welcome = "😊 ¿Cómo está tu motivación hoy?"
        quick_replies = [
            {"label": "😑 Aburrimiento", "value": "Siento aburrimiento"},
            {"label": "😤 Frustración", "value": "Siento frustración"},
            {"label": "😰 Ansiedad", "value": "Siento ansiedad"},
            {"label": "🌀 Dispersión", "value": "Siento dispersión"},
            {"label": "😔 Baja motivación", "value": "Tengo baja motivación"},
            {"label": "💭 Otro", "value": "Siento otra cosa"}
        ]
        return welcome, session, quick_replies
    
    # 3) Extracción de slots
    try:
        new_slots = await extract_slots_with_llm(user_text, session.slots)
    except Exception as e:
        logger.error(f"Error en extracción de slots: {e}")
        new_slots = extract_slots_heuristic(user_text, session.slots)
    
    session.slots = new_slots
    
    # 4) Si falta dato clave, preguntar (solo en las primeras interacciones)
    missing = []
    if not new_slots.tipo_tarea:
        missing.append("tipo_tarea")
    if not new_slots.fase:
        missing.append("fase")
    if not new_slots.plazo:
        missing.append("plazo")
    if not new_slots.tiempo_bloque:
        missing.append("tiempo_bloque")
    
    # Preguntar si faltan datos importantes y aún no hemos iterado mucho
    if missing and session.iteration < 2:
        priority = ["tipo_tarea", "plazo", "fase", "tiempo_bloque"]
        want = next((k for k in priority if k in missing), None)
        quick_replies = None
        
        if want == "tipo_tarea":
            q = "¿Qué tipo de trabajo tienes que hacer?"
            quick_replies = [
                {"label": "📝 Escribir algo", "value": "Tengo que escribir un trabajo"},
                {"label": "📖 Leer/Estudiar", "value": "Tengo que leer y estudiar"},
                {"label": "🧮 Resolver ejercicios", "value": "Tengo que resolver ejercicios"},
                {"label": "🔍 Revisar/Corregir", "value": "Tengo que revisar mi trabajo"}
            ]
        elif want == "fase":
            q = "¿En qué etapa estás?"
            quick_replies = [
                {"label": "💡 Recién empezando", "value": "Estoy en la fase de ideacion"},
                {"label": "📋 Planificando", "value": "Estoy en la fase de planificacion"},
                {"label": "✍️ Haciendo el trabajo", "value": "Estoy en la fase de ejecucion"},
                {"label": "🔍 Revisando", "value": "Estoy en la fase de revision"}
            ]
        elif want == "plazo":
            q = "¿Para cuándo lo necesitas?"
            quick_replies = [
                {"label": "🔥 Hoy", "value": "Es para hoy"},
                {"label": "⏰ Mañana", "value": "Es para mañana"},
                {"label": "📅 Esta semana", "value": "Es para esta semana"},
                {"label": "🗓️ Más adelante", "value": "Tengo más de una semana"}
            ]
        else:
            q = "¿Cuánto tiempo tienes disponible ahora?"
            quick_replies = [
                {"label": "⚡ 10 min", "value": "Tengo 10 minutos"},
                {"label": "🎯 15 min", "value": "Tengo 15 minutos"},
                {"label": "💪 25 min", "value": "Tengo 25 minutos"},
                {"label": "🔥 Más tiempo", "value": "Tengo más de 25 minutos"}
            ]
        
        return q, session, quick_replies
    
    # Defaults prudentes
    if not new_slots.tiempo_bloque:
        new_slots.tiempo_bloque = 15
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
    if "quiero probar un ejercicio de bienestar" in user_text.lower() or "DERIVAR_BIENESTAR" in user_text.upper():
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
    
    user_text_lower = user_text.lower().strip()
    
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
                {"label": "✅ Sí, vamos a intentarlo", "value": "Sí, quiero probar un ejercicio de bienestar"},
                {"label": "🔄 No, sigamos con estrategias", "value": "No gracias, sigamos intentando con otras estrategias"}
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
            if session.tiempo_bloque and session.tiempo_bloque > 10:
                session.tiempo_bloque = 10  # Forzar bloque más corto
            else:
                session.tiempo_bloque = 10
            
            # Actualizar los slots para que la generación de respuesta use el tiempo acortado
            session.slots.tiempo_bloque = 10
            logger.info(f"Nueva Q3: {session.Q3}, Nuevo tiempo: {session.tiempo_bloque}")
        # ****** FIN DE LA NUEVA LÓGICA DE RECALIBRACIÓN ******
        
        # Si aún no llega a 2 fallos, continuar para generar nueva estrategia
        # NO hacer return aquí, dejar que el código siga y genere nueva estrategia
    
    # 7) Generar respuesta conversacional usando Gemini con historial
    try:
        llm_model = genai.GenerativeModel(
            model_name='gemini-2.5-pro',
            system_instruction=get_system_prompt()
        )
        
        # Construir el historial de conversación para Gemini
        history = []
        if chat_history:
            for msg in chat_history[:-1]:  # Excluir el último mensaje del usuario (ya lo pasaremos aparte)
                history.append({
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [msg["text"]]
                })
        
        # Agregar contexto adicional si existe
        info_contexto = f"""
[Info contextual - úsala para personalizar tu respuesta]:
- Sentimiento: {new_slots.sentimiento or 'no especificado'}
- Tarea: {new_slots.tipo_tarea or 'no especificada'} {f"de {new_slots.ramo}" if new_slots.ramo else ""}
- Plazo: {new_slots.plazo or 'no especificado'}
- Fase: {new_slots.fase or 'no especificada'}
- Tiempo disponible: {new_slots.tiempo_bloque or 15} minutos
{context if context else ""}
"""
        
        # Iniciar chat con historial
        chat = llm_model.start_chat(history=history)
        
        # Enviar mensaje actual con contexto
        full_message = f"{info_contexto}\n\nEstudiante: {user_text}"
        response = chat.send_message(
            full_message,
            generation_config=genai.types.GenerationConfig(
                temperature=0.8,
                max_output_tokens=400,  # Aumentado para dar mejores explicaciones
                top_p=0.95
            )
        )
        
        reply = response.text.strip()
        
    except Exception as e:
        logger.error(f"Error generando respuesta conversacional: {e}")
        # Fallback simple y empático
        reply = f"Entiendo, cuéntame un poco más sobre lo que necesitas hacer. ¿Qué tipo de trabajo es y para cuándo lo necesitas?"
    
    session.iteration += 1
    session.last_strategy = reply
    
    # Si ya dio una estrategia (iteration >= 1), preguntar si funcionó
    # La primera iteración es el saludo, desde la segunda ya da estrategias
    if session.iteration >= 1:
        quick_replies = [
            {"label": "✅ Me ayudó, me siento mejor", "value": "me ayudó"},
            {"label": "😐 Sigo igual", "value": "sigo igual"},
            {"label": "😟 Me siento peor", "value": "no funcionó"}
        ]
    else:
        # Solo en el primer mensaje (saludo), dejar fluir la conversación
        quick_replies = None
    
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

