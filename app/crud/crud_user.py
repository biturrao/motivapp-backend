from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.user import UserCreate, PsychologistCreate # <-- CAMBIO: Importar PsychologistCreate

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    """
    Crea un nuevo usuario ALUMNO y su perfil asociado.
    """
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        role="student"  # <-- CAMBIO: Hardcodeamos el rol de "student"
    )
    db.add(db_user)
    db.flush() # Obtenemos el ID del usuario antes de crear el perfil

    # --- Creación del perfil (sin cambios) ---
    profile_data = UserProfile(
        user_id=db_user.id,
        name=user.name,
        age=user.age,
        institution=user.institution,
        major=user.major,
        entry_year=user.entry_year,
        course_types=user.course_types,
        family_responsibilities=user.family_responsibilities,
        is_working=user.is_working,
        mental_health_support=user.mental_health_support,
        mental_health_details=user.mental_health_details,
        chronic_condition=user.chronic_condition,
        chronic_condition_details=user.chronic_condition_details,
        neurodivergence=user.neurodivergence,
        neurodivergence_details=user.neurodivergence_details,
        preferred_support_types=user.preferred_support_types,
    )
    db.add(profile_data)
    
    db.commit()
    db.refresh(db_user)
    return db_user

# --- CAMBIO: Nueva función para crear psicólogos ---
def create_psychologist_user(db: Session, user: PsychologistCreate) -> User:
    """
    Crea un nuevo usuario PSICÓLOGO.
    Este usuario no tiene un UserProfile.
    """
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        role="psychologist" # Asignamos el rol de psicólogo
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
# --- Fin del cambio ---

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
