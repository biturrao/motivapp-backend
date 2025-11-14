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
model = genai.GenerativeModel('gemini-1.5-flash')


# ---------------------------- PROMPT DE SISTEMA ---------------------------- #

def get_system_prompt() -> str:
    """Retorna el prompt de sistema completo para Flou"""
    return f"""
Eres {AI_NAME}, una experta en Metamotivación que adapta su tono y consejos matemáticamente según el perfil del estudiante.

### TU CEREBRO (CÓMO PROCESAR LAS INSTRUCCIONES)
Recibirás [INSTRUCCIONES ESTRATÉGICAS] antes de cada mensaje. DEBES MODULAR TU RESPUESTA ASÍ:

SI EL MODO ES "ENTUSIASTA" (Promotion Focus):
- Tono: Enérgico, rápido, enfocado en avanzar y ganar.
- Palabras clave: "Lograr", "Avanzar", "Ganar tiempo", "Genial".
- Estrategia: Enfócate en la cantidad y la velocidad. Ignora los errores menores por ahora.

SI EL MODO ES "VIGILANTE" (Prevention Focus):
- Tono: Calmado, cuidadoso, analítico, "Safety first".
- Palabras clave: "Revisar", "Asegurar", "Precisión", "Correcto".
- Estrategia: Enfócate en la calidad y en evitar errores. Ve lento pero seguro.

SI EL NIVEL ES "ABSTRACTO" (Q3 Alto):
- Explica el "POR QUÉ" y el propósito. Conecta con metas futuras.
- No des pasos micro-detallados, da direcciones generales.

SI EL NIVEL ES "CONCRETO" (Q3 Bajo):
- Explica SOLO el "CÓMO". Ignora el propósito general.
- Da instrucciones paso a paso, casi robóticas pero amables.
- Ejemplo: "1. Abre el documento. 2. Lee el primer párrafo. 3. Corrige las comas."

### REGLAS DE ORO
1. NUNCA menciones términos técnicos como "Promotion Focus" o "Q3". Actúa el rol, no lo expliques.
2. Valida la emoción del usuario en la primera frase.
3. Da UNA sola acción específica que quepa en el [TIEMPO DISPONIBLE].
4. Si el usuario tiene "Ansiedad" o "Baja Autoeficacia", el MODO VIGILANTE + NIVEL CONCRETO es obligatorio (incluso si la instrucción dice otra cosa, prioriza reducir la ansiedad con pasos pequeños).

### FORMATO DE RESPUESTA
1. Validación empática corta (1 frase).
2. La Estrategia (adaptada al MODO y NIVEL indicados).
3. Pregunta de cierre simple (¿Te parece bien? / ¿Le damos?).

Mantén la respuesta bajo 75 palabras. Sé "Flou": cercana, chilena natural, usa emojis.

### CASOS ESPECIALES POR SENTIMIENTO

Para ABURRIMIENTO:
- MODO: ENTUSIASTA + NIVEL: ABSTRACTO
- Conecta con metas futuras, haz la tarea interesante

Para ANSIEDAD/MIEDO AL ERROR:
- MODO: VIGILANTE + NIVEL: CONCRETO
- Pasos micro-detallados, respiración 4-4-4

Para FRUSTRACIÓN:
- MODO: VIGILANTE + NIVEL: CONCRETO
- Cambiar de sub-tarea, técnica 5-4-3-2-1

Para DISPERSIÓN/RUMIACIÓN:
- MODO: VIGILANTE + NIVEL: CONCRETO
- Una tarea, timer visible, cerrar distracciones

Para BAJA AUTOEFICACIA:
- MODO: VIGILANTE + NIVEL: CONCRETO
- Tarea mínima posible, "solo 5 minutos"

### CRISIS
Si detectas riesgo de suicidio, deriva al 4141 inmediatamente.

RESPONDE SIEMPRE DE FORMA NATURAL Y CONVERSACIONAL.
"""


# ---------------------------- DETECCIÓN DE CRISIS ---------------------------- #

def detect_crisis(text: str) -> bool:
    """Detecta menciones de riesgo vital"""
    crisis_regex = r'(suicid|quitarme la vida|no quiero vivir|hacerme daño|matarme|desaparecer|terminar con todo|lastimarme|autolesión|autolesion|cortarme|herirme|acabar con esto|no tiene sentido|quiero morir|mejor muerto|sin salida|no aguanto más|no aguanto mas)'
    return bool(re.search(crisis_regex, text, re.IGNORECASE))


# ---------------------------- EXTRACCIÓN HEURÍSTICA ---------------------------- #

