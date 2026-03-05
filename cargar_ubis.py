import requests

from app.database import SessionLocal
from app.models.provincia import Provincia
from app.models.localidad import Localidad

db = SessionLocal()

# API del gobierno
url = "https://apis.datos.gob.ar/georef/api/localidades?max=5000"

data = requests.get(url).json()

localidades = data["localidades"]

provincias_guardadas = {}

for loc in localidades:

    nombre_localidad = loc["nombre"]
    provincia_nombre = loc["provincia"]["nombre"]

    cp = None

    # crear provincia si no existe
    if provincia_nombre not in provincias_guardadas:

        provincia = db.query(Provincia).filter(
            Provincia.nombre == provincia_nombre
        ).first()

        if not provincia:

            provincia = Provincia(nombre=provincia_nombre)

            db.add(provincia)
            db.commit()
            db.refresh(provincia)

        provincias_guardadas[provincia_nombre] = provincia.id

    provincia_id = provincias_guardadas[provincia_nombre]

    nueva_localidad = Localidad(
        nombre=nombre_localidad,
        provincia_id=provincia_id,
        codigo_postal=cp
    )

    db.add(nueva_localidad)

db.commit()

print("Ubicaciones cargadas correctamente")