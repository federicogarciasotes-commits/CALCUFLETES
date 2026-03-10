from app.database import SessionLocal, engine, Base
from app.models.usuario import Usuario
from app.auth.security import pwd_context
from app.models.direccion import Direccion
from app.models.origen import Origen

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


default = db.query(Origen).filter(Origen.es_default).first()

if not default:

    direccion1 = Direccion(
        calle="Suecia",
        altura=2909,
        localidad_id=400,
        codigo_postal=5013
    )

    db.add(direccion1)
    db.commit()
    db.refresh(direccion1)

    origen1 = Origen(
        nombre="Droguería",
        direccion_id=direccion1.id,
        es_default=True
    )

    db.add(origen1)
    db.commit()
    
direccion2 = Direccion(
    calle="Av Malvinas",
    altura=4000,
    localidad_id=400,
    codigo_postal=5016,
    piso="PB",
    departamento="B"
)

db.add(direccion2)
db.commit()
db.refresh(direccion2)

origen2 = Origen(
    nombre="Depósito",
    direccion_id=direccion2.id,
    es_default=False
)

db.add(origen2)
db.commit()   

db.close()
