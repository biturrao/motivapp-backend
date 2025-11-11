"""
Script para probar la eliminación de ejercicios
"""
import sys
import os

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.wellness_exercise import WellnessExercise
from app.models.exercise_completion import ExerciseCompletion
from app.crud import crud_wellness


def main():
    """Probar eliminación de ejercicios"""
    db = SessionLocal()
    
    try:
        # Listar todos los ejercicios
        print("\n📋 Ejercicios existentes:")
        exercises = db.query(WellnessExercise).all()
        
        if not exercises:
            print("  ❌ No hay ejercicios en la base de datos")
            return
        
        for ex in exercises:
            # Contar completaciones
            completions_count = db.query(ExerciseCompletion).filter(
                ExerciseCompletion.exercise_id == ex.id
            ).count()
            
            print(f"  - ID: {ex.id} | {ex.name} ({ex.recommended_state}) | Completaciones: {completions_count}")
        
        # Preguntar cuál eliminar
        print("\n🗑️  Para eliminar un ejercicio:")
        print("  1. Usa el endpoint DELETE /api/v1/wellness/exercises/{exercise_id}")
        print("  2. O usa el CRUD: crud_wellness.delete_exercise(db, exercise_id)")
        
        # Ejemplo de cómo usarlo programáticamente
        print("\n📝 Ejemplo de uso en Python:")
        print("  from app.crud import crud_wellness")
        print("  from app.db.session import SessionLocal")
        print("  ")
        print("  db = SessionLocal()")
        print("  deleted = crud_wellness.delete_exercise(db, exercise_id=1)")
        print("  if deleted:")
        print("      print('Ejercicio eliminado')")
        print("  else:")
        print("      print('Ejercicio no encontrado')")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
