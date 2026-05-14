import httpx

from .base import TransportistaCotizador
from .factory import registrar_proveedor
from .utils import calcular_medidas_bultos
import math


API_URL = "https://ws.busplus.com.ar/alerce/cotizar"


class ViacargoCotizador(TransportistaCotizador):

    nombre = "viacargo"

    def _bulto_promedio(self, medidas):
        cantidad_bultos = medidas["cantidad_bultos"] or 1
        volumen_promedio_cm3 = medidas["volumen_cm3"] / cantidad_bultos
        peso_promedio = medidas["peso_total"] / cantidad_bultos
        alto_cm = math.trunc(volumen_promedio_cm3 / 10_000)

        return {
            "peso": round(peso_promedio, 2),
            "ancho_cm": 100,
            "largo_cm": 100,
            "alto_cm": alto_cm,
            "volumen_cm3": volumen_promedio_cm3,
        }

    async def cotizar(self, origen: dict, destino: dict, bultos: list, **extras):
        """
        origen / destino: dicts con codigo postal y localidad.
        bultos: lista de objetos Bulto con peso en kg y medidas en metros.
        extras opcionales:
            valor_declarado: float (default 60000)
            tipo_portes:     "P" = pago origen (default), "D" = pago destino
        """
        medidas = calcular_medidas_bultos(bultos)
        bulto_promedio = self._bulto_promedio(medidas)
        valor_declarado = extras.get("valor_declarado", 60000)
        tipo_portes = extras.get("tipo_portes", "P")

        payload = {
            "IdClienteRemitente": "99999999",
            "IdCentroRemitente": "99",
            "CodigoPostalRemitente": str(origen["cp"]),
            "CodigoPostalDestinatario": str(destino["cp"]),
            "NumeroBultos": str(medidas["cantidad_bultos"]),
            "Kilos": str(bulto_promedio["peso"]),
            "Alto": str(bulto_promedio["alto_cm"]),
            "Ancho": str(bulto_promedio["ancho_cm"]),
            "Largo": str(bulto_promedio["largo_cm"]),
            "ImporteValorDeclarado": str(int(valor_declarado)),
            "TipoPortes": tipo_portes,
        }

        headers = {
            "Content-Type": "application/json",
            "Referer": "https://formularios.viacargo.com.ar/",
            "Origin": "https://formularios.viacargo.com.ar",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        try:
            async with httpx.AsyncClient(timeout=15, headers=headers) as client:
                response = await client.post(API_URL, json=payload)

        except httpx.RequestError as e:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"Error de conexion: {str(e)}",
            }

        if response.status_code != 200:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
            }

        try:
            data = response.json()
        except Exception:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "Respuesta no es JSON valido",
                "raw": response.text[:300],
            }

        cotizaciones = data.get("Cotizacion", [])
        if not cotizaciones:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "No se recibieron cotizaciones",
            }

        permitidos = [
            c for c in cotizaciones
            if c.get("PRODUCTO_PERMITIDO") == "S"
        ]
        if not permitidos:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "Ningun producto disponible para este envio",
            }

        permitidos.sort(key=lambda x: float(x.get("TOTAL", 0)))
        mejor = permitidos[0]

        return {
            "transportista": self.nombre,
            "precio": float(mejor["TOTAL"]),
            "detalle": {
                "producto": mejor["PRODUCTO_DESCRIPCION"],
                "tiempo_entrega": mejor["TIEMPO_ENTREGA"],
                "todas_opciones": [
                    {
                        "producto": c["PRODUCTO_DESCRIPCION"],
                        "precio": float(c["TOTAL"]),
                        "tiempo_entrega": c["TIEMPO_ENTREGA"],
                    }
                    for c in permitidos
                ],
                "peso_total": medidas["peso_total"],
                "cantidad_bultos": medidas["cantidad_bultos"],
                "bulto_promedio": bulto_promedio,
                "bulto_mayor": medidas["bulto_mayor"],
                "volumen_total_cm3": medidas["volumen_cm3"],
            },
        }


registrar_proveedor("viacargo", ViacargoCotizador())
