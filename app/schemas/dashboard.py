from pydantic import BaseModel
from typing import List

class SectionAverage(BaseModel):
    section_name: str
    average_score: float

class QuestionnaireSummaryResponse(BaseModel):
    summary: List[SectionAverage]
