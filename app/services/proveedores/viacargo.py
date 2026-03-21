import httpx

from .base import TransportistaCotizador
from .factory import registrar_proveedor


API_URL = "https://ws.busplus.com.ar/alerce/cotizar"


class ViacargoCotizador(TransportistaCotizador):

    nombre = "viacargo"

    async def cotizar(self, origen_cp: str, destino_cp: str, bultos: list, **extras):
        """
        origen_cp / destino_cp: código postal como string (ej: "5000")
        bultos: lista de objetos Bulto con peso en kg y medidas en metros
        extras opcionales:
            valor_declarado: float (default 60000)
            tipo_portes:     "P" = pago origen (default), "D" = pago destino
        """

        peso_total      = sum(b.peso for b in bultos)
        alto_cm         = round(max(b.alto  for b in bultos) * 100)
        ancho_cm        = round(max(b.ancho for b in bultos) * 100)
        largo_cm        = round(max(b.largo for b in bultos) * 100)
        valor_declarado = extras.get("valor_declarado", 60000)
        tipo_portes     = extras.get("tipo_portes", "P")

        payload = {
            "IdClienteRemitente":      "99999999",
            "IdCentroRemitente":       "99",
            "CodigoPostalRemitente":   str(origen_cp),
            "CodigoPostalDestinatario": str(destino_cp),
            "NumeroBultos":            str(len(bultos)),
            "Kilos":                   str(round(peso_total, 2)),
            "Alto":                    str(alto_cm),
            "Ancho":                   str(ancho_cm),
            "Largo":                   str(largo_cm),
            "ImporteValorDeclarado":   str(int(valor_declarado)),
            "TipoPortes":              tipo_portes,
        }

        headers = {
            "Content-Type": "application/json",
            "Referer":      "https://formularios.viacargo.com.ar/",
            "Origin":       "https://formularios.viacargo.com.ar",
            "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        try:
            async with httpx.AsyncClient(timeout=15, headers=headers) as client:
                response = await client.post(API_URL, json=payload)

        except httpx.RequestError as e:
            return {"transportista": self.nombre, "precio": None,
                    "error": f"Error de conexión: {str(e)}"}

        if response.status_code != 200:
            return {"transportista": self.nombre, "precio": None,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"}

        try:
            data = response.json()
        except Exception:
            return {"transportista": self.nombre, "precio": None,
                    "error": "Respuesta no es JSON válido",
                    "raw": response.text[:300]}

        cotizaciones = data.get("Cotizacion", [])
        if not cotizaciones:
            return {"transportista": self.nombre, "precio": None,
                    "error": "No se recibieron cotizaciones"}

        # Filtrar solo los productos permitidos y ordenar por precio
        permitidos = [
            c for c in cotizaciones
            if c.get("PRODUCTO_PERMITIDO") == "S"
        ]
        if not permitidos:
            return {"transportista": self.nombre, "precio": None,
                    "error": "Ningún producto disponible para este envío"}

        permitidos.sort(key=lambda x: float(x.get("TOTAL", 0)))
        mejor = permitidos[0]

        return {
            "transportista": self.nombre,
            "precio":        float(mejor["TOTAL"]),
            "detalle": {
                "producto":        mejor["PRODUCTO_DESCRIPCION"],
                "tiempo_entrega":  mejor["TIEMPO_ENTREGA"],
                "todas_opciones": [
                    {
                        "producto": c["PRODUCTO_DESCRIPCION"],
                        "precio":   float(c["TOTAL"]),
                        "tiempo_entrega": c["TIEMPO_ENTREGA"],
                    }
                    for c in permitidos
                ],
                "peso_total":      peso_total,
                "cantidad_bultos": len(bultos),
            }
        }


# auto registro
registrar_proveedor("viacargo", ViacargoCotizador())