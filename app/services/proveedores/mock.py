from .base import TransportistaCotizador
from .factory import registrar_proveedor
from .utils import calcular_medidas_bultos


class MockCotizador(TransportistaCotizador):

    nombre = "mock"

    async def cotizar(self, origen: dict, destino: dict, bultos: list, **extras):
        medidas = calcular_medidas_bultos(bultos)
        precio = 3000 + (medidas["peso_total"] * 500)

        return {
            "transportista": self.nombre,
            "precio": precio,
            "detalle": {
                "origen": origen,
                "destino": destino,
                "peso_total": medidas["peso_total"],
                "volumen_cm3": medidas["volumen_cm3"],
            },
        }


registrar_proveedor("mock", MockCotizador())
