from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.direccion import DireccionInput
from app.schemas.origen import OrigenResponse, OrigenTitulo

from app.routers.auth import get_db
from app.models.direccion import Direccion
from app.models.usuario import Usuario
from app.auth.dependencies import get_current_user
from app.models.localidad import Localidad
from app.models.provincia import Provincia
from app.models.origen import Origen

router = APIRouter(prefix="/origenes", tags=["Origenes"])


@router.get("/titulos", response_model=list[OrigenTitulo])
def listar_titulos(db: Session = Depends(get_db)):

    origenes = db.query(Origen).all()

    return origenes
    

@router.get("/default", response_model=OrigenResponse)
def obtener_origen_default(db: Session = Depends(get_db)):

    origen = db.query(Origen).filter(Origen.es_default == True).first()

    if not origen:
        raise HTTPException(status_code=404, detail="No hay origen default")

    direccion = origen.direccion

    return {
    "id": origen.id,
    "nombre": origen.nombre,
    "es_default": origen.es_default,
    "direccion": {
        "calle": origen.direccion.calle,
        "altura": origen.direccion.altura,
        "piso": origen.direccion.piso,
        "departamento": origen.direccion.departamento,

        "localidad_id": origen.direccion.localidad.id,
        "provincia_id": origen.direccion.localidad.provincia.id,

        "localidad": origen.direccion.localidad.nombre,
        "provincia": origen.direccion.localidad.provincia.nombre
    }
}
    
    
@router.get("/{origen_id}", response_model=OrigenResponse)
def obtener_origen(origen_id: int, db: Session = Depends(get_db)):

    origen = db.query(Origen).filter(Origen.id == origen_id).first()

    if not origen:
        raise HTTPException(status_code=404, detail="Origen no encontrado")

    direccion = origen.direccion

    return {
    "id": origen.id,
    "nombre": origen.nombre,
    "es_default": origen.es_default,
    "direccion": {
        "calle": origen.direccion.calle,
        "altura": origen.direccion.altura,
        "piso": origen.direccion.piso,
        "departamento": origen.direccion.departamento,

        "localidad_id": origen.direccion.localidad.id,
        "provincia_id": origen.direccion.localidad.provincia.id,

        "localidad": origen.direccion.localidad.nombre,
        "provincia": origen.direccion.localidad.provincia.nombre
    }
}



@router.put("/{origen_id}/default")
def set_default(origen_id: int, db: Session = Depends(get_db)):

    db.query(Origen).update({Origen.es_default: False})

    origen = db.query(Origen).filter(Origen.id == origen_id).first()

    if not origen:
        raise HTTPException(status_code=404, detail="Origen no encontrado")

    origen.es_default = True
    db.commit()

    return {"mensaje": "Origen actualizado"}
    

