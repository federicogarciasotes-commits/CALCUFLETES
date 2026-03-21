from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.transportista import Transportista
from app.models.transportista_destino import TransportistaDestino
from app.models.transportista_dia import TransportistaDia
from app.models.dias_reparto import DiaReparto

from app.schemas.transportista import (
    TransportistaCreate,
    TransportistaResponse,
    TransportistaListado
)
from app.models.usuario import Usuario
from app.auth.dependencies import get_current_user


def transportista_to_dict(t: Transportista):
    return {
        "id": t.id,
        "nombre": t.nombre,
        "descripcion": t.descripcion,
        "destinos": [d.localidad.nombre for d in t.destinos],
        "dias": [d.dia_reparto.nombre for d in t.dias]
    }


def verificar_admin(usuario: Usuario):
    if usuario.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tenés permisos para esta acción"
        )


router = APIRouter(
    prefix="/transportistas",
    tags=["Transportistas"]
)


@router.post("/", response_model=TransportistaResponse)
def crear_transportista(
    data: TransportistaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
    ):

    verificar_admin(current_user)

    transportista = Transportista(
        nombre=data.nombre,
        descripcion=data.descripcion
    )

    db.add(transportista)
    db.commit()
    db.refresh(transportista)

    for destino_id in data.destinos_ids:
        destino = TransportistaDestino(
            transportista_id=transportista.id,
            localidad_id=destino_id
        )
        db.add(destino)

    for dia_id in data.dias_ids:
        relacion = TransportistaDia(
            transportista_id=transportista.id,
            dia_id=dia_id
        )
        db.add(relacion)

    db.commit()

    return {
        "id": transportista.id,
        "nombre": transportista.nombre,
        "descripcion": transportista.descripcion,
        "destinos_ids": data.destinos_ids,
        "dias_ids": data.dias_ids
    }


@router.get("/dias/")
def listar_dias(db: Session = Depends(get_db)):
    return db.query(DiaReparto).all()


@router.get("/por-destino/{localidad_id}")
def transportistas_por_destino(localidad_id: int, db: Session = Depends(get_db)):

    resultados = (
        db.query(Transportista)
        .join(TransportistaDestino)
        .filter(TransportistaDestino.localidad_id == localidad_id)
        .all()
    )

    resultado = []

    for t in resultados:

        dias = [td.dia_reparto.nombre for td in t.dias]

        resultado.append({
            "id": t.id,
            "nombre": t.nombre,
            "descripcion": t.descripcion,
            "dias": dias
        })

    return resultado


@router.get("/listar", response_model=list[TransportistaResponse])
def listar_transportistas(db: Session = Depends(get_db)):

    transportistas = (
        db.query(Transportista)
        .options(
            joinedload(Transportista.destinos),
            joinedload(Transportista.dias)
        )
        .all()
    )

    resultado = []

    for t in transportistas:

        dest_ids = [d.localidad_id for d in t.destinos]
        dias_ids = [d.dia_id for d in t.dias]

        resultado.append({
            "id": t.id,
            "nombre": t.nombre,
            "descripcion": t.descripcion,
            "destinos_ids": dest_ids,
            "dias_ids": dias_ids
        })

    return resultado


@router.get("/listar/nombres", response_model=list[TransportistaListado])
def listar_transportistas_completo(db: Session = Depends(get_db)):

    transportistas = (
        db.query(Transportista)
        .options(
            joinedload(Transportista.destinos).joinedload(TransportistaDestino.localidad),
            joinedload(Transportista.dias).joinedload(TransportistaDia.dia_reparto)
        )
        .all()
    )

    return [transportista_to_dict(t) for t in transportistas]


@router.get("/{transportista_id}", response_model=TransportistaListado)
def obtener_transportista(transportista_id: int, db: Session = Depends(get_db)):

    transportista = (
        db.query(Transportista)
        .options(
            joinedload(Transportista.destinos).joinedload(TransportistaDestino.localidad),
            joinedload(Transportista.dias).joinedload(TransportistaDia.dia_reparto)
        )
        .filter(Transportista.id == transportista_id)
        .first()
    )

    if not transportista:
        raise HTTPException(
            status_code=404,
            detail="Transportista no encontrado"
        )

    return transportista_to_dict(transportista)


@router.put("/editar/{transportista_id}", response_model=TransportistaResponse)
def actualizar_transportista(
    transportista_id: int,
    data: TransportistaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)):

    verificar_admin(current_user)

    transportista = db.query(Transportista).filter(
        Transportista.id == transportista_id
    ).first()

    if not transportista:
        raise HTTPException(
            status_code=404,
            detail="Transportista no encontrado"
        )

    # actualizar datos básicos
    transportista.nombre = data.nombre
    transportista.descripcion = data.descripcion

    # borrar destinos actuales
    db.query(TransportistaDestino).filter(
        TransportistaDestino.transportista_id == transportista_id
    ).delete()

    # crear nuevos destinos
    for destino_id in data.destinos_ids:
        nuevo_destino = TransportistaDestino(
            transportista_id=transportista_id,
            localidad_id=destino_id
        )
        db.add(nuevo_destino)

    # borrar dias actuales
    db.query(TransportistaDia).filter(
        TransportistaDia.transportista_id == transportista_id
    ).delete()

    # crear nuevos dias
    for dia_id in data.dias_ids:
        nuevo_dia = TransportistaDia(
            transportista_id=transportista_id,
            dia_id=dia_id
        )
        db.add(nuevo_dia)

    db.commit()
    db.refresh(transportista)

    return {
        "id": transportista.id,
        "nombre": transportista.nombre,
        "descripcion": transportista.descripcion,
        "destinos_ids": data.destinos_ids,
        "dias_ids": data.dias_ids
    }
    

@router.delete("/{transportista_id}")
def eliminar_transportista(
    transportista_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):

    verificar_admin(current_user)

    transportista = db.query(Transportista).filter(
        Transportista.id == transportista_id
    ).first()

    if not transportista:
        raise HTTPException(
            status_code=404,
            detail="Transportista no encontrado"
        )

    db.delete(transportista)
    db.commit()

    return {"mensaje": "Transportista eliminado correctamente"}
