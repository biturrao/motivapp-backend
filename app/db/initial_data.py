import logging
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
import json

from app.models.section import Section
from app.models.question import Question
from app.models.content import Content, ContentType
from app.models.lesson import Lesson
from app.models.refresh_token import RefreshToken  # Importar para que SQLAlchemy cree la tabla
from app.models.wellness_exercise import WellnessExercise, ExerciseState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Los datos del cuestionario que definiste
seed_data = {
    "sections": [
        "Nivel de atención a las señales internas",
        "Dirigir la atención a las señales internas",
        "Creencias",
        "Autorregulación"
    ],
    "questions": {
        "Nivel de atención a las señales internas": [
            "Aun cuando hay muchas distracciones en mi entorno académico, noto las señales internas que indican un cambio en mi estado motivacional.",
            "Noto las señales internas que indican cambios en mi motivación académica incluso cuando estas señales son débiles o tenues.",
            "Aun cuando estoy ocupado con diferentes pensamientos o preocupaciones, noto las señales internas que indican cambios en mi motivación académica.",
            "A pesar de estar ocupado con otras tareas, permanezco atento a las señales internas que indican cambios en mi motivación académica."
        ],
        "Dirigir la atención a las señales internas": [
            "Cuando es importante hacerlo, puedo aumentar mi atención a las señales internas que indican cambios en mi motivación",
            "Puedo redirigir mi atención de mis pensamientos e inquietudes a las señales internas que indican cambios en mi motivación",
            "Puedo dirigir mi atención desde las actividades que estoy llevando a cabo a las señales internas que indican cambios en mi motivación",
            "Puedo enfocar mi atención en las señales internas que indican cambios en mi motivación, incluso cuando estoy distraído por otras actividades"
        ],
        "Creencias": [
            "Creo que puedo modificar y/o generar cambios en mis estados motivacionales.",
            "Creo que identificar conscientemente mis estados motivacionales me permite modificar y/o generar cambios en ellos.",
            "Creo que identificar conscientemente mis estados motivacionales a través de señales de mi cuerpo me permite modificar y/o generar cambios en mi motivación.",
            "Creo que identificar conscientemente mis estados motivacionales a través de cambios en mi comportamiento me permite modificar y/o generar cambios en mi motivación."
        ],
        "Autorregulación": [
            "Detectar un alto estado de motivación hacia la tarea/actividad académica me permite activar estrategias para mantener ese estado y mejorar mi rendimiento.",
            "Detectar un bajo estado de motivación hacia la tarea/actividad académica me permite activar estrategias para cambiar ese estado y mejorar mi rendimiento.",
            "Cuando siento malestar respecto a mi estado motivacional, me tomo un tiempo para evaluar lo que me está pasando.",
            "Confío en las señales internas que puedo detectar para evaluar mi motivación."
        ]
    }
}

def migrate_section_table(db: Session):
    """
    Add new columns to sections table if they don't exist.
    This is a manual migration for backward compatibility.
    """
    try:
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('sections')]
        
        # Add missing columns
        if 'description' not in columns:
            logger.info("Adding 'description' column to sections table...")
            db.execute(text("ALTER TABLE sections ADD COLUMN description TEXT"))
            db.commit()
        
        if 'order' not in columns:
            logger.info("Adding 'order' column to sections table...")
            db.execute(text("ALTER TABLE sections ADD COLUMN \"order\" INTEGER DEFAULT 0"))
            db.commit()
        
        if 'icon_name' not in columns:
            logger.info("Adding 'icon_name' column to sections table...")
            db.execute(text("ALTER TABLE sections ADD COLUMN icon_name VARCHAR(50)"))
            db.commit()
        
        logger.info("Section table migration completed.")
    except Exception as e:
        logger.error(f"Error during section table migration: {e}")
        db.rollback()


def seed_db(db: Session):
    """
    Siembra la base de datos con las secciones y preguntas iniciales.
    """
    # First, run migration to add new columns if needed
    migrate_section_table(db)
    
    # Comprueba si ya existen datos para no duplicar
    first_section = db.query(Section).first()
    if first_section:
        logger.info("La base de datos ya contiene datos iniciales. Saltando siembra de secciones.")
    else:
        logger.info("Sembrando la base de datos con secciones y preguntas...")
        
        # Crea un mapa para acceder fácilmente a los objetos de sección
        section_map = {}
        for section_name in seed_data["sections"]:
            # Crea y guarda la sección
            section = Section(name=section_name)
            db.add(section)
            db.commit()
            db.refresh(section)
            section_map[section_name] = section
            
            # Itera sobre las preguntas de esa sección
            for question_text in seed_data["questions"].get(section_name, []):
                question = Question(text=question_text, section_id=section.id)
                db.add(question)
        
        # Confirma todas las preguntas agregadas
        db.commit()
        logger.info("Siembra de la base de datos completada.")
        
        # Seed path sections
        seed_path_sections(db)
    
    # Seed wellness exercises (siempre intentar, tiene su propia verificación)
    seed_wellness_exercises(db)


