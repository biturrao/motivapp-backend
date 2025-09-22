import logging
from sqlalchemy.orm import Session

from app.models.section import Section
from app.models.question import Question

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

def seed_db(db: Session):
    """
    Siembra la base de datos con las secciones y preguntas iniciales.
    """
    # Comprueba si ya existen datos para no duplicar
    first_section = db.query(Section).first()
    if first_section:
        logger.info("La base de datos ya contiene datos iniciales. Saltando siembra.")
        return

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

