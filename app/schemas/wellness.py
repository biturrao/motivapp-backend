from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class WellnessExerciseBase(BaseModel):
    name: str = Field(..., description="Nombre del ejercicio")
    objective: str = Field(..., description="Objetivo del ejercicio")
    context: str = Field(..., description="Contexto (sentado, de pie, etc.)")
    duration_seconds: int = Field(..., description="Duración en segundos")
    recommended_state: str = Field(..., description="Estado recomendado: verde, ambar, rojo, cualquiera")
    taxonomy: str = Field(..., description="Qué trabaja el ejercicio")
    body_systems: str = Field(..., description="Sistemas corporales implicados")
    steps: str = Field(..., description="Pasos del ejercicio (JSON)")
    voice_scripts: str = Field(..., description="Guiones de voz (JSON)")
    measurement_notes: Optional[str] = Field(None, description="Notas de medición")
    ux_notes: Optional[str] = Field(None, description="Notas de UX/UI")
    safeguards: Optional[str] = Field(None, description="Salvaguardas")


class WellnessExerciseCreate(WellnessExerciseBase):
    """Schema para crear un ejercicio"""
    pass


class WellnessExercise(WellnessExerciseBase):
    """Schema para devolver un ejercicio"""
    id: int

    class Config:
        from_attributes = True


class MetamotivationEnergyBase(BaseModel):
    energy_state: str = Field(..., description="Estado: verde, ambar, rojo")


class MetamotivationEnergyCreate(MetamotivationEnergyBase):
    """Schema para crear un registro de energía"""
    pass


class MetamotivationEnergy(MetamotivationEnergyBase):
    """Schema para devolver un registro de energía"""
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExerciseCompletionBase(BaseModel):
    exercise_id: int
    energy_state: str = Field(..., description="Estado del semáforo cuando se realizó")
    intensity_pre: Optional[int] = Field(None, ge=0, le=10, description="Intensidad pre 0-10")
    intensity_post: Optional[int] = Field(None, ge=0, le=10, description="Intensidad post 0-10")
    user_notes: Optional[str] = Field(None, description="Notas del usuario")
    completed: bool = Field(True, description="Si se completó exitosamente")


class ExerciseCompletionCreate(ExerciseCompletionBase):
    """Schema para crear una completación"""
    pass


class ExerciseCompletionUpdate(BaseModel):
    """Schema para actualizar una completación en progreso"""
    intensity_post: Optional[int] = Field(None, ge=0, le=10)
    user_notes: Optional[str] = None
    completed: bool = True


class ExerciseCompletion(ExerciseCompletionBase):
    """Schema para devolver una completación"""
    id: int
    user_id: int
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExerciseCompletionWithExercise(ExerciseCompletion):
    """Schema que incluye los datos del ejercicio"""
    exercise: WellnessExercise


class ExerciseRecommendationRequest(BaseModel):
    """Request para obtener recomendación de ejercicio"""
    energy_state: str = Field(..., description="Estado del semáforo: verde, ambar, rojo")


class ExerciseRecommendationResponse(BaseModel):
    """Response con el ejercicio recomendado y resumen de IA"""
    exercise: WellnessExercise
    ai_summary: str = Field(..., description="Resumen personalizado generado por IA")
    reason: str = Field(..., description="Razón de la recomendación")
