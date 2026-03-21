from app.database import SessionLocal
from app.models.dias_reparto import DiaReparto

db = SessionLocal()

dias = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo"
]

for i, nombre in enumerate(dias, start=1):
    existe = db.query(DiaReparto).filter(DiaReparto.id == i).first()

    if not existe:
        db.add(DiaReparto(id=i, nombre=nombre))

db.commit()

print("Días cargados")