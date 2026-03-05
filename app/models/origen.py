from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class Origen(Base):
    __tablename__ = "origenes"

    id = Column(Integer, primary_key=True, index=True)

    titulo = Column(String, nullable=False)  # Droguería, Depósito, etc.

    provincia = Column(String, nullable=False)
    localidad = Column(String, nullable=False)
    calle = Column(String, nullable=False)
    numero = Column(String, nullable=False)
    codigo_postal = Column(Integer)

    piso = Column(String, nullable=True)
    departamento = Column(String, nullable=True)

    es_default = Column(Boolean, default=False)