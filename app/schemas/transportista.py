from pydantic import BaseModel
from typing import List, Optional

class TransportistaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    destinos_ids: List[int] = []
    dias_ids: List[int] = []


class TransportistaResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    destinos_ids: list[int]
    dias_ids: list[int]

    class Config:
        from_attributes = True
        

class TransportistaListado(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    destinos: list[str]
    dias: list[str]

    class Config:
        from_attributes = True