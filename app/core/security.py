from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

oauth2_scheme_name = "Bearer"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=expires_delta or settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def can_accept_or_reject_quote(user, quote):
    """Prüft, ob der User ein Angebot annehmen/ablehnen darf (Owner, Admin, Superuser)"""
    if not quote or not getattr(quote, 'project', None):
        return False
    if getattr(user, 'id', None) == getattr(quote.project, 'owner_id', None):
        return True
    # Erlaube auch Admin-User (nicht nur 'admin' und 'superuser')
    user_type = getattr(user, 'user_type', '')
    if user_type in ("admin", "superuser", "super_admin"):
        return True
    # Zusätzlich: Erlaube User mit E-Mail admin@buildwise.de (Fallback)
    if getattr(user, 'email', '') == 'admin@buildwise.de':
        return True
    return False
