from sqlalchemy import Column, Integer, ForeignKey
from app.database import Base

class TransportistaDia(Base):
    __tablename__ = "transportista_dias"

    transportista_id = Column(Integer, ForeignKey("transportistas.id"), primary_key=True)
    dia_id = Column(Integer, ForeignKey("dias_reparto.id"), primary_key=True)