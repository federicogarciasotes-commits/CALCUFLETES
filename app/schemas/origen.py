from pydantic import BaseModel, ConfigDict
from typing import Optional


class OrigenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    provincia: str
    localidad: str
    calle: str
    numero: str
    codigo_postal: int
    piso: Optional[str] = None
    departamento: Optional[str] = None
    es_default: bool
    
    
class OrigenTitulo(BaseModel):
    id: int
    titulo: str

    model_config = ConfigDict(from_attributes=True)