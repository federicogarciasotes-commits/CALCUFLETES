from .base import TransportistaCotizador
from .factory import registrar_proveedor
from .pendiente import respuesta_pendiente


class SendboxCotizador(TransportistaCotizador):

    nombre = "sendbox"

    async def cotizar(self, origen: dict, destino: dict, bultos: list, **extras):
        return respuesta_pendiente(
            self.nombre,
            origen,
            destino,
            bultos,
            "Sendbox pendiente de credenciales/API.",
            "Solicitar acceso API al equipo comercial de Sendbox.",
        )


registrar_proveedor("sendbox", SendboxCotizador())
