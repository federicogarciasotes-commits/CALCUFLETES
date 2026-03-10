from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class Ruta(Base):
    __tablename__ = "rutas"

    id = Column(Integer, primary_key=True)

    origen_texto = Column(String)
    destino_texto = Column(String)

    distancia_metros = Column(Integer)
    duracion_segundos = Column(Integer)

    mapa_url = Column(String)