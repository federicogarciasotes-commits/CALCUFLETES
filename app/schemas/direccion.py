from typing import Optional
from pydantic import BaseModel, ConfigDict



class DireccionInput(BaseModel):
    calle: str
    altura: int
    piso: str | None = None
    departamento: str | None = None
    localidad_id: int


class DireccionResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    calle: str
    altura: int

    piso: Optional[str] = None
    departamento: Optional[str] = None

    localidad_id: int
    provincia_id: int

    localidad: str
    provincia: str