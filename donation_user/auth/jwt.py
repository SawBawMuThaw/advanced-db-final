from datetime import datetime, timedelta, timezone
from typing import Any
from pathlib import Path

from jose import JWTError, jwt
from pydantic_settings import BaseSettings


class _JWTSettings(BaseSettings):
    JWT_PRIVATE_KEY_PATH: str = "private_key.pem"
    JWT_PUBLIC_KEY_PATH: str = "public_key.pem"
    JWT_ALGORITHM: str = "RS256"
    JWT_EXPIRE_MIN: int = 60

    class Config:
        env_file = ".env"
        extra = "ignore"


_cfg = _JWTSettings()

# Resolve paths relative to donation_user/ root so they work
_BASE = Path(__file__).parent.parent
PRIVATE_KEY = (_BASE / _cfg.JWT_PRIVATE_KEY_PATH).read_text()
PUBLIC_KEY  = (_BASE / _cfg.JWT_PUBLIC_KEY_PATH).read_text()


def create_access_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=_cfg.JWT_EXPIRE_MIN)
    payload.update({"exp": expire})
    return jwt.encode(payload, PRIVATE_KEY, algorithm=_cfg.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, PUBLIC_KEY, algorithms=[_cfg.JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc