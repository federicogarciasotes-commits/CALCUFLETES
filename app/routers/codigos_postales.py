from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.localidad import Localidad

router = APIRouter(prefix="/codigos_postales", tags=["Codigos Postales"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/buscar-por-cp/{cp}")
def buscar_por_cp(cp: str, db: Session = Depends(get_db)):

    codigo = db.query(CodigoPostal).filter(
        CodigoPostal.codigo == cp
    ).first()

    if not codigo:
        return {"error": "codigo postal no encontrado"}

    return {
        "codigo_postal": codigo.codigo,
        "localidad": codigo.localidad.nombre,
        "provincia": codigo.localidad.provincia.nombre
    }