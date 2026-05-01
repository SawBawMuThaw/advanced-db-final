from fastapi import APIRouter, HTTPException, status

from ..models.user import UserResponse
from ..repository.user_repo import UserRepository

router = APIRouter(tags=["users"])
_users = UserRepository()


@router.get("/user/{id}", response_model=UserResponse)
def get_user(id: int):
    """Return public profile for a user by ID."""
    user = _users.get_by_id(id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(**user)