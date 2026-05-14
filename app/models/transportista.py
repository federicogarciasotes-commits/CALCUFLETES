from sqlalchemy import Boolean, Column, Integer, String
from app.database import Base
from sqlalchemy.orm import relationship

class Transportista(Base):
    __tablename__ = "transportistas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    descripcion = Column(String)
    activo = Column(Boolean, nullable=False, default=True, server_default="1")

    destinos = relationship(
        "TransportistaDestino",
        back_populates="transportista",
        cascade="all, delete-orphan"
    )

    dias = relationship(
        "TransportistaDia",
        back_populates="transportista",
        cascade="all, delete-orphan"
    )
