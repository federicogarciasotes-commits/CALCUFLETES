import random
from .base import TransportistaCotizador
from .factory import registrar_proveedor


class MockCotizador(TransportistaCotizador):

    nombre = "mock"

    async def cotizar(self, origen, destino, bultos):

        peso_total = sum(b.peso for b in bultos)

        precio = 3000 + (peso_total * 500)
        
        volumen_total = sum(b.volumen for b in bultos)

        return {
            "transportista": self.nombre,
            "precio": precio,
            "detalle": {
                "peso_total": peso_total,
                "volumen": volumen_total
            }
        }


registrar_proveedor("mock", MockCotizador())