def seed_path_sections(db: Session):
    """
    Seeds the learning path sections with their contents and lessons.
    Sections: Iniciar, Autoregulación, Creencias, Señales Internas
    """
    logger.info("Sembrando secciones del path de aprendizaje...")
    
    # Check if path sections already exist
    existing_path_section = db.query(Section).filter(Section.name == "Iniciar").first()
    if existing_path_section:
        logger.info("Las secciones del path ya existen. Saltando siembra.")
        return
    
    # Define path sections
    path_sections = [
        {
            "name": "Iniciar",
            "description": "Fundamentos del entrenamiento de la mente y habilidades básicas",
            "order": 1,
            "icon_name": "compass"
        },
        {
            "name": "Autoregulación",
            "description": "Desarrolla habilidades de autorregulación emocional y motivacional",
            "order": 2,
            "icon_name": "brain"
        },
        {
            "name": "Creencias",
            "description": "Explora y modifica creencias sobre tu capacidad de cambio",
            "order": 3,
            "icon_name": "lightbulb"
        },
        {
            "name": "Señales Internas",
            "description": "Aprende a identificar y responder a señales internas de motivación",
            "order": 4,
            "icon_name": "heart"
        }
    ]
    
    # Create sections with sample contents and lessons
    for section_data in path_sections:
        section = Section(
            name=section_data["name"],
            description=section_data["description"],
            order=section_data["order"],
            icon_name=section_data["icon_name"]
        )
        db.add(section)
        db.commit()
        db.refresh(section)
        
        # Add sample contents for each section
        sample_contents = [
            {
                "title": f"Introducción a {section_data['name']}",
                "description": f"Contenido teórico sobre {section_data['name']}",
                "content_type": ContentType.VIDEO,
                "content_url": f"https://example.com/videos/{section_data['name'].lower()}_intro.mp4",
                "duration_minutes": 5,
                "order": 1
            },
            {
                "title": f"Fundamentos de {section_data['name']}",
                "description": f"Lectura fundamental sobre {section_data['name']}",
                "content_type": ContentType.TEXT,
                "content_url": f"https://example.com/texts/{section_data['name'].lower()}_fundamentos",
                "duration_minutes": 10,
                "order": 2
            }
        ]
        
        for content_data in sample_contents:
            content = Content(
                section_id=section.id,
                title=content_data["title"],
                description=content_data["description"],
                content_type=content_data["content_type"],
                content_url=content_data["content_url"],
                duration_minutes=content_data["duration_minutes"],
                order=content_data["order"]
            )
            db.add(content)
        
        # Add sample lessons for each section
        sample_lessons = [
            {
                "title": f"Lección 1: Primeros pasos en {section_data['name']}",
                "description": f"Primera lección práctica de {section_data['name']}",
                "content_url": f"https://example.com/lessons/{section_data['name'].lower()}_lesson1",
                "duration_minutes": 15,
                "order": 1
            },
            {
                "title": f"Lección 2: Práctica avanzada de {section_data['name']}",
                "description": f"Segunda lección de {section_data['name']}",
                "content_url": f"https://example.com/lessons/{section_data['name'].lower()}_lesson2",
                "duration_minutes": 20,
                "order": 2
            }
        ]
        
        for lesson_data in sample_lessons:
            lesson = Lesson(
                section_id=section.id,
                title=lesson_data["title"],
                description=lesson_data["description"],
                content_url=lesson_data["content_url"],
                duration_minutes=lesson_data["duration_minutes"],
                order=lesson_data["order"]
            )
            db.add(lesson)
    
    db.commit()
    logger.info("Siembra de secciones del path completada.")
    
    # Seed wellness exercises
    seed_wellness_exercises(db)


