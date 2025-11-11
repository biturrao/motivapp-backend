# app/schemas/chat.py

from pydantic import BaseModel
from datetime import datetime
from typing import List, Literal, Optional, Dict, Any


# ---------------------------- Tipos Metamotivacionales ----------------------------

Sentimiento = Literal[
    "aburrimiento",
    "frustracion",
    "ansiedad_error",
    "dispersion_rumiacion",
    "baja_autoeficacia",
    "otro"
]

TipoTarea = Literal[
    "ensayo",
    "esquema",
    "borrador",
    "lectura_tecnica",
    "resumen",
    "resolver_problemas",
    "protocolo_lab",
    "mcq",
    "presentacion",
    "coding_bugfix",
    "proofreading"
]

Fase = Literal["ideacion", "planificacion", "ejecucion", "revision"]

Plazo = Literal["hoy", "<24h", "esta_semana", ">1_semana"]

TiempoBloque = Literal[10, 12, 15, 25]


# ---------------------------- Slots y SessionState ----------------------------

class Slots(BaseModel):
    """Información extraída del texto del usuario"""
    sentimiento: Optional[Sentimiento] = None
    sentimiento_otro: Optional[str] = None
    tipo_tarea: Optional[TipoTarea] = None
    ramo: Optional[str] = None
    plazo: Optional[Plazo] = None
    fase: Optional[Fase] = None
    tiempo_bloque: Optional[TiempoBloque] = None


class EvalResult(BaseModel):
    """Resultado de la evaluación de un bloque"""
    exito: Optional[bool] = None
    cambio_sentimiento: Optional[Literal["↑", "=", "↓"]] = None


class SessionStateSchema(BaseModel):
    """Estado de la sesión metamotivacional"""
    greeted: bool = False
    iteration: int = 0
    sentimiento_inicial: Optional[str] = None
    sentimiento_actual: Optional[str] = None
    slots: Slots = Slots()
    Q2: Optional[Literal["A", "B"]] = None
    Q3: Optional[Literal["↑", "↓", "mixto"]] = None
    enfoque: Optional[Literal["promocion_eager", "prevencion_vigilant"]] = None
    tiempo_bloque: Optional[TiempoBloque] = None
    last_strategy: Optional[str] = None
    last_eval_result: Optional[EvalResult] = None


# ---------------------------- Mensajes de Chat ----------------------------

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


class QuickReply(BaseModel):
    """Opción de respuesta rápida para el usuario"""
    label: str  # Texto que se muestra en el botón
    value: str  # Valor que se envía al backend


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    user_message: ChatMessage
    ai_message: ChatMessage
    quick_replies: Optional[List[QuickReply]] = None  # Opciones de respuesta rápida
    session_state: Optional[SessionStateSchema] = None  # Opcional para debugging


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessage]


class ProfileSummaryRequest(BaseModel):
    profile: dict


class ProfileSummaryResponse(BaseModel):
    summary: str

