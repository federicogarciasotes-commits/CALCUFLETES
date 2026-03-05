from app.database import SessionLocal, engine, Base
from app.models.usuario import Usuario
from app.auth.security import pwd_context

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
    default = Origen(id= 1, 
                     titulo = "Droguería", 
                     provincia = "Cordoba",
                     localidad = "Cordoba",
                     calle = "Suecia",
                     numero = 2909,
                     codigo_postal = 5013,
                     es_default = True)
    db.add(default)
    db.commit()
    
d2 = Origen(id= 2, 
                     titulo = "Depósito", 
                     provincia = "Cordoba",
                     localidad = "Cordoba",
                     calle = "Av Malvinas",
                     numero = 4000,
                     codigo_postal = 5016,
                     piso = "PB",
                     departamento = "B",
                     es_default = False)
db.add(d2)
db.commit()   

db.close()