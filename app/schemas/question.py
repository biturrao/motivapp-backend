from pydantic import BaseModel

# Schema para leer una pregunta
class QuestionRead(BaseModel):
    id: int
    text: str
    section_name: str

    class Config:
        from_attributes = True
