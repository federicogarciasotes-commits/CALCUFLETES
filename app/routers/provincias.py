from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.provincia import Provincia

router = APIRouter(prefix="/provincias", tags=["Provincias"])


@router.get("/")
def listar_provincias(db: Session = Depends(get_db)):
    provincias = db.query(Provincia).all()

    return [
        {
            "id": p.id,
            "nombre": p.nombre
        }
        for p in provincias
    ]