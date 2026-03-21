from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.cotizacion import CotizacionRequest
from app.services.cotizador_service import CotizadorService

router = APIRouter(prefix="/cotizaciones", tags=["Cotizaciones"])


@router.post("/")
async def cotizar(data: CotizacionRequest, db: Session = Depends(get_db)):

    service = CotizadorService(db)

    return await service.cotizar_envio(data)