from pydantic import BaseModel, Field

class User(BaseModel):
    userId : int
    username : str