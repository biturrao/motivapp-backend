from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenWithRefresh(BaseModel):
    """Token response que incluye refresh token"""
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class RefreshTokenRequest(BaseModel):
    """Request para refrescar el access token"""
    refresh_token: str

# Alias para compatibilidad
TokenPayload = TokenData
