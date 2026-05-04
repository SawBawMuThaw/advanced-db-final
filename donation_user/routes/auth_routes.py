from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..auth.hashing import hash_password, verify_password
from ..auth.jwt import create_access_token
from ..models.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from ..repository.user_repo import UserRepository

router = APIRouter(tags=["auth"])
_users = UserRepository()


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """Authenticate a user and return a JWT (RS256)."""
    user = _users.get_by_username(body.username)
    if user is None or not verify_password(body.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token({"sub": str(user["userId"]), "role": user["role"]})
    return LoginResponse(token=token, type="Bearer")


@router.post("/register", response_model=RegisterResponse, status_code=200)
def register(body: RegisterRequest):
    """Create a new user account."""
    try:
        if _users.username_exists(body.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        if _users.email_exists(body.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        hashed = hash_password(body.password)
        user_id = _users.create_user(body.username, hashed, body.email)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc}",
        )
    # Client-side redirect to login.html is handled by the caller (gateway / front-end)
    return RegisterResponse(userId=user_id)
