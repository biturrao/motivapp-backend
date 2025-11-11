from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.wellness import (
    WellnessExercise,
    MetamotivationEnergy,
    MetamotivationEnergyCreate,
    ExerciseCompletion,
    ExerciseCompletionCreate,
    ExerciseCompletionUpdate,
    ExerciseCompletionWithExercise,
    ExerciseRecommendationRequest,
    ExerciseRecommendationResponse
)
from app.crud import crud_wellness, crud_energy, crud_completion
from app.services.ai_service import model
import json

router = APIRouter()


@router.post("/energy", response_model=MetamotivationEnergy, status_code=status.HTTP_201_CREATED)
def save_energy_state(
    energy_data: MetamotivationEnergyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Guardar el estado de energía metamotivacional del usuario
    (selección del semáforo: verde, ambar, rojo)
    """
    # Validar que el estado sea válido
    valid_states = ["verde", "ambar", "rojo"]
    if energy_data.energy_state.lower() not in valid_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estado inválido. Debe ser uno de: {', '.join(valid_states)}"
        )
    
    return crud_energy.create_energy_record(db, current_user.id, energy_data)


@router.get("/energy/history", response_model=List[MetamotivationEnergy])
def get_energy_history(
    skip: int = 0,
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener el historial de estados de energía del usuario"""
    return crud_energy.get_energy_records(db, current_user.id, skip, limit)


@router.get("/energy/today", response_model=List[MetamotivationEnergy])
def get_todays_energy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener los registros de energía de hoy"""
    return crud_energy.get_todays_energy_records(db, current_user.id)


@router.get("/energy/stats")
def get_energy_statistics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener estadísticas de energía de los últimos N días"""
    return crud_energy.get_energy_stats(db, current_user.id, days)


@router.post("/exercises/recommend", response_model=ExerciseRecommendationResponse)
def get_exercise_recommendation(
    request: ExerciseRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener una recomendación de ejercicio basada en el estado del semáforo.
    La IA genera un resumen personalizado del ejercicio.
    """
    energy_state = request.energy_state.lower()
    
    # Validar estado
    valid_states = ["verde", "ambar", "rojo"]
    if energy_state not in valid_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estado inválido. Debe ser uno de: {', '.join(valid_states)}"
        )
    
    # Obtener un ejercicio aleatorio que no se haya hecho hoy
    exercise = crud_wellness.get_random_exercise_for_user(db, current_user.id, energy_state)
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron ejercicios disponibles para este estado"
        )
    
    # Parsear los pasos y scripts de voz
    try:
        steps_list = json.loads(exercise.steps)
        voice_scripts = json.loads(exercise.voice_scripts)
    except json.JSONDecodeError:
        steps_list = [exercise.steps]
        voice_scripts = [exercise.voice_scripts]
    
    # Generar resumen con IA
    prompt = f"""
Como Newra, el asistente de bienestar de MetaMind, genera un resumen breve y motivador para el siguiente ejercicio de mindfulness.

El usuario ha indicado que su estado de metamotivación actual es: **{energy_state}**

**Ejercicio seleccionado:**
- Nombre: {exercise.name}
- Objetivo: {exercise.objective}
- Duración: {exercise.duration_seconds} segundos
- Contexto: {exercise.context}

**Lo que trabaja:**
{exercise.taxonomy}

**Pasos básicos:**
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(steps_list[:3]))}

Genera un resumen de 2-3 oraciones que:
1. Valide cómo se siente el usuario según su estado del semáforo
2. Explique brevemente cómo este ejercicio le ayudará
3. Sea motivador y empático

Responde SOLO con el resumen, sin saludos ni despedidas.
"""
    
    try:
        response = model.generate_content(prompt)
        ai_summary = response.text.strip()
    except Exception as e:
        # Fallback si falla la IA
        ai_summary = f"Este ejercicio de {exercise.duration_seconds} segundos te ayudará a trabajar en {exercise.taxonomy.split(';')[0]}. Es perfecto para tu estado actual."
    
    # Determinar la razón de la recomendación
    estado_map = {
        "verde": "equilibrio y claridad",
        "ambar": "regulación y enfoque",
        "rojo": "calma y restauración"
    }
    
    reason = f"Este ejercicio es ideal para tu estado actual de {estado_map[energy_state]}"
    
    return ExerciseRecommendationResponse(
        exercise=exercise,
        ai_summary=ai_summary,
        reason=reason
    )


@router.get("/exercises", response_model=List[WellnessExercise])
def get_all_exercises(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener todos los ejercicios disponibles"""
    return crud_wellness.get_exercises(db, skip, limit)


