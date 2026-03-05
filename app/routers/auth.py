from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.usuario import Usuario
from app.auth.security import verify_password, create_access_token
from app.auth.dependencies import get_current_user, require_admin
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.usuario import UsuarioResponse

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(
        Usuario.username == form_data.username
    ).first()

    if not user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UsuarioResponse)
def obtener_mi_usuario(
    current_user: Usuario = Depends(get_current_user)
):
    return current_user

@router.get("/admin-only")
def admin_only(user: Usuario = Depends(require_admin)):
    return {"message": "Acceso permitido solo para admin"}