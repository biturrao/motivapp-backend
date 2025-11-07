# app/schemas/answer.py
from pydantic import BaseModel
from typing import List

# Schema para una única respuesta que se recibe
class AnswerCreate(BaseModel):
    question_id: int
    value: int # El valor de la respuesta, ej. de 1 a 5

# Schema para la lista de respuestas que enviará el frontend
class AnswersRequest(BaseModel):
    answers: List[AnswerCreate]

class QuestionForAnswer(BaseModel):
    """Schema mínimo para mostrar el texto de la pregunta junto a la respuesta."""
    id: int
    text: str

    class Config:
        from_attributes = True

class AnswerRead(BaseModel):
    """Schema para LEER una respuesta (para el panel de psicólogo)."""
    id: int
    question_id: int
    value: int
    question: QuestionForAnswer  # Anidamos el texto de la pregunta

    class Config:
        from_attributes = True


# Alias para compatibilidad
Answer = AnswerRead