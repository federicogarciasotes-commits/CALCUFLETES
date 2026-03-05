from sqlalchemy import Column, Integer, String
from app.database import Base
from sqlalchemy.orm import relationship

class Provincia(Base):
    __tablename__ = "provincias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True)

    localidades = relationship("Localidad", back_populates="provincia")