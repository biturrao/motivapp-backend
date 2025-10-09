from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.user import UserCreate

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    """
    Crea un nuevo usuario y su perfil asociado en una sola transacción.
    """
    # 1. Preparar el objeto de usuario
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.flush()  # Usa flush para asignar un ID a db_user sin terminar la transacción

    # 2. Preparar el objeto de perfil usando el ID del nuevo usuario
    profile_data = UserProfile(
        user_id=db_user.id,
        name=user.name,
        age=user.age,
        institution=user.institution,
        major=user.major,
        on_medication=user.on_medication,
        has_learning_difficulties=user.has_learning_difficulties,
    )
    db.add(profile_data)
    
    # 3. Guarda todo en la base de datos a la vez
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user