import base64
import hashlib
import json
import os
from datetime import UTC, datetime, timedelta

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jwt import InvalidTokenError, decode, encode
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(subject: str, session_id: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE)
    return encode(
        {"sub": subject, "sid": session_id, "exp": expires_at},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict | None:
    try:
        return decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except InvalidTokenError:
        return None


def _key() -> bytes:
    configured = settings.CREDENTIALS_ENCRYPTION_KEY
    if configured:
        try:
            decoded = base64.urlsafe_b64decode(configured.encode())
            if len(decoded) == 32:
                return decoded
        except ValueError:
            pass
    return hashlib.sha256((settings.SECRET_KEY or "development-key").encode()).digest()


def encrypt_credentials(value: dict) -> tuple[str, str]:
    nonce = os.urandom(12)
    encrypted = AESGCM(_key()).encrypt(nonce, _json_bytes(value), None)
    return base64.urlsafe_b64encode(encrypted).decode(), base64.urlsafe_b64encode(
        nonce
    ).decode()


def decrypt_credentials(encrypted: str, nonce: str) -> dict:
    payload = AESGCM(_key()).decrypt(
        base64.urlsafe_b64decode(nonce), base64.urlsafe_b64decode(encrypted), None
    )
    import json

    return json.loads(payload)


def _json_bytes(value: dict) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode()
