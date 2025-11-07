from pydantic import BaseModel

# Schema para leer una pregunta
class QuestionRead(BaseModel):
    id: int
    text: str
    section_name: str

    class Config:
        from_attributes = True


# Alias para compatibilidad
Question = QuestionRead


# Schema para crear una pregunta
class QuestionCreate(BaseModel):
    text: str
    section_id: int
