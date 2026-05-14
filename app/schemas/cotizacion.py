from pydantic import BaseModel
from typing import Optional


class Bulto(BaseModel):
    peso: float
    alto: float
    ancho: float
    largo: float
    volumen: float


class CotizacionRequest(BaseModel):

    localidad_origen_id: int
    localidad_destino_id: int
    cantidad_bultos: int
    peso_total: float
    volumen_total: Optional[float] = None
