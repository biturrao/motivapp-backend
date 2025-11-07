# mot_back/app/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando aplicación y creando tablas...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()
    
    yield
    
    print("Apagando aplicación...")

app = FastAPI(title="MetaMotivation API", version="1.0.0", lifespan=lifespan)


# Routers
app.include_router(login_endpoints.router, prefix="/api/v1", tags=["Login"])
app.include_router(user_endpoints.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(question_endpoints.router, prefix="/api/v1/questions", tags=["Questions"])
app.include_router(check_in_endpoints.router, prefix="/api/v1/check-in", tags=["Check-in"])
app.include_router(dashboard_endpoints.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(profile_endpoints.router, prefix="/api/v1", tags=["Profile"])
app.include_router(path_endpoints.router, prefix="/api/v1/path", tags=["Path"])
@app.get("/")
def read_root():
    return {"message": "Welcome to the MetaMotivation API!"}