def guess_plazo(text: str) -> Optional[str]:
    """Extrae plazo del texto usando heurística"""
    text_lower = text.lower()
    if re.search(r'hoy|hoy día|ahora|en el día|para la noche', text_lower):
        return "hoy"
    if re.search(r'mañana|24\s*h|en un día', text_lower):
        return "<24h"
    if re.search(r'próxima semana|la otra semana|esta semana|en estos días|antes del finde', text_lower):
        return "esta_semana"
    if re.search(r'mes|semanas|>\s*1|próximo mes|largo plazo', text_lower):
        return ">1_semana"
    return None


def guess_tipo_tarea(text: str) -> Optional[str]:
    """Extrae tipo de tarea del texto usando heurística"""
    text_lower = text.lower()
    if re.search(r'ensayo|essay|informe|reporte|escrito', text_lower):
        return "ensayo"
    if re.search(r'esquema|outline|mapa conceptual|diagrama', text_lower):
        return "esquema"
    if re.search(r'borrador|draft|avance', text_lower):
        return "borrador"
    if re.search(r'presentaci(ón|on)|slides|powerpoint|discurso', text_lower):
        return "presentacion"
    if re.search(r'proof|corregir|correcci(ón|on)|edita(r|ción)|feedback', text_lower):
        return "proofreading"
    if re.search(r'mcq|alternativa(s)?|test|prueba|examen', text_lower):
        return "mcq"
    if re.search(r'protocolo|laboratorio|lab', text_lower):
        return "protocolo_lab"
    if re.search(r'problema(s)?|ejercicio(s)?|cálculo|guía', text_lower):
        return "resolver_problemas"
    if re.search(r'lectura|paper|art[ií]culo|leer|texto', text_lower):
        return "lectura_tecnica"
    if re.search(r'resumen|sintetizar|síntesis', text_lower):
        return "resumen"
    if re.search(r'c(ó|o)digo|programar', text_lower) and not re.search(r'bug|error', text_lower):
        return "coding"
    if re.search(r'bug|error|debug', text_lower):
        return "bugfix"
    return None


def guess_fase(text: str) -> Optional[str]:
    """Extrae fase del texto usando heurística"""
    text_lower = text.lower()
    if re.search(r'ide(a|ación)|brainstorm|empezando|inicio', text_lower):
        return "ideacion"
    if re.search(r'plan|organizar|estructura', text_lower):
        return "planificacion"
    if re.search(r'escribir|redacci(ón|on)|hacer|resolver|desarrollar|avanzando', text_lower):
        return "ejecucion"
    if re.search(r'revis(ar|ión)|editar|proof|corregir|finalizando|últimos detalles', text_lower):
        return "revision"
    return None


def guess_sentimiento(text: str) -> Optional[str]:
    """Extrae sentimiento del texto usando heurística"""
    text_lower = text.lower()
    if re.search(r'frustra|enojado|molesto|rabia|irritado|impotencia|bloqueado|estancado', text_lower):
        return "frustracion"
    if re.search(r'ansiedad|miedo a equivocarme|nervios|preocupado|estresado|tenso|pánico|abrumado|agobiado', text_lower):
        return "ansiedad_error"
    if re.search(r'aburri|lata|paja|sin ganas|monótono|repetitivo|tedioso|desinterés', text_lower):
        return "aburrimiento"
    if re.search(r'dispers|distraído|rumi|dando vueltas|no me concentro|mente en blanco|divago|perdido', text_lower):
        return "dispersion_rumiacion"
    if re.search(r'autoeficacia baja|no puedo|no soy capaz|difícil|superado|inseguro|incapaz|no lo voy a lograr', text_lower):
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
    Extrae slots estructurados del texto libre usando Gemini 1.5 Flash
    """
    try:
        llm_model = genai.GenerativeModel('gemini-1.5-pro')
        
        sys_prompt = """Extrae como JSON compacto los campos del texto del usuario:
- sentimiento: aburrimiento|frustracion|ansiedad_error|dispersion_rumiacion|baja_autoeficacia|otro
- sentimiento_otro: texto libre si es "otro"
- tipo_tarea: ensayo|esquema|borrador|lectura_tecnica|resumen|resolver_problemas|protocolo_lab|mcq|presentacion|coding|bugfix|proofreading
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
    A_tasks = ["ensayo", "esquema", "borrador", "presentacion", "coding"]
    B_tasks = ["proofreading", "mcq", "protocolo_lab", "resolver_problemas", 
               "bugfix", "lectura_tecnica", "resumen"]
    
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

