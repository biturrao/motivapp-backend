"""
Script para limpiar ejercicios antiguos y recargar solo los 3 ejercicios nuevos
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.wellness_exercise import WellnessExercise
from app.db.initial_data import seed_wellness_exercises
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_old_exercises(db: Session):
    """Eliminar todos los ejercicios antiguos"""
    try:
        # Contar ejercicios existentes
        count = db.query(WellnessExercise).count()
        logger.info(f"Ejercicios existentes: {count}")
        
        if count > 0:
            # Eliminar todos los ejercicios
            db.query(WellnessExercise).delete()
            db.commit()
            logger.info(f"✅ Eliminados {count} ejercicios antiguos")
        else:
            logger.info("No hay ejercicios para eliminar")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error eliminando ejercicios: {e}")
        db.rollback()
        return False


def main():
    """Limpiar y recargar ejercicios"""
    logger.info("🔄 Iniciando limpieza de ejercicios...")
    
    db = SessionLocal()
    
    try:
        # 1. Limpiar ejercicios antiguos
        if clean_old_exercises(db):
            logger.info("✅ Ejercicios antiguos eliminados")
            
            # 2. Cargar los 3 nuevos ejercicios
            logger.info("📥 Cargando 3 ejercicios nuevos...")
            seed_wellness_exercises(db)
            
            # 3. Verificar
            new_count = db.query(WellnessExercise).count()
            logger.info(f"✅ Total de ejercicios en base de datos: {new_count}")
            
            # Mostrar los ejercicios
            exercises = db.query(WellnessExercise).all()
            logger.info("\n📋 Ejercicios cargados:")
            for ex in exercises:
                logger.info(f"  - {ex.name} ({ex.recommended_state})")
            
            logger.info("\n🎉 ¡Limpieza completada exitosamente!")
        else:
            logger.error("❌ Error en la limpieza, no se cargarán nuevos ejercicios")
    
    except Exception as e:
        logger.error(f"❌ Error general: {e}")
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
