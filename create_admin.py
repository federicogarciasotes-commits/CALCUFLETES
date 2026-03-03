from app.database import SessionLocal, engine, Base
from app.models.usuario import Usuario
from app.auth.security import pwd_context

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Verificar si ya existe un admin
existing_admin = db.query(Usuario).filter(Usuario.role == "admin").first()

if existing_admin:
    print("Ya existe un usuario admin. No se creó uno nuevo.")
else:
    hashed_password = pwd_context.hash("admin123")

    admin = Usuario(
        username="admin",
        password_hash=hashed_password,
        role="admin"
    )

    db.add(admin)
    db.commit()
    print("Admin creado correctamente.")
    
from app.database import SessionLocal
from app.models.origen import Origen


default = db.query(Origen).filter(Origen.codigo == "DEFAULT").first()

if not default:
    default = Origen(nombre="Principal", codigo="DEFAULT")
    db.add(default)
    db.commit()

db.close()