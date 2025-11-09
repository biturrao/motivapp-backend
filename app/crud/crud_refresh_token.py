from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.models.refresh_token import RefreshToken
from app.core.security import create_refresh_token


def create_user_refresh_token(
    db: Session,
    *,
    user_id: int,
    device_info: str = None,
    expires_days: int = 30
) -> RefreshToken:
    """
    Crea un nuevo refresh token para un usuario.
    """
    token_string = create_refresh_token()
    expires_at = datetime.utcnow() + timedelta(days=expires_days)
    
    refresh_token = RefreshToken(
        user_id=user_id,
        token=token_string,
        expires_at=expires_at,
        device_info=device_info
    )
    
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    
    return refresh_token


def get_refresh_token(db: Session, token: str) -> Optional[RefreshToken]:
    """
    Obtiene un refresh token por su valor.
    """
    return db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()


def revoke_refresh_token(db: Session, token: str) -> bool:
    """
    Revoca un refresh token (lo marca como inválido).
    """
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token
    ).first()
    
    if refresh_token:
        refresh_token.is_revoked = True
        db.commit()
        return True
    
    return False


def revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """
    Revoca todos los refresh tokens de un usuario.
    Útil para "cerrar sesión en todos los dispositivos".
    """
    count = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False
    ).update({"is_revoked": True})
    
    db.commit()
    return count


def cleanup_expired_tokens(db: Session) -> int:
    """
    Elimina tokens expirados de la base de datos.
    Se puede ejecutar periódicamente para mantener la BD limpia.
    """
    count = db.query(RefreshToken).filter(
        RefreshToken.expires_at < datetime.utcnow()
    ).delete()
    
    db.commit()
    return count
