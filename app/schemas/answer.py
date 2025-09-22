from pydantic import BaseModel
from typing import List

# Schema para una única respuesta que se recibe
class AnswerCreate(BaseModel):
    question_id: int
    value: int # El valor de la respuesta, ej. de 1 a 5

# Schema para la lista de respuestas que enviará el frontend
class AnswersRequest(BaseModel):
    answers: List[AnswerCreate]
