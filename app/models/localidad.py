from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from app.database import Base
from sqlalchemy.orm import relationship


class Localidad(Base):
    __tablename__ = "localidades"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)

    provincia_id = Column(Integer, ForeignKey("provincias.id"))

    provincia = relationship("Provincia", back_populates="localidades")
    
    codigos_postales = relationship(
    "CodigoPostal",
    back_populates="localidad"
    )