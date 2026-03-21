from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.codigo_postal import CodigoPostal
from app.models.localidad import Localidad

router = APIRouter(prefix="/codigos_postales", tags=["Codigos Postales"])


@router.get("/buscar-por-cp/{cp}")
def buscar_por_cp(cp: str, db: Session = Depends(get_db)):

    codigo = db.query(CodigoPostal).filter(
        CodigoPostal.codigo == cp
    ).first()

    if not codigo:
        return {"error": "codigo postal no encontrado"}

    return {
    "codigo_postal": codigo.codigo,
    "localidad_id": codigo.localidad.id,
    "localidad": codigo.localidad.nombre,
    "provincia": codigo.localidad.provincia.nombre
}
    
@router.get("/por-localidad/{localidad_id}")
def obtener_cp_localidad(localidad_id: int, db: Session = Depends(get_db)):

    cps = db.query(CodigoPostal).filter(
        CodigoPostal.localidad_id == localidad_id
    ).all()

    return [cp.codigo for cp in cps]