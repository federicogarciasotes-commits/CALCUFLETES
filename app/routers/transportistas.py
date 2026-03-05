from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.transportista import Transportista
from app.models.transportista_destino import TransportistaDestino
from app.models.transportista_dia import TransportistaDia
from app.schemas.transportista import TransportistaCreate, TransportistaResponse


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

router = APIRouter(prefix="/transportistas", tags=["Transportistas"])

@router.post("/", response_model=TransportistaResponse)
def crear_transportista(data: TransportistaCreate, db: Session = Depends(get_db)):

    transportista = Transportista(
        nombre=data.nombre,
        descripcion=data.descripcion
    )

    db.add(transportista)
    db.commit()
    db.refresh(transportista)

    for destino_id in data.destinos_ids:
        relacion = TransportistaDestino(
            transportista_id=transportista.id,
            destino_id=destino_id
        )
        db.add(relacion)

    for dia_id in data.dias_ids:
        relacion = TransportistaDia(
            transportista_id=transportista.id,
            dia_id=dia_id
        )
        db.add(relacion)

    db.commit()

    return transportista
    

@router.get("/por-destino/{localidad_id}")
def transportistas_por_destino(localidad_id: int, db: Session = Depends(get_db)):

    transportistas = (
        db.query(Transportista)
        .join(TransportistaDestino)
        .filter(TransportistaDestino.localidad_id == localidad_id)
        .all()
    )

    return [
        {
            "id": t.id,
            "nombre": t.nombre,
            "descripcion": t.descripcion
        }
        for t in transportistas
    ]