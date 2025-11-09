# app/schemas/chat.py

from pydantic import BaseModel
from datetime import datetime
from typing import List, Literal


class ChatMessageBase(BaseModel):
    role: Literal['user', 'model']
    text: str


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessage(ChatMessageBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    user_message: ChatMessage
    ai_message: ChatMessage


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessage]


class ProfileSummaryRequest(BaseModel):
    profile: dict


class ProfileSummaryResponse(BaseModel):
    summary: str
