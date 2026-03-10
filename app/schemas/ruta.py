from pydantic import BaseModel
from app.schemas.direccion import DireccionInput

class RutaRequest(BaseModel):
    origen: DireccionInput
    destino: DireccionInput