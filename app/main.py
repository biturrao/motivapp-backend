# mot_back/app/main.py

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

from app.db.base import Base 
from app.db.session import engine, SessionLocal
from app.db.initial_data import seed_db

from app.api.v1.endpoints import users as user_endpoints
from app.api.v1.endpoints import login as login_endpoints
from app.api.v1.endpoints import questions as question_endpoints
from app.api.v1.endpoints import check_in as check_in_endpoints
from app.api.v1.endpoints import dashboard as dashboard_endpoints
from app.api.v1.endpoints import profile as profile_endpoints
from app.api.v1.endpoints import path as path_endpoints
from app.api.v1.endpoints import ai_chat as ai_chat_endpoints
from app.api.v1.endpoints import wellness as wellness_endpoints
from app.api.v1.endpoints import feedback as feedback_endpoints

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar Rate Limiter
# Usa la IP del cliente para identificar usuarios
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando aplicación y creando tablas...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas exitosamente")
        
        db = SessionLocal()
        try:
            seed_db(db)
            logger.info("✅ Datos iniciales cargados")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Error durante el inicio: {str(e)}")
        raise
    
    yield
    
    logger.info("👋 Apagando aplicación...")

app = FastAPI(
    title="MetaMotivation API", 
    version="1.0.0", 
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Agregar limiter al estado de la app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configuración CORS para Azure
# Para apps nativas (APK), no necesitamos dominios específicos
# Solo mantenemos localhost para desarrollo local con Expo
origins = [
    "http://localhost:8081",  # Expo local (desarrollo)
    "http://localhost:19006",  # Expo web (desarrollo)
    # Las apps nativas (APK) no necesitan estar en esta lista
    # porque no tienen "origin" como los navegadores web
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(login_endpoints.router, prefix="/api/v1", tags=["Login"])
app.include_router(user_endpoints.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(question_endpoints.router, prefix="/api/v1/questions", tags=["Questions"])
app.include_router(check_in_endpoints.router, prefix="/api/v1/check-in", tags=["Check-in"])
app.include_router(dashboard_endpoints.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(profile_endpoints.router, prefix="/api/v1", tags=["Profile"])
app.include_router(path_endpoints.router, prefix="/api/v1/path", tags=["Path"])
app.include_router(ai_chat_endpoints.router, prefix="/api/v1/ai-chat", tags=["AI Chat"])
app.include_router(wellness_endpoints.router, prefix="/api/v1/wellness", tags=["Wellness"])
app.include_router(feedback_endpoints.router, prefix="/api/v1/feedback", tags=["Feedback"])

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the MetaMotivation API!",
        "status": "online",
        "environment": "Azure App Service"
    }

@app.get("/health")
def health_check():
    """Endpoint de health check para Azure"""
    return {
        "status": "healthy",
        "service": "MetaMotivation API"
    }
