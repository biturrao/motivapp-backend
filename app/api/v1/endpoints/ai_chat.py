# app/api/v1/endpoints/ai_chat.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
import json

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.chat import (
    ChatRequest, ChatResponse, ChatHistoryResponse, 
    ProfileSummaryRequest, ProfileSummaryResponse, ChatMessage as ChatMessageSchema
)
from app.crud import crud_chat
from app.crud import crud_session
from app.services.ai_service import handle_user_turn, generate_profile_summary
from app.crud.crud_user_profile import get_profile
from app.crud.crud_daily_check_in import get_latest_checkin
from app.crud.crud_dashboard import get_questionnaire_summary

logger = logging.getLogger(__name__)

router = APIRouter()


def build_user_context(db: Session, user: User) -> str:
    """
    Construye el contexto del usuario para personalizar las respuestas de la IA.
    """
    try:
        context_string = "Contexto del usuario (no lo menciones directamente, úsalo para personalizar): "
        
        # Obtener último check-in
        last_checkin = get_latest_checkin(db, user.id)
        if last_checkin:
            context_string += f"Último check-in de motivación: {last_checkin.motivation_level}/6. "
        
        # Obtener resumen del cuestionario
        summary = get_questionnaire_summary(db, user_id=user.id)
        if summary:
            context_string += "Resumen cuestionario meta-motivación: "
            summary_parts = [f"{s['section_name']} promedio {s['average_score']:.1f}/7" for s in summary]
            context_string += ", ".join(summary_parts) + ". "
        
        # Obtener perfil
        profile = get_profile(db, user.id)
        if profile:
            context_string += "Perfil: "
            profile_parts = []
            
            if profile.name:
                profile_parts.append(f"nombre {profile.name}")
            if profile.age:
                profile_parts.append(f"edad {profile.age}")
            if profile.institution:
                profile_parts.append(f"institución {profile.institution}")
            if profile.major:
                profile_parts.append(f"carrera {profile.major}")
            if profile.entry_year:
                profile_parts.append(f"año ingreso {profile.entry_year}")
            if profile.course_types:
                profile_parts.append(f"tipo asignaturas: {profile.course_types}")
            if profile.family_responsibilities:
                profile_parts.append(f"responsabilidades familiares: {profile.family_responsibilities}")
            if profile.is_working:
                profile_parts.append(f"situación laboral: {profile.is_working}")
            if profile.mental_health_support:
                profile_parts.append(f"apoyo salud mental: {profile.mental_health_support}")
            if profile.chronic_condition:
                profile_parts.append(f"condición crónica: {profile.chronic_condition}")
            if profile.neurodivergence:
                profile_parts.append(f"neurodivergencia: {profile.neurodivergence}")
            
            if profile_parts:
                context_string += ", ".join(profile_parts) + ". "
        
        return context_string
        
    except Exception as e:
        logger.warning(f"No se pudo construir el contexto completo del usuario: {e}")
        return ""


@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Envía un mensaje al chatbot y obtiene una respuesta.
    Usa el sistema metamotivacional de Flou (Miele & Scholer).
    Guarda ambos mensajes en el historial del usuario.
    """
    try:
        # Crear el mensaje del usuario
        user_message = crud_chat.create_message(
            db=db,
            user_id=current_user.id,
            role='user',
            text=request.message
        )
        
        # Obtener o crear sesión metamotivacional
        session_db = crud_session.get_or_create_session(db, current_user.id)
        session_schema = crud_session.session_to_schema(session_db)
        
        # Obtener historial reciente de mensajes (últimos 10)
        chat_history_db = crud_chat.get_user_messages(db, current_user.id, limit=10)
        chat_history = [
            {"role": msg.role, "text": msg.text} 
            for msg in chat_history_db
        ]
        
        # Construir contexto del usuario
        context = build_user_context(db, current_user)
        
        # Procesar con el orquestador metamotivacional
        ai_response_text, updated_session, quick_replies = await handle_user_turn(
            session=session_schema,
            user_text=request.message,
            context=context,
            chat_history=chat_history
        )
        
        # Guardar sesión actualizada
        crud_session.update_session(db, current_user.id, updated_session)
        
        # Crear el mensaje de la IA
        ai_message = crud_chat.create_message(
            db=db,
            user_id=current_user.id,
            role='model',
            text=ai_response_text
        )
        
        return ChatResponse(
            user_message=ChatMessageSchema.from_orm(user_message),
            ai_message=ChatMessageSchema.from_orm(ai_message),
            quick_replies=quick_replies,  # Incluir opciones de respuesta rápida
            session_state=updated_session  # Opcional para debugging
        )
        
    except Exception as e:
        logger.error(f"Error procesando mensaje de chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al procesar el mensaje")


@router.get("/history", response_model=ChatHistoryResponse)
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el historial de chat del usuario actual.
    """
    try:
        messages = crud_chat.get_user_messages(db, current_user.id)
        return ChatHistoryResponse(
            messages=[ChatMessageSchema.from_orm(msg) for msg in messages]
        )
    except Exception as e:
        logger.error(f"Error obteniendo historial de chat: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener el historial")


@router.delete("/history")
def clear_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina todo el historial de chat del usuario actual.
    También reinicia la sesión metamotivacional.
    """
    try:
        # Eliminar mensajes
        count = crud_chat.delete_user_messages(db, current_user.id)
        
        # Reiniciar sesión
        crud_session.reset_session(db, current_user.id)
        
        return {
            "message": f"Se eliminaron {count} mensajes del historial y se reinició la sesión",
            "count": count
        }
    except Exception as e:
        logger.error(f"Error eliminando historial de chat: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar el historial")


@router.post("/profile-summary", response_model=ProfileSummaryResponse)
async def get_profile_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera un resumen personalizado del perfil del usuario usando IA.
    """
    try:
        # Obtener el perfil del usuario
        profile = get_profile(db, current_user.id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Perfil no encontrado")
        
        # Convertir el perfil a diccionario
        profile_dict = {
            "name": profile.name,
            "age": profile.age,
            "institution": profile.institution,
            "major": profile.major,
            "entry_year": profile.entry_year,
            "course_types": profile.course_types,
            "family_responsibilities": profile.family_responsibilities,
            "is_working": profile.is_working,
            "mental_health_support": profile.mental_health_support,
            "mental_health_details": profile.mental_health_details,
            "chronic_condition": profile.chronic_condition,
            "chronic_condition_details": profile.chronic_condition_details,
            "neurodivergence": profile.neurodivergence,
            "neurodivergence_details": profile.neurodivergence_details,
            "preferred_support_types": profile.preferred_support_types,
        }
        
        # Generar el resumen
        summary = await generate_profile_summary(profile_dict)
        
        return ProfileSummaryResponse(summary=summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando resumen de perfil: {e}")
        raise HTTPException(status_code=500, detail="Error al generar el resumen del perfil")

