# app/crud/crud_chat.py

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatMessageCreate


def create_message(db: Session, user_id: int, role: str, text: str) -> ChatMessage:
    """
    Crea un nuevo mensaje de chat para un usuario.
    """
    db_message = ChatMessage(
        user_id=user_id,
        role=role,
        text=text,
        created_at=datetime.utcnow()
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_user_messages(db: Session, user_id: int, limit: Optional[int] = None) -> List[ChatMessage]:
    """
    Obtiene todos los mensajes de chat de un usuario, ordenados por fecha.
    """
    query = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).order_by(ChatMessage.created_at.asc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def delete_user_messages(db: Session, user_id: int) -> int:
    """
    Elimina todos los mensajes de chat de un usuario.
    Retorna el número de mensajes eliminados.
    """
    count = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).delete()
    db.commit()
    return count


def get_message_count(db: Session, user_id: int) -> int:
    """
    Obtiene el número total de mensajes de un usuario.
    """
    return db.query(ChatMessage).filter(ChatMessage.user_id == user_id).count()
