from pydantic import BaseModel
from typing import Literal

class UsuarioCreate(BaseModel):
    username: str
    password: str
    role: Literal["admin", "vendedor"]

class UsuarioResponse(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True