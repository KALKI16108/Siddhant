from pydantic import BaseModel
from typing import Optional

# Pydantic model for creating a new user (request body)
class UserCreate(BaseModel):
    username: str
    password: str

# Pydantic model for user authentication (request body for login)
class LoginRequest(BaseModel):
    username: str
    password: str

# Pydantic model for displaying basic user information (response body)
class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True  # Enable ORM mode to read data from SQLAlchemy models

# Pydantic model for JWT token response
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Pydantic model for data inside the JWT token
class TokenData(BaseModel):
    username: Optional[str] = None