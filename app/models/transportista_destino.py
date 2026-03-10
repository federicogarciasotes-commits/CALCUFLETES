from sqlalchemy import Column, Integer, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint

class TransportistaDestino(Base):
    __tablename__ = "transportista_destinos"

    id = Column(Integer, primary_key=True)

    transportista_id = Column(Integer, ForeignKey("transportistas.id"))
    localidad_id = Column(Integer, ForeignKey("localidades.id"))

    transportista = relationship("Transportista", back_populates="destinos")
    localidad = relationship("Localidad")

    __table_args__ = (
        UniqueConstraint("transportista_id", "localidad_id"),
    )