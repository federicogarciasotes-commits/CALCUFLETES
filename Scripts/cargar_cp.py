import csv
from unidecode import unidecode

from app.database import SessionLocal
from app.models.localidad import Localidad
from app.models.codigo_postal import CodigoPostal


def normalizar(txt):
    return unidecode(txt.lower().strip())


def cargar_cp():

    db = SessionLocal()

    localidades = db.query(Localidad).all()

    mapa = {}

    for loc in localidades:
        key = (
            normalizar(loc.nombre),
            normalizar(loc.provincia.nombre)
        )
        mapa[key] = loc

    cargados = 0

    with open("codigos_postales.csv", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        for row in reader:

            cp = row["cp"]
            localidad = normalizar(row["localidad"])
            provincia = normalizar(row["provincia"])

            key = (localidad, provincia)

            if key not in mapa:
                continue

            loc = mapa[key]

            existe = db.query(CodigoPostal).filter(
                CodigoPostal.codigo == cp,
                CodigoPostal.localidad_id == loc.id
            ).first()

            if existe:
                continue

            nuevo = CodigoPostal(
                codigo=cp,
                localidad_id=loc.id
            )

            db.add(nuevo)

            cargados += 1

    db.commit()

    print("CP cargados:", cargados)

    db.close()


if __name__ == "__main__":
    cargar_cp()