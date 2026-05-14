from sqlalchemy.orm import Session
from app.models.transportista import Transportista
from app.models.transportista_destino import TransportistaDestino
from app.models.localidad import Localidad


class TransportistaRepository:

    def __init__(self, db):
        self.db = db

    def obtener_todos(self):

        return (
            self.db.query(Transportista)
            .filter(Transportista.activo.is_(True))
            .all()
        )

    def obtener_por_localidad(self, localidad_id):

        resultados = (
            self.db.query(Transportista)
            .join(TransportistaDestino)
            .filter(TransportistaDestino.localidad_id == localidad_id)
            .all()
        )

        return resultados


    def obtener_localidad(self, localidad_id):

        return (
            self.db.query(Localidad)
            .filter(Localidad.id == localidad_id)
            .first()
        )
