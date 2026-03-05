from sqlalchemy import Column, Integer, String
from app.database import Base
from sqlalchemy.orm import relationship

class Transportista(Base):
    __tablename__ = "transportistas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    descripcion = Column(String)

    destinos = relationship("TransportistaDestino", back_populates="transportista")