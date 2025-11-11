from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
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
    Obtener un ejercicio aleatorio para el usuario que no haya completado hoy
    """
    available = get_available_exercises_for_user(db, user_id, energy_state, exclude_today=True)
    
    if not available:
        # Si ya completó todos, devolver uno aleatorio sin restricción
        available = get_exercises_by_state(db, energy_state)
    
    if not available:
        return None
    
    return random.choice(available)


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
