from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
import random

from app.models.wellness_exercise import WellnessExercise, ExerciseState
from app.models.exercise_completion import ExerciseCompletion
from app.schemas.wellness import WellnessExerciseCreate


def get_exercise(db: Session, exercise_id: int) -> Optional[WellnessExercise]:
    """Obtener un ejercicio por ID"""
    return db.query(WellnessExercise).filter(WellnessExercise.id == exercise_id).first()


def get_exercise_by_name(db: Session, name: str) -> Optional[WellnessExercise]:
    """Obtener un ejercicio por nombre"""
    return db.query(WellnessExercise).filter(WellnessExercise.name == name).first()


def get_exercises(db: Session, skip: int = 0, limit: int = 100) -> List[WellnessExercise]:
    """Obtener lista de ejercicios"""
    return db.query(WellnessExercise).offset(skip).limit(limit).all()


def get_exercises_by_state(
    db: Session, 
    energy_state: str,
    skip: int = 0,
    limit: int = 100
) -> List[WellnessExercise]:
    """
    Obtener ejercicios filtrados por estado del semáforo.
    Incluye ejercicios que coincidan con el estado O que sean para 'cualquiera'
    """
    state_enum = ExerciseState(energy_state.lower())
    
    return db.query(WellnessExercise).filter(
        (WellnessExercise.recommended_state == state_enum) |
        (WellnessExercise.recommended_state == ExerciseState.CUALQUIERA)
    ).offset(skip).limit(limit).all()


def get_available_exercises_for_user(
    db: Session,
    user_id: int,
    energy_state: str,
    exclude_today: bool = True
) -> List[WellnessExercise]:
    """
    Obtener ejercicios disponibles para un usuario según su estado.
    Si exclude_today=True, excluye ejercicios ya completados hoy.
    """
    # Obtener ejercicios válidos para el estado
    valid_exercises = get_exercises_by_state(db, energy_state)
    
    if not exclude_today:
        return valid_exercises
    
    # Obtener IDs de ejercicios completados hoy
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    completed_today = db.query(ExerciseCompletion.exercise_id).filter(
        and_(
            ExerciseCompletion.user_id == user_id,
            ExerciseCompletion.started_at >= today_start,
            ExerciseCompletion.completed == True
        )
    ).all()
    
    completed_ids = {c[0] for c in completed_today}
    
    # Filtrar ejercicios no completados
    available = [ex for ex in valid_exercises if ex.id not in completed_ids]
    
    return available


def get_random_exercise_for_user(
    db: Session,
    user_id: int,
    energy_state: str
) -> Optional[WellnessExercise]:
    """
    Obtener el siguiente ejercicio en la secuencia para el usuario.
    Ciclo: 1 -> 2 -> 3 -> 1
    """
    # 1. Obtener todos los ejercicios válidos para el estado
    valid_exercises = get_exercises_by_state(db, energy_state)
    if not valid_exercises:
        return None
        
    # Ordenar por ID para asegurar orden consistente
    valid_exercises.sort(key=lambda x: x.id)
    
    # 2. Buscar la última completación que coincida con alguno de la lista
    valid_ids = [ex.id for ex in valid_exercises]
    last_matching_completion = db.query(ExerciseCompletion).filter(
        and_(
            ExerciseCompletion.user_id == user_id,
            ExerciseCompletion.exercise_id.in_(valid_ids)
        )
    ).order_by(desc(ExerciseCompletion.started_at)).first()
    
    if last_matching_completion:
        # Encontrar el índice del último ejercicio
        try:
            last_index = next(
                i for i, ex in enumerate(valid_exercises) 
                if ex.id == last_matching_completion.exercise_id
            )
            # Devolver el siguiente (circular)
            return valid_exercises[(last_index + 1) % len(valid_exercises)]
        except StopIteration:
            # Fallback por si acaso
            return valid_exercises[0]
            
    # Si no ha hecho ninguno de esta lista, devolver el primero
    return valid_exercises[0]


def create_exercise(db: Session, exercise: WellnessExerciseCreate) -> WellnessExercise:
    """Crear un nuevo ejercicio"""
    db_exercise = WellnessExercise(**exercise.model_dump())
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise


def delete_exercise(db: Session, exercise_id: int) -> bool:
    """
    Eliminar un ejercicio por ID.
    Retorna True si se eliminó, False si no existía.
    """
    exercise = db.query(WellnessExercise).filter(WellnessExercise.id == exercise_id).first()
    if not exercise:
        return False
    
    db.delete(exercise)
    db.commit()
    return True


def get_user_exercise_stats(db: Session, user_id: int, days: int = 30) -> dict:
    """
    Obtener estadísticas de ejercicios del usuario en los últimos N días
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    completions = db.query(ExerciseCompletion).filter(
        and_(
            ExerciseCompletion.user_id == user_id,
            ExerciseCompletion.started_at >= since,
            ExerciseCompletion.completed == True
        )
    ).all()
    
    total_completed = len(completions)
    
    # Contar por estado
    by_state = {}
    for c in completions:
        by_state[c.energy_state] = by_state.get(c.energy_state, 0) + 1
    
    # Calcular promedio de mejora (intensidad pre - post)
    improvements = [
        c.intensity_pre - c.intensity_post 
        for c in completions 
        if c.intensity_pre is not None and c.intensity_post is not None
    ]
    avg_improvement = sum(improvements) / len(improvements) if improvements else 0
    
    return {
        "total_completed": total_completed,
        "by_state": by_state,
        "avg_improvement": round(avg_improvement, 2),
        "days_analyzed": days
    }