def seed_wellness_exercises(db: Session):
    """
    Seeds the wellness exercises (12 embodied cognition + mindfulness exercises)
    """
    logger.info("Sembrando ejercicios de bienestar...")
    
    # Check if exercises already exist
    existing_exercise = db.query(WellnessExercise).first()
    if existing_exercise:
        logger.info("Los ejercicios de bienestar ya existen. Saltando siembra.")
        return
    
    exercises_data = [
        {
            "name": "¿Qué Siento? 60s",
            "objective": "Pasar de confusión difusa a identificación corporal y etiqueta emocional/metamotivacional",
            "context": "Sentado",
            "duration_seconds": 75,
            "recommended_state": ExerciseState.CUALQUIERA,
            "taxonomy": "Conciencia interoceptiva; etiquetado afectivo; señales→hipótesis regulables",
            "body_systems": "Sensaciones viscerales, tensión muscular, respiración",
            "steps": json.dumps([
                "Marca 1–2 zonas en la silueta corporal (frente/dorso)",
                "Elige cualidad: presión/calor/tensión/cosquilleo/vacío",
                "Valora intensidad 0–10 y etiqueta emoción + sentimiento metamotivacional",
                "Nombra el posible gatillo (frase corta)"
            ]),
            "voice_scripts": json.dumps([
                "Localiza dónde lo sientes en tu cuerpo",
                "Ponle nombre a la sensación y a la emoción",
                "Observa una exhalación larga antes de seguir"
            ]),
            "measurement_notes": "Intensidad y valencia pre/post; zonas y cualidades; etiqueta elegida",
            "ux_notes": "Silueta interactiva; lista de etiquetas con buscador; círculo 60s; audio guía; hápticos suaves",
            "safeguards": "Si intensidad ≥8/10 repetida, mostrar recursos de apoyo"
        },
        {
            "name": "RND-60",
            "objective": "Interrumpir reactividad, etiquetar sensación/emoción y definir un siguiente micro‑paso",
            "context": "Sentado",
            "duration_seconds": 60,
            "recommended_state": ExerciseState.AMBAR,
            "taxonomy": "Exhalación prolongada; etiquetado; intención orientada",
            "body_systems": "Respiración; lenguaje interno; intención motora",
            "steps": json.dumps([
                "3 respiraciones nasales, exhalación más larga (~6 s)",
                "Nombra sensación y emoción en una frase breve",
                "Formula un 'siguiente paso' concreto y realizable",
                "Confirma disposición para iniciar"
            ]),
            "voice_scripts": json.dumps([
                "Exhala un poco más largo",
                "Di: 'tensión en hombros, ansiedad leve'",
                "Ahora orienta tu energía a un pequeño siguiente paso"
            ]),
            "measurement_notes": "Activación pre/post; latencia hasta iniciar (autorreporte)",
            "ux_notes": "Anillo que guía 3 respiraciones; campo de texto breve; botón 'Listo'",
            "safeguards": "Permitir 'pausar' si la activación sube"
        },
        {
            "name": "Péndulo Somático 90",
            "objective": "Aumentar tolerancia alternando foco entre zona incómoda y zona neutra",
            "context": "Sentado",
            "duration_seconds": 90,
            "recommended_state": ExerciseState.ROJO,
            "taxonomy": "Pendulación interoceptiva; flexibilidad atencional",
            "body_systems": "Propiocepción de pecho/abdomen vs. pies/manos",
            "steps": json.dumps([
                "Elige zona incómoda e intensidad inicial",
                "Elige zona neutra/agradable",
                "3 ciclos: 10 s zona A → 10 s zona B (con temporizador)",
                "Re‑valora intensidad"
            ]),
            "voice_scripts": json.dumps([
                "Observa la zona incómoda, sin forzar",
                "Cambia a una zona neutra y descansa la atención",
                "Nota qué cambió"
            ]),
            "measurement_notes": "Intensidad pre/post; Δ alivio",
            "ux_notes": "Temporizador circular que cambia de color según foco A/B; hápticos en cada cambio",
            "safeguards": "Si aumenta malestar, volver a respiración lenta o finalizar"
        },
        {
            "name": "5-4-3-2-1 + Puente",
            "objective": "Grounding multisensorial y enfoque amable hacia la siguiente acción",
            "context": "Sentado",
            "duration_seconds": 105,
            "recommended_state": ExerciseState.AMBAR,
            "taxonomy": "Exteroceptive grounding; mindful noticing",
            "body_systems": "Visión, audición, tacto/propiocepción, olfato/gusto",
            "steps": json.dumps([
                "Nombra 5 cosas que ves, 4 que oyes, 3 que tocas",
                "Identifica 2 olores/sabores presentes o recordados",
                "Formula 1 pensamiento/acto de cuidado o siguiente paso",
                "Respira lento y confirma"
            ]),
            "voice_scripts": json.dumps([
                "Mira alrededor y nombra cinco elementos visuales",
                "Escucha dos sonidos lejanos",
                "Elige una idea amable para continuar"
            ]),
            "measurement_notes": "Valencia y activación pre/post; cumplimiento del 'puente'",
            "ux_notes": "Checklist progresivo con círculo maestro; micro‑animaciones minimalistas",
            "safeguards": "Modo sin estímulos fuertes (oscuro) si hay sensibilidad"
        },
        {
            "name": "Semáforo Interoceptivo",
            "objective": "Auto‑clasificar nivel de activación y aplicar micro‑protocolo",
            "context": "Sentado",
            "duration_seconds": 52,
            "recommended_state": ExerciseState.CUALQUIERA,
            "taxonomy": "Self‑rating interoceptivo; micro‑regulación adaptativa",
            "body_systems": "Arousal percibido; respiración; tono postural",
            "steps": json.dumps([
                "Elige color: Verde/Ámbar/Rojo",
                "Aplica protocolo breve (sellar, exhalar 4×, 4‑6 breathing)",
                "Re‑valora activación",
                "Elige continuar o pausar"
            ]),
            "voice_scripts": json.dumps([
                "¿Cómo está tu activación ahora mismo?",
                "Sigamos el protocolo para tu color",
                "¿Prefieres continuar o pausar?"
            ]),
            "measurement_notes": "Arousal 0–10 pre/post; decisión; cumplimiento",
            "ux_notes": "Botones tricolores; anillo de respiraciones; feedback inmediato",
            "safeguards": "Aviso y recursos si hay activación extrema repetida"
        },
        {
            "name": "Surf del Impulso",
            "objective": "Observar y atravesar picos de impulso sin actuar",
            "context": "Sentado",
            "duration_seconds": 75,
            "recommended_state": ExerciseState.AMBAR,
            "taxonomy": "Urge surfing; inhibición amable; mindful awareness",
            "body_systems": "Interocepción del impulso; respiración",
            "steps": json.dumps([
                "Nombra el impulso y su localización corporal",
                "Observa 45–60 s la 'ola' con respiración constante",
                "Re‑valora intensidad",
                "Decide el regreso amable a tu actividad"
            ]),
            "voice_scripts": json.dumps([
                "Observa el impulso como una ola que sube y baja",
                "Respira y permanece con curiosidad",
                "¿Bajó al menos dos puntos?"
            ]),
            "measurement_notes": "Intensidad pre/post; retorno (sí/no)",
            "ux_notes": "Animación de ola con círculo de tiempo; botón 'Regresar'",
            "safeguards": "Si el impulso implica riesgo, recomendar ayuda profesional"
        },
        {
            "name": "Postura-Objetivo Snap",
            "objective": "Ajuste postural y frase corta para alinear estado e intención",
            "context": "Sentado",
            "duration_seconds": 37,
            "recommended_state": ExerciseState.VERDE,
            "taxonomy": "Embodied goal priming; regulación postural; autoeficacia",
            "body_systems": "Columna/mandíbula; voz suave",
            "steps": json.dumps([
                "Chequeo postural; liberar mandíbula",
                "Ajusta a postura neutra/erguida",
                "Exhala diciendo tu frase‑meta (6–8 palabras)",
                "Nota el cambio en claridad"
            ]),
            "voice_scripts": json.dumps([
                "Ajusta tus apoyos y suelta la mandíbula",
                "Exhala y di tu frase‑meta clara y simple"
            ]),
            "measurement_notes": "Autoeficacia 0–10 pre/post; frase registrada",
            "ux_notes": "Háptico breve al 'snap'; círculo 30 s; campo para frase",
            "safeguards": "Si hay dolor, adaptar o detener"
        },
        {
            "name": "Escaneo Amable 60",
            "objective": "De malestar difuso a claridad somática con autocompasión",
            "context": "Sentado",
            "duration_seconds": 75,
            "recommended_state": ExerciseState.CUALQUIERA,
            "taxonomy": "Body scan breve; self‑compassion; etiquetado somático",
            "body_systems": "Recorrido cabeza‑tronco‑piernas; respiración",
            "steps": json.dumps([
                "Recorre mentalmente 3 zonas (alta, media, baja)",
                "Elige el punto más presente",
                "Pon una palabra amable a la experiencia mientras exhalas",
                "Nota cualquier cambio"
            ]),
            "voice_scripts": json.dumps([
                "Explora de cabeza a pies con curiosidad",
                "Nombra en una palabra lo que sientes y sé amable contigo"
            ]),
            "measurement_notes": "Intensidad 0–10 pre/post; utilidad percibida",
            "ux_notes": "Círculo de progreso con tres segmentos; voz cálida",
            "safeguards": "Permitir saltar zonas si hay incomodidad"
        },
        {
            "name": "Anclaje Corazón-Respira",
            "objective": "Activar calma mediante contacto propioceptivo y exhalación prolongada",
            "context": "Sentado",
            "duration_seconds": 60,
            "recommended_state": ExerciseState.ROJO,
            "taxonomy": "Vagal toning; respiración 4‑6; seguridad somática",
            "body_systems": "Mano en pecho/abdomen; ritmo respiratorio",
            "steps": json.dumps([
                "Coloca una mano en el pecho y otra en el abdomen",
                "Inhala 4 s, exhala 6 s × 6 ciclos",
                "Percibe el vaivén bajo tus manos"
            ]),
            "voice_scripts": json.dumps([
                "Siente el contacto y deja que la exhalación se alargue sola"
            ]),
            "measurement_notes": "Ritmo percibido (rápido/medio/lento); activación pre/post",
            "ux_notes": "Anillo que marca ciclos; háptico al cambio inhalar/exhalar",
            "safeguards": "Si hay mareo, reducir ritmo o detener"
        },
        {
            "name": "Horizonte Periférico 3D",
            "objective": "Reducir hipervigilancia ampliando campo visual y señales de seguridad",
            "context": "Sentado",
            "duration_seconds": 75,
            "recommended_state": ExerciseState.AMBAR,
            "taxonomy": "Visual field widening; orientación contextual; grounding auditivo/táctil",
            "body_systems": "Músculos oculomotores; audición; propiocepción de apoyo",
            "steps": json.dumps([
                "Explora con la mirada izquierda‑centro‑derecha‑arriba‑abajo",
                "Suaviza enfoque para sentir visión periférica 10 s",
                "Identifica 2 sonidos y 1 sensación de apoyo"
            ]),
            "voice_scripts": json.dumps([
                "Abre tu visión como si miraras el horizonte",
                "Reconoce un sonido lejano y el apoyo de tus pies"
            ]),
            "measurement_notes": "Activación 0–10 pre/post; seguridad percibida (baja/media/alta)",
            "ux_notes": "Animación suave de expansión; círculo maestro; opción sin audio",
            "safeguards": "Si hay mareo, permitir cerrar ojos o detener"
        },
        {
            "name": "Pasos que Exhalan",
            "objective": "Descargar agitación coordinando pasos y exhalación más larga",
            "context": "De pie/en movimiento",
            "duration_seconds": 90,
            "recommended_state": ExerciseState.AMBAR,
            "taxonomy": "Walking breathing; descarga motora regulada",
            "body_systems": "Patrón de marcha; respiración; propiocepción plantar",
            "steps": json.dumps([
                "De pie: siente las plantas de los pies",
                "Camina: inhala 3 pasos, exhala 4 durante varias vueltas",
                "Nota el cambio en energía"
            ]),
            "voice_scripts": json.dumps([
                "Deja que tu exhalación dure un paso más que la inhalación"
            ]),
            "measurement_notes": "Estado (letargo/ok/agitado); Δ activación; disposición a continuar",
            "ux_notes": "Metrónomo sutil por pasos (opcional); círculo 90 s",
            "safeguards": "Usar en espacios seguros; pasillo despejado"
        },
        {
            "name": "Resonancia Mmm 60",
            "objective": "Calmar mediante vibración suave y exhalación prolongada",
            "context": "Sentado",
            "duration_seconds": 52,
            "recommended_state": ExerciseState.ROJO,
            "taxonomy": "Humming breath; regulación vagal; atención a vibración",
            "body_systems": "Laringe, cavidad oral, caja torácica",
            "steps": json.dumps([
                "Inhala nasal 3–4 s",
                "Exhala con 'mmm' 5–6 s, notando vibración",
                "Repite 5 ciclos y re‑evalúa"
            ]),
            "voice_scripts": json.dumps([
                "Siente la vibración en labios y pecho mientras exhalas"
            ]),
            "measurement_notes": "Localización de vibración (labios/pecho/cara); activación pre/post",
            "ux_notes": "Temporizador por ciclos dentro de un anillo; opción de silencio si en público",
            "safeguards": "Evitar si hay dolor de garganta agudo"
        }
    ]
    
    for exercise_data in exercises_data:
        exercise = WellnessExercise(**exercise_data)
        db.add(exercise)
    
    db.commit()
    logger.info(f"Sembraron {len(exercises_data)} ejercicios de bienestar exitosamente.")


