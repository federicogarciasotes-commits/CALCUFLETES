from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.origen import OrigenResponse, OrigenTitulo

from app.routers.auth import get_db
from app.models.origen import Origen
from app.models.usuario import Usuario
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/origenes", tags=["Origenes"])


@router.get("/titulos", response_model=list[OrigenTitulo])
def listar_titulos(db: Session = Depends(get_db)):
    origenes = db.query(Origen).all()
    return origenes
    
    
@router.get("/{origen_id}", response_model=OrigenResponse)
def obtener_origen(origen_id: int, db: Session = Depends(get_db)):
    origen = db.query(Origen).filter(Origen.id == origen_id).first()

    if not origen:
        raise HTTPException(status_code=404, detail="Origen no encontrado")

    return origen


@router.put("/origenes/{origen_id}/default")
def set_default(origen_id: int, db: Session = Depends(get_db)):

    db.query(Origen).update({Origen.es_default: False})

    origen = db.query(Origen).filter(Origen.id == origen_id).first()

    origen.es_default = True
    db.commit()

    return {"mensaje": "Origen actualizado"}