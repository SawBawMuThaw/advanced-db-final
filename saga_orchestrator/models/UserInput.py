from pydantic import BaseModel, Field

class UserInput(BaseModel):
    username : str = Field(min_length=3, max_length=50, description="Username of the user")
    email : str = Field(min_length=5, max_length=100, description="Email address of the user")
    password : str = Field(min_length=8, max_length=100, description="Password for the user")