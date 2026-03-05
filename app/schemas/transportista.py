from pydantic import BaseModel
from typing import List


class TransportistaCreate(BaseModel):
    nombre: str
    descripcion: str | None = None
    destinos_ids: List[int]
    dias_ids: List[int]


class TransportistaResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None

    class Config:
        from_attributes = True