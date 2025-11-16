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


def migrate_session_states_table(db: Session):
    """
    Add new columns to session_states table if they don't exist.
    This fixes the missing onboarding_complete, strategy_given, and failed_attempts columns.
    """
    try:
        inspector = inspect(db.bind)
        
        # Check if table exists first
        if 'session_states' not in inspector.get_table_names():
            logger.info("Table session_states doesn't exist yet. Will be created by Base.metadata.create_all()")
            return
        
        columns = [col['name'] for col in inspector.get_columns('session_states')]
        
        # Add missing columns
        if 'onboarding_complete' not in columns:
            logger.info("Adding 'onboarding_complete' column to session_states table...")
            db.execute(text("ALTER TABLE session_states ADD COLUMN onboarding_complete BOOLEAN NOT NULL DEFAULT FALSE"))
            db.commit()
        
        if 'strategy_given' not in columns:
            logger.info("Adding 'strategy_given' column to session_states table...")
            db.execute(text("ALTER TABLE session_states ADD COLUMN strategy_given BOOLEAN NOT NULL DEFAULT FALSE"))
            db.commit()
        
        if 'failed_attempts' not in columns:
            logger.info("Adding 'failed_attempts' column to session_states table...")
            db.execute(text("ALTER TABLE session_states ADD COLUMN failed_attempts INTEGER NOT NULL DEFAULT 0"))
            db.commit()
        
        logger.info("Session states table migration completed.")
    except Exception as e:
        logger.error(f"Error during session_states table migration: {e}")
        db.rollback()


def seed_db(db: Session):
    """
    Siembra la base de datos con las secciones y preguntas iniciales.
    """
    # First, run migrations to add new columns if needed
    migrate_section_table(db)
    migrate_session_states_table(db)
    
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
            "name": "Pasos que Exhalan",
            "objective": "Descargar agitación coordinando pasos y exhalación más larga",
            "context": "De pie/En movimiento",
            "duration_seconds": 90,
            "recommended_state": ExerciseState.ROJO,
            "taxonomy": "Walking breathing; descarga motora regulada",
            "body_systems": "Patrón de marcha; respiración; propiocepción plantar",
            "steps": json.dumps([
                "De pie, siente las plantas de los pies",
                "Camina inhalando durante 3 pasos",
                "Exhala durante 4 pasos, haciendo la exhalación más larga",
                "Repite durante varias vueltas",
                "Nota el cambio en tu nivel de energía"
            ]),
            "voice_scripts": json.dumps([
                "Siente cómo las plantas de tus pies se conectan con el suelo",
                "Deja que tu exhalación dure un paso más que la inhalación",
                "Observa cómo la agitación va disminuyendo con cada vuelta"
            ]),
            "measurement_notes": "Estado (letargo/ok/agitado); cambio en activación; disposición a continuar",
            "ux_notes": "Metrónomo sutil por pasos (opcional); círculo visual de 90 segundos; contador de pasos",
            "safeguards": "Usar en espacios seguros; pasillo despejado; detenerse si hay mareo"
        },
        {
            "name": "Anclaje Corazón-Respira",
            "objective": "Activar calma mediante contacto propioceptivo y exhalación prolongada",
            "context": "Sentado",
            "duration_seconds": 60,
            "recommended_state": ExerciseState.AMBAR,
            "taxonomy": "Vagal toning; respiración 4-6; seguridad somática",
            "body_systems": "Mano en pecho/abdomen; ritmo respiratorio",
            "steps": json.dumps([
                "Coloca una mano en el pecho y otra en el abdomen",
                "Inhala 4 segundos, exhala 6 segundos",
                "Repite durante 6 ciclos completos",
                "Percibe el vaivén bajo tus manos"
            ]),
            "voice_scripts": json.dumps([
                "Siente el contacto cálido de tus manos",
                "Inhala lentamente por 4... exhala suavemente por 6",
                "Deja que la exhalación se alargue sin esfuerzo"
            ]),
            "measurement_notes": "Ritmo percibido (rápido/medio/lento); activación pre/post",
            "ux_notes": "Anillo que marca ciclos; háptico al cambio inhalar/exhalar; animación de corazón",
            "safeguards": "Si hay mareo, reducir ritmo o detener"
        },
        {
            "name": "Escaneo Amable 60",
            "objective": "De malestar difuso a claridad somática con autocompasión",
            "context": "Sentado",
            "duration_seconds": 75,
            "recommended_state": ExerciseState.VERDE,
            "taxonomy": "Body scan breve; self-compassion; etiquetado somático",
            "body_systems": "Recorrido cabeza-tronco-piernas; respiración",
            "steps": json.dumps([
                "Recorre mentalmente 3 zonas: cabeza y cuello, tronco, piernas",
                "Elige el punto donde sientes algo más presente",
                "Pon una palabra amable a la experiencia mientras exhalas",
                "Nota cualquier cambio en tu cuerpo"
            ]),
            "voice_scripts": json.dumps([
                "Explora de cabeza a pies con curiosidad amable",
                "¿Dónde sientes algo en este momento?",
                "Nombra en una palabra lo que sientes y sé amable contigo",
                "Nota qué cambió al reconocer tu experiencia"
            ]),
            "measurement_notes": "Intensidad 0-10 pre/post; utilidad percibida",
            "ux_notes": "Círculo de progreso con tres segmentos corporales; voz cálida; ilustración de silueta",
            "safeguards": "Permitir saltar zonas si hay incomodidad"
        },
    ]
    
    for exercise_data in exercises_data:
        exercise = WellnessExercise(**exercise_data)
        db.add(exercise)
    
    db.commit()
    logger.info(f"Sembraron {len(exercises_data)} ejercicios de bienestar exitosamente.")



