from app.database import Base, engine
from app.models import Producto, Subcategoria

# Borra la tabla
Producto.__table__.drop(engine)
print("Tabla borrada")

Subcategoria.__table__.drop(engine)
print("Tabla borrada")