from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class TransportistaDia(Base):
    __tablename__ = "transportista_dias"

    transportista_id = Column(Integer, ForeignKey("transportistas.id"), primary_key=True)
    dia_id = Column(Integer, ForeignKey("dias_reparto.id"), primary_key=True)

    transportista = relationship("Transportista", back_populates="dias")
    dia_reparto = relationship("DiaReparto")