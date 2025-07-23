from datetime import datetime, timedelta
from typing import Optional
import hashlib
import secrets

from jose import JWTError, jwt

from .config import settings

oauth2_scheme_name = "Bearer"


def hash_password_simple(password: str) -> str:
    """Einfache Passwort-Hashing ohne bcrypt"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256()
    hash_obj.update((password + salt).encode('utf-8'))
    return f"sha256${salt}${hash_obj.hexdigest()}"


def verify_password_simple(plain_password: str, hashed_password: str) -> bool:
    """Einfache Passwort-Verifikation ohne bcrypt"""
    try:
        parts = hashed_password.split('$')
        if len(parts) != 3 or parts[0] != 'sha256':
            return False
        salt = parts[1]
        stored_hash = parts[2]
        
        hash_obj = hashlib.sha256()
        hash_obj.update((plain_password + salt).encode('utf-8'))
        return hash_obj.hexdigest() == stored_hash
    except:
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Überprüft ein Passwort - unterstützt sowohl bcrypt als auch einfaches Hashing"""
    # Prüfe ob es ein einfaches Hash ist
    if hashed_password.startswith('sha256$'):
        return verify_password_simple(plain_password, hashed_password)
    
    # Fallback zu bcrypt (falls verfügbar)
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Falls bcrypt fehlschlägt, verwende einfaches Hashing
        return verify_password_simple(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hasht ein Passwort - verwendet einfaches Hashing"""
    return hash_password_simple(password)


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