from pydantic import BaseModel,EmailStr


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    type: str = "Bearer"


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: EmailStr


class RegisterResponse(BaseModel):
    userId: int