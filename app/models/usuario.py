from sqlalchemy import Column, Integer, String
from app.database import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)

    origen_id = Column(Integer, ForeignKey("origenes.id"))
    origen = relationship("Origen")