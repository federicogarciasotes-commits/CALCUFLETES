import os
import httpx

from .base import TransportistaCotizador
from .factory import registrar_proveedor


class AndreaniCotizador(TransportistaCotizador):

    URL_QA = "https://apisqa.andreani.com/v1/tarifas"
    URL_PROD = "https://apis.andreani.com/v1/tarifas"

    nombre = "andreani"

    def __init__(self):

        entorno = os.getenv("ANDREANI_ENV", "qa")

        if entorno == "prod":
            self.base_url = self.URL_PROD
        else:
            self.base_url = self.URL_QA

        self.contrato = os.getenv("ANDREANI_CONTRATO", "TEST")
        self.cliente = os.getenv("ANDREANI_CLIENTE", "TEST")

    async def cotizar(self, origen, destino, bultos):

        params = {
            "cpOrigen": origen,
            "cpDestino": destino,
            "contrato": self.contrato,
            "cliente": self.cliente
        }

        for i, b in enumerate(bultos):

            # Andreani suele esperar volumen en cm3 o dm3
            volumen = (b.alto * b.ancho * b.largo) / 1000

            params[f"bultos[{i}][kilos]"] = b.peso
            params[f"bultos[{i}][volumen]"] = volumen

        try:

            async with httpx.AsyncClient(timeout=10) as client:

                response = await client.get(
                    self.base_url,
                    params=params
                )

        except httpx.RequestError as e:

            return {
                "transportista": self.nombre,
                "error": f"error de conexión: {str(e)}"
            }

        if response.status_code != 200:

            return {
                "transportista": self.nombre,
                "error": response.text
            }

        data = response.json()

        return {
            "transportista": self.nombre,
            "precio": float(data["tarifaConIva"]["total"]),
            "detalle": data
        }


# auto registro
registrar_proveedor("andreani", AndreaniCotizador())