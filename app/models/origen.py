from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Origen(Base):
    __tablename__ = "origenes"

    id = Column(Integer, primary_key=True)

    nombre = Column(String, nullable=False)

    direccion_id = Column(Integer, ForeignKey("direcciones.id"))

    es_default = Column(Boolean, default=False)

    direccion = relationship("Direccion")