# app/crud/crud_session.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, ProgrammingError
from typing import Optional
from datetime import datetime
import json
import logging

from app.models.session_state import SessionState
from app.schemas.chat import SessionStateSchema, Slots, EvalResult

logger = logging.getLogger(__name__)


def get_or_create_session(db: Session, user_id: int) -> SessionState:
    """
    Obtiene o crea una sesión para el usuario.
    Si la tabla no existe, retorna una sesión temporal en memoria.
    """
    try:
        session = db.query(SessionState).filter(SessionState.user_id == user_id).first()
        
        if not session:
            session = SessionState(
                user_id=user_id,
                greeted=False,
                iteration=0,
                slots={},
                last_eval_result={}
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        
        return session
    except (OperationalError, ProgrammingError) as e:
        logger.warning(f"Tabla session_states no existe aún. Usando sesión temporal en memoria: {e}")
        # Retornar sesión temporal sin persistencia
        session = SessionState(
            user_id=user_id,
            greeted=False,
            iteration=0,
            slots={},
            last_eval_result={}
        )
        session.id = 0  # ID temporal
        return session


def update_session(db: Session, user_id: int, session_data: SessionStateSchema) -> SessionState:
    """
    Actualiza el estado de la sesión del usuario.
    Si la tabla no existe, solo retorna la sesión actualizada sin persistir.
    """
    try:
        session = get_or_create_session(db, user_id)
        
        # Actualizar campos
        session.greeted = session_data.greeted
        session.iteration = session_data.iteration
        session.sentimiento_inicial = session_data.sentimiento_inicial
        session.sentimiento_actual = session_data.sentimiento_actual
        session.slots = session_data.slots.model_dump()
        session.Q2 = session_data.Q2
        session.Q3 = session_data.Q3
        session.enfoque = session_data.enfoque
        session.tiempo_bloque = session_data.tiempo_bloque
        session.last_strategy = session_data.last_strategy
        session.last_eval_result = session_data.last_eval_result.model_dump() if session_data.last_eval_result else {}
        session.updated_at = datetime.utcnow()
        
        # Solo intentar commit si la sesión tiene ID real
        if session.id != 0:
            db.commit()
            db.refresh(session)
        
        return session
    except (OperationalError, ProgrammingError) as e:
        logger.warning(f"No se pudo persistir la sesión: {e}")
        return session


def session_to_schema(session: SessionState) -> SessionStateSchema:
    """
    Convierte el modelo de SessionState a SessionStateSchema.
    """
    slots_dict = session.slots if isinstance(session.slots, dict) else {}
    eval_dict = session.last_eval_result if isinstance(session.last_eval_result, dict) else {}
    
    return SessionStateSchema(
        greeted=session.greeted,
        iteration=session.iteration,
        sentimiento_inicial=session.sentimiento_inicial,
        sentimiento_actual=session.sentimiento_actual,
        slots=Slots(**slots_dict),
        Q2=session.Q2,
        Q3=session.Q3,
        enfoque=session.enfoque,
        tiempo_bloque=session.tiempo_bloque,
        last_strategy=session.last_strategy,
        last_eval_result=EvalResult(**eval_dict) if eval_dict else None
    )


def reset_session(db: Session, user_id: int) -> SessionState:
    """
    Reinicia la sesión del usuario.
    Si la tabla no existe, retorna una nueva sesión temporal limpia.
    """
    try:
        session = get_or_create_session(db, user_id)
        
        session.greeted = False
        session.iteration = 0
        session.sentimiento_inicial = None
        session.sentimiento_actual = None
        session.slots = {}
        session.Q2 = None
        session.Q3 = None
        session.enfoque = None
        session.tiempo_bloque = None
        session.last_strategy = None
        session.last_eval_result = {}
        session.updated_at = datetime.utcnow()
        
        # Solo intentar commit si la sesión tiene ID real
        if session.id != 0:
            db.commit()
            db.refresh(session)
        
        return session
    except (OperationalError, ProgrammingError) as e:
        logger.warning(f"No se pudo resetear la sesión: {e}")
        # Retornar sesión limpia temporal
        return SessionState(
            id=0,
            user_id=user_id,
            greeted=False,
            iteration=0,
            sentimiento_inicial=None,
            sentimiento_actual=None,
            slots={},
            Q2=None,
            Q3=None,
            enfoque=None,
            tiempo_bloque=None,
            last_strategy=None,
            last_eval_result={},
            updated_at=datetime.utcnow()
        )
