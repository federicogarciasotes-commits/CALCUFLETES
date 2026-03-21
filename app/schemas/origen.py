from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.schemas.direccion import DireccionResponse
from app.schemas.direccion import DireccionInput


class OrigenTitulo(BaseModel):

    id: int
    nombre: str

    model_config = ConfigDict(from_attributes=True)


class OrigenResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    es_default: bool

    direccion: DireccionResponse


class OrigenCreate(BaseModel):
    nombre: str
    es_default: bool = False
    direccion: DireccionInput  # calle, altura, piso, departamento, localidad_id