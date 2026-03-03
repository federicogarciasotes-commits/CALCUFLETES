from sqlalchemy import Column, Integer, String
from app.database import Base

class Origen(Base):
    __tablename__ = "origenes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    codigo = Column(String, unique=True, nullable=False)