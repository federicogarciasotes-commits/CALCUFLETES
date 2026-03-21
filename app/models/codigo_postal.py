from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class CodigoPostal(Base):
    __tablename__ = "codigos_postales"

    id = Column(Integer, primary_key=True)

    codigo = Column(String, nullable=False, index=True)

    localidad_id = Column(Integer, ForeignKey("localidades.id"))

    localidad = relationship("Localidad", back_populates="codigos_postales")