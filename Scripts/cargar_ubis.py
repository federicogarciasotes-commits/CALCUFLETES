import requests

from app.database import SessionLocal
from app.models.provincia import Provincia
from app.models.localidad import Localidad
from app.models.codigo_postal import CodigoPostal

db = SessionLocal()

# API del gobierno
url_localidades = "https://apis.datos.gob.ar/georef/api/localidades?max=5000"

data = requests.get(url_localidades).json()

localidades = data["localidades"]

provincias_guardadas = {}

for loc in localidades:

    nombre_localidad = loc["nombre"]
    provincia_nombre = loc["provincia"]["nombre"]

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
    )

    db.add(nueva_localidad)

db.commit()

print("Ubicaciones cargadas correctamente")


'''
url_cp = "https://apis.datos.gob.ar/georef/api/codigos-postales?max=5000"

data = requests.get(url_cp).json()

print(data.keys())
print(data)

codigos = data["codigos-postales"]

for cp_data in codigos:

    cp = cp_data["codigo"]
    nombre_localidad = cp_data["localidad"]["nombre"]
    provincia_nombre = cp_data["provincia"]["nombre"]

    localidad = (
        db.query(Localidad)
        .join(Provincia)
        .filter(
            Localidad.nombre == nombre_localidad,
            Provincia.nombre == provincia_nombre
        )
        .first()
    )

    if localidad:

        nuevo_cp = CodigoPostal(
            codigo=cp,
            localidad_id=localidad.id
        )

        db.add(nuevo_cp)

db.commit()

print("Codigos postales cargados")
'''