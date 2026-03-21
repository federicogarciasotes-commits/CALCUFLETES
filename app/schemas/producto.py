from pydantic import BaseModel, validator
from typing import List, Optional

class SubcategoriaBase(BaseModel):
    nombre: str
    largo: float
    ancho: float
    alto: float
    peso: float

class SubcategoriaCreate(SubcategoriaBase):
    pass

class SubcategoriaRead(SubcategoriaBase):
    id: int

    model_config = {
        "from_attributes": True
    }
        
class SubcategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    largo: Optional[float] = None
    ancho: Optional[float] = None
    alto: Optional[float] = None
    peso: Optional[float] = None


class ProductoBase(BaseModel):
    nombre: str
    subcategorias_ids: List[int]  # Obligatorio al menos una

    # Validación: al menos una subcategoría
    @validator("subcategorias_ids")
    def validar_subcategorias(cls, v):
        if not v:
            raise ValueError("El producto debe tener al menos una subcategoría")
        return v

class ProductoCreate(BaseModel):
    nombre: str
    subcategorias_ids: list[int]

class ProductoRead(BaseModel):
    id: int
    nombre: str
    subcategorias: list[SubcategoriaRead]

    model_config = {
        "from_attributes": True
    }

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    subcategorias_ids: Optional[List[int]] = None