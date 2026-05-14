from .base import TransportistaCotizador
from .factory import registrar_proveedor
from .pendiente import respuesta_pendiente


class ExpresoLujanCotizador(TransportistaCotizador):

    nombre = "expresolujan"

    async def cotizar(self, origen: dict, destino: dict, bultos: list, **extras):
        return respuesta_pendiente(
            self.nombre,
            origen,
            destino,
            bultos,
            "Expreso Lujan pendiente de API o mecanismo tecnico de cotizacion.",
            "Consultar integracion tecnica a cotizaciones@expresolujan.com.",
        )


registrar_proveedor("expresolujan", ExpresoLujanCotizador())
