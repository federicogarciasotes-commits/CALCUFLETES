from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship

class Direccion(Base):
    __tablename__ = "direcciones"

    id = Column(Integer, primary_key=True)

    calle = Column(String)
    altura = Column(Integer)

    localidad_id = Column(Integer, ForeignKey("localidades.id"))
    localidad = relationship("Localidad")
    
    codigo_postal = Column(Integer)

    piso = Column(String, nullable=True)
    departamento = Column(String, nullable=True)
