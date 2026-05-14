import unicodedata

import httpx

from .base import TransportistaCotizador
from .factory import registrar_proveedor
from .utils import calcular_medidas_bultos, calcular_medidas_por_bulto


BASE_URL = "https://ventasweb.intranetflash.com/tarifario"
COTIZADOR_URL = BASE_URL + "/nuevo2"

TIPO_GESTION_RETIRO_Y_ENTREGA = "2"
TIPO_PAQUETERIA_BULTOS = 1


class FlashLogisticaCotizador(TransportistaCotizador):

    nombre = "flashlogistica"

    def _normalizar(self, texto):
        texto = unicodedata.normalize("NFKD", texto or "")
        texto = texto.encode("ascii", "ignore").decode("ascii")
        return " ".join(texto.upper().replace(".", " ").replace(",", " ").split())

    def _to_float(self, value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        value = str(value).strip()
        if "," in value and "." in value:
            value = value.replace(".", "").replace(",", ".")
        elif "," in value:
            value = value.replace(",", ".")
        try:
            return float(value)
        except ValueError:
            return None

    def _headers(self):
        return {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://ventasweb.intranetflash.com",
            "Referer": COTIZADOR_URL,
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124 Safari/537.36"
            ),
            "X-Requested-With": "XMLHttpRequest",
        }

    async def _post_json(self, client, endpoint, payload):
        resp = await client.post(BASE_URL + "/" + endpoint, json=payload)
        resp.raise_for_status()
        return resp.json()

    def _buscar_provincia(self, provincias, nombre):
        objetivo = self._normalizar(nombre)
        for provincia in provincias:
            if self._normalizar(provincia.get("nombre")) == objetivo:
                return provincia
        return None

    def _buscar_localidad(self, localidades, nombre):
        objetivo = self._normalizar(nombre)
        for localidad in localidades:
            actual = self._normalizar(localidad.get("nombre"))
            if actual == objetivo:
                return localidad
        for localidad in localidades:
            actual = self._normalizar(localidad.get("nombre"))
            if objetivo in actual or actual in objetivo:
                return localidad
        return None

    def _armar_piezas(self, bultos, valor_declarado):
        piezas = []
        for medidas in calcular_medidas_por_bulto(bultos):
            piezas.append(
                {
                    "ancho": medidas["ancho_cm"],
                    "largo": medidas["largo_cm"],
                    "alto": medidas["alto_cm"],
                    "kilos": round(medidas["peso"], 3),
                    "volumen": medidas["volumen_cm3"],
                    "detalle": "Mercaderia",
                    "seguro": valor_declarado,
                }
            )
        return piezas

    async def cotizar(self, origen: dict, destino: dict, bultos: list, **extras):
        """
        Cotiza con el tarifario web de Flash Logistica.
        Requiere que origen/destino incluyan provincia y localidad.
        """
        if not origen.get("provincia") or not destino.get("provincia"):
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "Flash requiere provincia de origen y destino para cotizar.",
            }

        valor_declarado = extras.get("valor_declarado", 0)
        medidas = calcular_medidas_bultos(bultos)

        try:
            async with httpx.AsyncClient(
                timeout=25,
                follow_redirects=True,
                headers=self._headers(),
            ) as client:
                await client.get(COTIZADOR_URL)

                provincias_origen_data = await self._post_json(
                    client,
                    "ajaxGetProvinciasOrigen",
                    {"tipo_gestion_paqueteria": TIPO_GESTION_RETIRO_Y_ENTREGA},
                )
                provincias_origen = provincias_origen_data.get("resultado", [])
                provincia_origen = self._buscar_provincia(
                    provincias_origen,
                    origen["provincia"],
                )
                if not provincia_origen:
                    return {
                        "transportista": self.nombre,
                        "precio": None,
                        "error": f"Flash no tiene origen habilitado en provincia: {origen['provincia']}",
                        "detalle": {"provincias_origen": provincias_origen},
                    }

                localidades_origen_data = await self._post_json(
                    client,
                    "ajaxGetLocalidades",
                    {
                        "provincia_id": provincia_origen["id"],
                        "tipo": 1,
                        "tipo_gestion_paqueteria": TIPO_GESTION_RETIRO_Y_ENTREGA,
                    },
                )
                localidades_origen = localidades_origen_data.get("resultado", [])
                localidad_origen = self._buscar_localidad(
                    localidades_origen,
                    origen["localidad"],
                )
                if not localidad_origen:
                    return {
                        "transportista": self.nombre,
                        "precio": None,
                        "error": f"Flash no encontro localidad origen: {origen['localidad']}",
                        "detalle": {"localidades_origen": localidades_origen[:20]},
                    }

                provincias_destino_data = await self._post_json(
                    client,
                    "ajaxGetProvinciasDestino",
                    {
                        "provincia_id": provincia_origen["id"],
                        "tipo_gestion_paqueteria": TIPO_GESTION_RETIRO_Y_ENTREGA,
                    },
                )
                provincias_destino = provincias_destino_data.get("resultado", [])
                provincia_destino = self._buscar_provincia(
                    provincias_destino,
                    destino["provincia"],
                )
                if not provincia_destino:
                    return {
                        "transportista": self.nombre,
                        "precio": None,
                        "error": f"Flash no tiene destino habilitado en provincia: {destino['provincia']}",
                        "detalle": {"provincias_destino": provincias_destino},
                    }

                localidades_destino_data = await self._post_json(
                    client,
                    "ajaxGetLocalidades",
                    {
                        "provincia_id": provincia_destino["id"],
                        "tipo": 2,
                        "tipo_gestion_paqueteria": TIPO_GESTION_RETIRO_Y_ENTREGA,
                    },
                )
                localidades_destino = localidades_destino_data.get("resultado", [])
                localidad_destino = self._buscar_localidad(
                    localidades_destino,
                    destino["localidad"],
                )
                if not localidad_destino:
                    return {
                        "transportista": self.nombre,
                        "precio": None,
                        "error": f"Flash no encontro localidad destino: {destino['localidad']}",
                        "detalle": {"localidades_destino": localidades_destino[:20]},
                    }

                piezas = self._armar_piezas(bultos, valor_declarado)
                precio_data = await self._post_json(
                    client,
                    "ajaxGetPrecio",
                    {
                        "localidad_origen": localidad_origen["localidad_id"],
                        "localidad_destino": localidad_destino["localidad_id"],
                        "piezas": piezas,
                        "tipo_gestion_paqueteria": TIPO_GESTION_RETIRO_Y_ENTREGA,
                        "tipo_paqueteria_seleccionada": TIPO_PAQUETERIA_BULTOS,
                    },
                )

        except httpx.RequestError as e:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"Error de conexion: {str(e)}",
            }
        except Exception as e:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"Error procesando respuesta de Flash: {str(e)}",
            }

        if precio_data.get("error"):
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": precio_data.get("mensaje") or "Flash devolvio error al cotizar.",
                "detalle": precio_data,
            }

        precio = self._to_float(precio_data.get("total"))
        if precio is None:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"No se pudo parsear total de Flash: {str(precio_data)[:300]}",
                "detalle": precio_data,
            }

        return {
            "transportista": self.nombre,
            "precio": precio,
            "detalle": {
                "origen_flash": localidad_origen,
                "destino_flash": localidad_destino,
                "peso_total_kg": medidas["peso_total"],
                "volumen_cm3": medidas["volumen_cm3"],
                "cantidad_bultos": medidas["cantidad_bultos"],
                "subtotal_neto": self._to_float(precio_data.get("subTotalPrecioNeto")),
                "iva": self._to_float(precio_data.get("iva")),
                "costo_administrativo": precio_data.get("costoAdministrativo"),
                "respuesta": precio_data,
            },
        }


registrar_proveedor("flashlogistica", FlashLogisticaCotizador())
registrar_proveedor("flash", FlashLogisticaCotizador())
