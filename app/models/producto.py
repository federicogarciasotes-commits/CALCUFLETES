from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base

# Tabla intermedia producto-subcategoría
producto_subcategoria = Table(
    "producto_subcategoria",
    Base.metadata,
    Column("producto_id", Integer, ForeignKey("productos.id"), nullable=False),
    Column("subcategoria_id", Integer, ForeignKey("subcategorias.id"), nullable=False)
)

class Subcategoria(Base):
    __tablename__ = "subcategorias"

    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False, unique=True)
    largo = Column(Float, nullable=False)
    ancho = Column(Float, nullable=False)
    alto = Column(Float, nullable=False)
    peso = Column(Float, nullable=False)

    productos = relationship(
        "Producto",
        secondary=producto_subcategoria,
        back_populates="subcategorias"
    )

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False, unique=True)

    subcategorias = relationship(
        "Subcategoria",
        secondary=producto_subcategoria,
        back_populates="productos"
    )