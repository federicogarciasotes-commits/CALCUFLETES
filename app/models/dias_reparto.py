from sqlalchemy import Column, Integer, String
from app.database import Base

class DiaReparto(Base):
    __tablename__ = "dias_reparto"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)