"""
gateway/auth.py – JWT verification dependency for the API Gateway.
Reads the RS256 public key from the path configured in .env.
Injects the decoded payload into every protected route via FastAPI Depends().
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

_PUBLIC_KEY_PATH = os.getenv("JWT_PUBLIC_KEY_PATH", "../donation_user/public_key.pem")
_ALGORITHM       = os.getenv("JWT_ALGORITHM", "RS256")

# Resolve relative to gateway package root
_key_path = (BASE_DIR / _PUBLIC_KEY_PATH).resolve()
if not _key_path.exists():
    raise RuntimeError(f"JWT public key not found at: {_key_path}")

PUBLIC_KEY = _key_path.read_text()

# ---------------------------------------------------------------------------
# Bearer scheme (auto_error=False so we can return a clean 401)
# ---------------------------------------------------------------------------
_bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------
def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> dict[str, Any]:
    """
    FastAPI dependency.  Returns the decoded JWT payload on success.
    Raises HTTP 401 on missing / invalid / expired tokens.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            PUBLIC_KEY,
            algorithms=[_ALGORITHM],
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


# Convenience alias for type hints
TokenPayload = Annotated[dict[str, Any], Depends(require_auth)]