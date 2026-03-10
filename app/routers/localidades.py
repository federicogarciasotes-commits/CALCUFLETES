from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.localidad import Localidad

router = APIRouter(prefix="/localidades", tags=["Localidades"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/buscar")
def buscar_localidades(
    nombre: str = Query(...),
    db: Session = Depends(get_db)
):

    localidades = (
        db.query(Localidad)
        .filter(Localidad.nombre.ilike(f"%{nombre}%"))
        .limit(20)
        .all()
    )

    return localidades
    return localidades


@router.get("/{provincia_id}")
def listar_localidades(provincia_id: int, db: Session = Depends(get_db)):
    localidades = (
        db.query(Localidad)
        .filter(Localidad.provincia_id == provincia_id)
        .all()
    )

    return [
        {
            "id": l.id,
            "nombre": l.nombre,
            # "codigo postal": l.codigo_postal
        }
        for l in localidades
    ]
    

