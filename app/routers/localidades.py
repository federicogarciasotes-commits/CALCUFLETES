from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.localidad import Localidad
from app.models.codigo_postal import CodigoPostal

router = APIRouter(prefix="/localidades", tags=["Localidades"])


@router.get("/buscar")
def obtener_localidades(
    provincia_id: int | None = None,
    nombre: str | None = None,
    db: Session = Depends(get_db)
):

    query = db.query(Localidad)

    if provincia_id:
        query = query.filter(Localidad.provincia_id == provincia_id)

    if nombre:
        query = query.filter(Localidad.nombre.ilike(f"%{nombre}%"))

    return query.limit(1500).all()

@router.get("/{id}/cp-principal")
def cp_principal(id: int, db: Session = Depends(get_db)):

    localidad = db.query(Localidad).filter(
        Localidad.id == id
    ).first()

    if not localidad or not localidad.cp_principal:
        return {"error": "sin codigo postal"}

    return {"codigo_postal": localidad.cp_principal}
