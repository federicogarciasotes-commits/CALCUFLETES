from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from app.database import Base
from sqlalchemy.orm import relationship


class Localidad(Base):
    __tablename__ = "localidades"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)

    provincia_id = Column(Integer, ForeignKey("provincias.id"))
    
    codigo_postal = Column(String, nullable=True)

    activo = Column(Boolean, default=True)

    provincia = relationship("Provincia", back_populates="localidades")