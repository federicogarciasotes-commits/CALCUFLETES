from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse
from app.auth.security import pwd_context
from app.auth.dependencies import require_admin
from app.routers.auth import get_db
from app.models.origen import Origen
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=UsuarioResponse)
def crear_usuario(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    existing_user = db.query(Usuario).filter(
        Usuario.username == usuario_data.username
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    hashed_password = pwd_context.hash(usuario_data.password)
    
    default_origen = db.query(Origen).filter(Origen.es_default == True).first()

    if not default_origen:
        raise HTTPException(status_code=500, detail="No hay origen default configurado")

    nuevo_usuario = Usuario(
        username=user_data.username,
        password=hash_password(user_data.password),
        origen_id=default_origen.id
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return nuevo_usuario
    

@router.put("/me/origen/{origen_id}")
def cambiar_mi_origen(
    origen_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1️ Verificar que el origen exista
    origen = db.query(Origen).filter(Origen.id == origen_id).first()

    if not origen:
        raise HTTPException(status_code=404, detail="Origen no encontrado")

    # 2️ Traer el usuario dentro de ESTA sesión
    user = db.query(Usuario).filter(Usuario.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 3️ Actualizar
    user.origen_id = origen.id

    db.commit()

    return {
        "message": "Origen actualizado correctamente",
        "origen": origen.titulo
    }