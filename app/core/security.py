import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# Temporäre Lösung für bcrypt-Fehler
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception as e:
    print(f"⚠️ bcrypt-Fehler: {e}")
    # Fallback auf sha256_crypt
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# JWT-Konfiguration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme_name = "oauth2"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def can_accept_or_reject_quote(user, quote):
    """Prüft ob Benutzer ein Angebot annehmen oder ablehnen kann"""
    # Projekt-Besitzer kann alle Angebote annehmen/ablehnen
    if hasattr(quote, 'milestone') and hasattr(quote.milestone, 'project'):
        if quote.milestone.project.owner_id == user.id:
            return True
    
    # Admin kann alles
    if user.email == "admin@buildwise.de":
        return True
    
    return False
