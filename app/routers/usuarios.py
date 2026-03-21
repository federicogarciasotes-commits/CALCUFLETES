from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.auth.security import pwd_context
from app.auth.dependencies import require_admin
from app.routers.auth import get_db
from app.models.direccion import Direccion
from app.models.origen import Origen
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


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

    default_origen = db.query(Origen).filter(
        Origen.es_default == True
    ).first()

    if not default_origen:
        raise HTTPException(
            status_code=500,
            detail="No hay origen default configurado"
        )

    if usuario_data.role not in ["admin", "vendedor"]:
        raise HTTPException(
            status_code=400,
            detail="Rol inválido"
        )

    nuevo_usuario = Usuario(
    username=usuario_data.username,
    password_hash=hashed_password,
    role=usuario_data.role,
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
        "origen": origen.nombre
    }
    

# Listar todos los usuarios (solo admin)
@router.get("/listar", response_model=list[UsuarioResponse])
def listar_usuarios(db=Depends(get_db), admin=Depends(require_admin)):
    return db.query(Usuario).all()

# Editar usuario (solo admin)
@router.put("/{usuario_id}", response_model=UsuarioResponse)
def editar_usuario(usuario_id: int, datos: UsuarioUpdate, db=Depends(get_db), admin=Depends(require_admin)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if datos.username:
        usuario.username = datos.username
    if datos.password:
        usuario.password_hash = pwd_context.hash(datos.password)
    if datos.role:
        usuario.role = datos.role
    db.commit()
    db.refresh(usuario)
    return usuario

# Eliminar usuario (solo admin)
@router.delete("/{usuario_id}")
def eliminar_usuario(usuario_id: int, db=Depends(get_db), admin=Depends(require_admin)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(usuario)
    db.commit()
    return {"message": "Usuario eliminado"}