@router.get("/exercises/{exercise_id}", response_model=WellnessExercise)
def get_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener un ejercicio específico por ID"""
    exercise = crud_wellness.get_exercise(db, exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ejercicio no encontrado"
        )
    return exercise


@router.delete("/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar un ejercicio específico por ID.
    Esto también eliminará todas las completaciones asociadas debido al cascade.
    """
    deleted = crud_wellness.delete_exercise(db, exercise_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ejercicio no encontrado"
        )
    return None


@router.post("/exercises/complete", response_model=ExerciseCompletion, status_code=status.HTTP_201_CREATED)
def complete_exercise_direct(
    completion_data: ExerciseCompletionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Completar un ejercicio directamente (sin dos pasos).
    Crea un registro de completación con mediciones pre y post.
    """
    # Verificar que el ejercicio existe
    exercise = crud_wellness.get_exercise(db, completion_data.exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ejercicio no encontrado"
        )
    
    # Crear la completación
    completion = crud_completion.create_completion(db, current_user.id, completion_data)
    
    # Si tiene intensidad post, marcar como completado
    if completion_data.intensity_post is not None:
        update_data = ExerciseCompletionUpdate(
            intensity_post=completion_data.intensity_post,
            completed_at=True
        )
        completion = crud_completion.update_completion(db, completion.id, update_data)
    
    return completion


@router.post("/completions", response_model=ExerciseCompletion, status_code=status.HTTP_201_CREATED)
def start_exercise(
    completion_data: ExerciseCompletionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Iniciar un ejercicio (crear registro de completación).
    El usuario puede actualizar este registro después con las mediciones post.
    """
    # Verificar que el ejercicio existe
    exercise = crud_wellness.get_exercise(db, completion_data.exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ejercicio no encontrado"
        )
    
    return crud_completion.create_completion(db, current_user.id, completion_data)


@router.patch("/completions/{completion_id}", response_model=ExerciseCompletion)
def complete_exercise(
    completion_id: int,
    completion_update: ExerciseCompletionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar una completación de ejercicio (marcar como completado, agregar mediciones post)
    """
    # Verificar que la completación existe y pertenece al usuario
    completion = crud_completion.get_completion(db, completion_id)
    if not completion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de completación no encontrado"
        )
    
    if completion.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar esta completación"
        )
    
    updated = crud_completion.update_completion(db, completion_id, completion_update)
    return updated


@router.get("/completions", response_model=List[ExerciseCompletion])
def get_my_completions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener el historial de completaciones del usuario"""
    return crud_completion.get_user_completions(db, current_user.id, skip, limit)


@router.get("/completions/today", response_model=List[ExerciseCompletion])
def get_todays_completions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener las completaciones de hoy"""
    return crud_completion.get_todays_completions(db, current_user.id)


@router.get("/stats")
def get_wellness_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener estadísticas de bienestar: racha y total de ejercicios completados"""
    streak = crud_completion.get_completion_streak(db, current_user.id)
    total_completions = crud_completion.get_total_completions(db, current_user.id)
    last_completion = crud_completion.get_last_completion_date(db, current_user.id)
    
    return {
        "streak": streak,
        "total_completions": total_completions,
        "last_completion": last_completion
    }


@router.get("/stats/exercises")
def get_exercise_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener estadísticas de ejercicios completados"""
    return crud_wellness.get_user_exercise_stats(db, current_user.id, days)


@router.get("/stats/streak")
def get_completion_streak(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener la racha de días consecutivos con ejercicios completados"""
    streak = crud_completion.get_completion_streak(db, current_user.id)
    return {"streak_days": streak}
