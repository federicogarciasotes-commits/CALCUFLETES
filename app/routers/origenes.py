from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.direccion import DireccionInput
from app.schemas.origen import OrigenResponse, OrigenTitulo, OrigenCreate

from app.database import get_db
from app.models.direccion import Direccion
from app.models.usuario import Usuario
from app.auth.dependencies import get_current_user
from app.models.localidad import Localidad
from app.models.provincia import Provincia
from app.models.origen import Origen
from app.auth.dependencies import require_admin

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
    

@router.get("/", response_model=list[OrigenResponse])
def listar_origenes(db: Session = Depends(get_db)):
    origenes = db.query(Origen).all()
    return [
        {
            "id": o.id,
            "nombre": o.nombre,
            "es_default": o.es_default,
            "direccion": {
                "calle": o.direccion.calle,
                "altura": o.direccion.altura,
                "piso": o.direccion.piso,
                "departamento": o.direccion.departamento,
                "localidad_id": o.direccion.localidad.id,
                "provincia_id": o.direccion.localidad.provincia.id,
                "localidad": o.direccion.localidad.nombre,
                "provincia": o.direccion.localidad.provincia.nombre
            }
        }
        for o in origenes
    ] 

 
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


@router.post("/", response_model=OrigenResponse)
def crear_origen(data: OrigenCreate, db=Depends(get_db), admin=Depends(require_admin)):
    direccion = Direccion(**data.direccion.model_dump())
    db.add(direccion)
    db.flush()  # para obtener el id sin commitear
    if data.es_default:
        db.query(Origen).update({Origen.es_default: False})
    origen = Origen(nombre=data.nombre, es_default=data.es_default, direccion_id=direccion.id)
    db.add(origen)
    db.commit()
    db.refresh(origen)
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

@router.put("/{origen_id}", response_model=OrigenResponse)
def editar_origen(origen_id: int, data: OrigenCreate, db=Depends(get_db), admin=Depends(require_admin)):
    origen = db.query(Origen).filter(Origen.id == origen_id).first()
    if not origen:
        raise HTTPException(404, "Origen no encontrado")
    origen.nombre = data.nombre
    if data.es_default:
        db.query(Origen).update({Origen.es_default: False})
    origen.es_default = data.es_default
    # actualizar dirección
    dir = db.query(Direccion).filter(Direccion.id == origen.direccion_id).first()
    for campo, valor in data.direccion.model_dump().items():
        setattr(dir, campo, valor)
    db.commit()
    db.refresh(origen)
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

@router.delete("/{origen_id}")
def eliminar_origen(origen_id: int, db=Depends(get_db), admin=Depends(require_admin)):
    origen = db.query(Origen).filter(Origen.id == origen_id).first()
    if not origen:
        raise HTTPException(404, "Origen no encontrado")

    era_default = origen.es_default
    db.delete(origen)
    db.flush()

    if era_default:
        nuevo_default = db.query(Origen).filter(Origen.id != origen_id).first()
        if not nuevo_default:
            raise HTTPException(400, "No podés eliminar el único origen existente")
        nuevo_default.es_default = True

    db.commit()
    return {"mensaje": "Origen eliminado"}