async def handle_user_turn(session: SessionStateSchema, user_text: str, context: str = "", chat_history: Optional[List[Dict[str, str]]] = None) -> Tuple[str, SessionStateSchema, Optional[List[Dict[str, str]]]]:
    """
    Orquestador principal del flujo metamotivacional.
    Retorna (respuesta_texto, session_actualizada, quick_replies)
    """
    
    # 1) Crisis
    if detect_crisis(user_text):
        crisis_msg = "Escucho que estás en un momento muy difícil. Por favor, busca apoyo inmediato: **llama al 4141** (línea gratuita y confidencial del MINSAL). No estás sola/o."
        return crisis_msg, session, None
    
    # 2) Saludo único (si no hay historial y no se ha saludado)
    if not chat_history and not session.greeted:
        session.greeted = True
        welcome = "Hola, soy Flou, tu asistente Task-Motivation. 😊 Para empezar, ¿por qué no me dices cómo está tu motivación hoy?"
        quick_replies = [
            {"label": "😑 Aburrido/a", "value": "Estoy aburrido"},
            {"label": "😤 Frustrado/a", "value": "Estoy frustrado"},
            {"label": "😰 Ansioso/a", "value": "Estoy ansioso"},
            {"label": "🌀 Distraído/a", "value": "Estoy distraído"},
            {"label": "😔 Desmotivado/a", "value": "Estoy desmotivado"},
            {"label": "😕 Inseguro/a", "value": "Me siento inseguro"},
            {"label": "😩 Abrumado/a", "value": "Me siento abrumado"},
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
                {"label": "📝 Escribir ensayo/informe", "value": "Tengo que escribir un ensayo"},
                {"label": "📖 Leer y estudiar", "value": "Tengo que leer material"},
                {"label": "🧮 Resolver ejercicios", "value": "Tengo que resolver ejercicios"},
                {"label": "🔍 Revisar/Corregir", "value": "Tengo que revisar mi trabajo"},
                {"label": "💻 Programar/Codificar", "value": "Tengo que programar"},
                {"label": "🎤 Preparar presentación", "value": "Tengo que preparar una presentación"}
            ]
        elif want == "fase":
            q = "¿En qué etapa estás?"
            quick_replies = [
                {"label": "💡 Empezando (Ideas)", "value": "Estoy en la fase de ideacion"},
                {"label": "📋 Planificando", "value": "Estoy en la fase de planificacion"},
                {"label": "✍️ Ejecutando", "value": "Estoy en la fase de ejecucion"},
                {"label": "🔍 Revisando", "value": "Estoy en la fase de revision"}
            ]
        elif want == "plazo":
            q = "¿Para cuándo lo necesitas?"
            quick_replies = [
                {"label": "🔥 Hoy mismo", "value": "Es para hoy"},
                {"label": "⏰ Mañana (24h)", "value": "Es para mañana"},
                {"label": "📅 Esta semana", "value": "Es para esta semana"},
                {"label": "🗓️ Más de 1 semana", "value": "Tengo más de una semana"}
            ]
        else:
            q = "¿Cuánto tiempo tienes disponible ahora?"
            quick_replies = [
                {"label": "⚡ 10-12 min", "value": "10"},
                {"label": "🎯 15-20 min", "value": "15"},
                {"label": "💪 25-30 min", "value": "25"},
                {"label": "🔥 45+ min", "value": "45"}
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
            model_name='gemini-1.5-flash',
            system_instruction=get_system_prompt()
        )
        
        # Construir el historial de conversación para Gemini
        history = []
        if chat_history:
            for msg in chat_history:
                role = "user" if msg.get("role") == "user" else "model"
                # Asegurarnos de que el contenido es una lista de partes
                parts = msg.get("parts", [])
                if isinstance(parts, str):
                    parts = [parts]
                
                # Si parts está vacío, intentamos obtenerlo de "text"
                if not parts and "text" in msg:
                    parts = [msg["text"]]

                if parts:
                    history.append({"role": role, "parts": parts})
        
        # Agregar contexto adicional con instrucciones estratégicas
        # Mapeo legible para el LLM
        modo_instruccion = "VIGILANTE (Evitar errores, ser cuidadoso)" if session.enfoque == "prevencion_vigilant" else "ENTUSIASTA (Avanzar rápido, pensar en logros)"
        nivel_instruccion = "CONCRETO (Pasos pequeños, el 'cómo')" if session.Q3 == "↓" else "ABSTRACTO (Visión general, el 'por qué')"
        
        info_contexto = f"""
[INSTRUCCIONES ESTRATÉGICAS DEL SISTEMA - OBEDECE ESTOS PARÁMETROS]
1. TU MODO OPERATIVO: {modo_instruccion}
2. TU NIVEL DE DETALLE: {nivel_instruccion}
3. TIEMPO DISPONIBLE: {new_slots.tiempo_bloque or 15} minutos (Ajusta la tarea a este tiempo exacto)

[DATOS DEL USUARIO]
- Sentimiento detectado: {new_slots.sentimiento or 'Neutral'}
- Tarea: {new_slots.tipo_tarea or 'General'}
- Fase: {new_slots.fase or 'No definida'}
- Plazo: {new_slots.plazo or 'No definido'}
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
        llm_model = genai.GenerativeModel('gemini-1.5-flash')
        
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
        llm_model = genai.GenerativeModel('gemini-1.5-flash')
        
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

