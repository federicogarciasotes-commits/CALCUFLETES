import logging
import os
from math import ceil
from datetime import datetime, timedelta, timezone

import httpx

from .base import TransportistaCotizador
from .factory import registrar_proveedor
from .utils import calcular_medidas_bultos, normalizar_texto, to_float


logger = logging.getLogger(__name__)

TIPOS_ENVIO_URL = "https://cotizador-api.andreani.com/api/v1/TipoDeEnvio"
COTIZAR_URL = "https://cotizador-api.andreani.com/api/v1/Cotizar"
TIPOS_ENVIO_TTL = timedelta(hours=6)

DEFAULT_XAPIKEY = "TEST_XqPMiwXzTRKHH0mF3gmtPtQt3LNGIuqCTdgaUHINMdmlaFid0x9MzlYTKXPxluYQ"
ALLOWED_TIPOS = ("paqueteria", "bigger", "pallet")
TIPO_PRIORIDAD = {
    "paqueteria": 1,
    "bigger": 2,
    "pallet": 3,
}
MODO_PREFERIDO = "a domicilio"


class AndreaniCotizador(TransportistaCotizador):

    nombre = "andreani"

    def __init__(self):
        self._tipos_cache = None
        self._tipos_cache_at = None

    def _headers(self):
        return {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://pymes.andreani.com",
            "referer": "https://pymes.andreani.com/",
            "user-agent": os.environ.get(
                "ANDREANI_USER_AGENT",
                (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/136.0.0.0 Safari/537.36"
                ),
            ),
            "xapikey": os.environ.get("ANDREANI_XAPIKEY", DEFAULT_XAPIKEY).strip(),
        }

    def _tipo_key(self, tipo):
        if isinstance(tipo, str):
            return "".join(normalizar_texto(tipo, reemplazos=()).lower().split())
        return "".join(normalizar_texto(tipo.get("nombre"), reemplazos=()).lower().split())

    def _item_rank(self, item_name):
        item_name = self._tipo_key(item_name)
        if "chico" in item_name:
            return 1
        if "mediano" in item_name:
            return 2
        if "grande" in item_name:
            return 3
        if "arlog" in item_name:
            return 4
        if "europeo" in item_name:
            return 5
        if "personalizado" in item_name:
            return 99
        return 50

    def _is_personalizado(self, item):
        return "personalizado" in self._tipo_key(item.get("itemName"))

    def _validation_for(self, item, name):
        for caracteristica in item.get("caracteristicas") or []:
            if self._tipo_key(caracteristica.get("name")) == self._tipo_key(name):
                return caracteristica
        return None

    def _peso_valor_para_item(self, item, peso_kg):
        caracteristica = self._validation_for(item, "Peso")
        if not caracteristica:
            return None

        medida = self._tipo_key(caracteristica.get("measure"))
        if medida == "kg":
            valor = round(float(peso_kg), 2)
            if abs(valor - round(valor)) < 1e-9:
                return str(int(round(valor)))
            return str(valor)

        peso_gr = round(float(peso_kg) * 1000)
        return str(int(peso_gr))

    def _valor_numerico_peso(self, item, peso_kg):
        caracteristica = self._validation_for(item, "Peso")
        if not caracteristica:
            return None

        medida = self._tipo_key(caracteristica.get("measure"))
        if medida == "kg":
            return float(peso_kg)
        return float(peso_kg) * 1000

    def _limites_item(self, item):
        def limite(nombre):
            caracteristica = self._validation_for(item, nombre) or {}
            validation = caracteristica.get("validation") or {}
            return {
                "min": to_float(validation.get("min"), default=0),
                "max": to_float(validation.get("max"), default=0),
                "measure": caracteristica.get("measure"),
            }

        return {
            "alto": limite("Alto"),
            "ancho": limite("Ancho"),
            "largo": limite("Largo"),
            "peso": limite("Peso"),
        }

    def _volumen_max_item(self, item):
        limites = self._limites_item(item)
        return (
            limites["alto"]["max"]
            * limites["ancho"]["max"]
            * limites["largo"]["max"]
        )

    def _entra_en_rango(self, valor, validation):
        minimo = validation.get("min")
        maximo = validation.get("max")
        if minimo is not None and valor < minimo:
            return False
        if maximo is not None and valor > maximo:
            return False
        return True

    def _construir_bulto_payload(self, item, medidas):
        valor_declarado_default = to_float(
            os.environ.get("ANDREANI_VALOR_DECLARADO"),
            default=20000,
        )
        caracteristica_valor = self._validation_for(item, "Valor-Declarado")
        minimo_valor = to_float(
            (caracteristica_valor or {}).get("validation", {}).get("min"),
            default=0,
        )
        valor_declarado = max(valor_declarado_default, minimo_valor)

        return {
            "itemId": item["id"],
            "altoCm": str(int(medidas["alto_cm"])),
            "anchoCm": str(int(medidas["ancho_cm"])),
            "largoCm": str(int(medidas["largo_cm"])),
            "Peso": self._peso_valor_para_item(item, medidas["peso"]),
            "valorDeclarado": str(int(valor_declarado)),
        }

    def _seleccionar_item_mayor_capacidad(self, tipo):
        items = tipo.get("items") or []
        if not items:
            return None

        return max(
            items,
            key=lambda item: (
                self._volumen_max_item(item),
                1 if self._is_personalizado(item) else 0,
                -self._item_rank(item.get("itemName")),
            ),
        )

    def _reempacar_para_item(self, item, medidas_totales):
        limites = self._limites_item(item)
        volumen_total = to_float(medidas_totales["volumen_cm3"], default=0)
        peso_total = to_float(medidas_totales["peso_total"], default=0)
        volumen_max = self._volumen_max_item(item)

        if volumen_total <= 0 or peso_total <= 0 or volumen_max <= 0:
            return None

        cantidad_bultos = max(1, ceil(volumen_total / volumen_max))
        peso_promedio = peso_total / cantidad_bultos
        peso_promedio_normalizado = self._valor_numerico_peso(item, peso_promedio)
        if peso_promedio_normalizado is None:
            return None

        if not self._entra_en_rango(peso_promedio_normalizado, limites["peso"]):
            return None

        area_base = limites["ancho"]["max"] * limites["largo"]["max"]
        if area_base <= 0:
            return None

        volumen_restante = volumen_total
        bultos = []
        items_elegidos = []

        for indice in range(cantidad_bultos):
            volumen_bulto = min(volumen_restante, volumen_max)
            alto_cm = ceil(volumen_bulto / area_base)
            if alto_cm <= 0 or alto_cm > limites["alto"]["max"]:
                return None
            if alto_cm < limites["alto"]["min"]:
                alto_cm = int(limites["alto"]["min"])

            medidas_bulto = {
                "alto_cm": int(alto_cm),
                "ancho_cm": int(limites["ancho"]["max"]),
                "largo_cm": int(limites["largo"]["max"]),
                "peso": round(peso_promedio, 4),
                "volumen_cm3": int(alto_cm) * int(limites["ancho"]["max"]) * int(limites["largo"]["max"]),
            }

            bultos.append(self._construir_bulto_payload(item, medidas_bulto))
            items_elegidos.append(
                {
                    "item_id": item["id"],
                    "item_name": item.get("itemName"),
                    "volumen_objetivo_cm3": volumen_bulto,
                    "medidas": medidas_bulto,
                }
            )
            volumen_restante -= volumen_bulto

        return {
            "bultos": bultos,
            "items_elegidos": items_elegidos,
            "cantidad_bultos": cantidad_bultos,
            "volumen_max_item_cm3": volumen_max,
            "peso_promedio_kg": round(peso_promedio, 4),
        }

    def _candidatos_tipo(self, tipos, medidas_totales):
        candidatos = []

        tipos_permitidos = sorted(
            (
                tipo
                for tipo in tipos
                if self._tipo_key(tipo) in ALLOWED_TIPOS
            ),
            key=lambda tipo: TIPO_PRIORIDAD.get(self._tipo_key(tipo), 999),
        )

        for tipo in tipos_permitidos:
            item = self._seleccionar_item_mayor_capacidad(tipo)
            if not item:
                continue

            packing = self._reempacar_para_item(item, medidas_totales)
            if not packing:
                continue

            candidatos.append(
                {
                    "tipo": tipo,
                    "item": item,
                    "packing": packing,
                }
            )

        return candidatos

    def _mejor_opcion(self, opciones):
        if not opciones:
            return None

        def precio(opcion):
            return to_float(opcion.get("tarifaConIva"), default=float("inf"))

        domicilio = [
            opcion
            for opcion in opciones
            if self._tipo_key(opcion.get("modoDeEntrega"))
            == self._tipo_key(MODO_PREFERIDO)
        ]
        if domicilio:
            return min(domicilio, key=precio)
        return min(opciones, key=precio)

    def _mejor_resultado(self, resultados):
        if not resultados:
            return None

        return min(
            resultados,
            key=lambda resultado: (
                to_float(resultado["opcion"].get("tarifaConIva"), default=float("inf")),
                TIPO_PRIORIDAD.get(self._tipo_key(resultado["tipo"]), 999),
                resultado["packing"]["cantidad_bultos"],
            ),
        )

    async def _obtener_tipos_envio(self):
        ahora = datetime.now(timezone.utc)
        if (
            self._tipos_cache is not None
            and self._tipos_cache_at is not None
            and ahora - self._tipos_cache_at < TIPOS_ENVIO_TTL
        ):
            return self._tipos_cache

        async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
            resp = await client.get(TIPOS_ENVIO_URL, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()

        self._tipos_cache = data
        self._tipos_cache_at = ahora
        return data

    async def cotizar(self, origen: dict, destino: dict, bultos: list, **extras):
        medidas_totales = calcular_medidas_bultos(bultos)

        try:
            tipos = await self._obtener_tipos_envio()
        except httpx.RequestError as exc:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"Error de conexion consultando catalogo Andreani: {exc}",
            }
        except Exception as exc:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"Error obteniendo tipos de envio Andreani: {exc}",
            }

        candidatos = self._candidatos_tipo(tipos, medidas_totales)
        if not candidatos:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": (
                    "Andreani no encontro una categoria compatible para todos los "
                    "bultos del envio."
                ),
                "detalle": {
                    "tipos_considerados": list(ALLOWED_TIPOS),
                    "volumen_total_cm3": medidas_totales["volumen_cm3"],
                    "peso_total_kg": medidas_totales["peso_total"],
                    "bulto_mayor": medidas_totales["bulto_mayor"],
                },
            }

        resultados = []

        try:
            async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
                for candidato in candidatos:
                    payload = {
                        "usuarioId": None,
                        "tipoDeEnvioId": candidato["tipo"]["id"],
                        "codigoPostalOrigen": str(origen["cp"]),
                        "codigoPostalDestino": str(destino["cp"]),
                        "bultos": candidato["packing"]["bultos"],
                    }

                    resp = await client.post(
                        COTIZAR_URL,
                        headers=self._headers(),
                        json=payload,
                    )

                    if resp.status_code != 200:
                        logger.warning(
                            "Andreani categoria=%s devolvio http=%s body=%s",
                            candidato["tipo"].get("nombre"),
                            resp.status_code,
                            resp.text[:300],
                        )
                        continue

                    try:
                        data = resp.json()
                    except Exception:
                        logger.warning(
                            "Andreani categoria=%s devolvio respuesta no JSON",
                            candidato["tipo"].get("nombre"),
                        )
                        continue

                    if not isinstance(data, list) or not data:
                        logger.warning(
                            "Andreani categoria=%s sin opciones de cotizacion respuesta=%s",
                            candidato["tipo"].get("nombre"),
                            str(data)[:300],
                        )
                        continue

                    opcion = self._mejor_opcion(data)
                    precio = to_float(opcion.get("tarifaConIva"))
                    if precio is None:
                        continue

                    resultados.append(
                        {
                            "tipo": candidato["tipo"].get("nombre"),
                            "tipo_id": candidato["tipo"]["id"],
                            "item": candidato["item"],
                            "packing": candidato["packing"],
                            "payload": payload,
                            "opciones": data,
                            "opcion": opcion,
                        }
                    )
        except httpx.RequestError as exc:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"Error de conexion Andreani: {exc}",
                "detalle": {
                    "cp_origen": origen["cp"],
                    "cp_destino": destino["cp"],
                },
            }

        mejor = self._mejor_resultado(resultados)
        if not mejor:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "Andreani no devolvio tarifas validas para ninguna categoria compatible.",
                "detalle": {
                    "categorias_probadas": [candidato["tipo"].get("nombre") for candidato in candidatos],
                    "volumen_total_cm3": medidas_totales["volumen_cm3"],
                    "peso_total_kg": medidas_totales["peso_total"],
                },
            }

        precio = to_float(mejor["opcion"].get("tarifaConIva"))

        return {
            "transportista": self.nombre,
            "precio": round(precio, 2),
            "detalle": {
                "endpoint": COTIZAR_URL,
                "tipo_envio_id": mejor["tipo_id"],
                "tipo_envio": mejor["tipo"],
                "item_usado": {
                    "id": mejor["item"]["id"],
                    "item_name": mejor["item"].get("itemName"),
                    "volumen_max_item_cm3": mejor["packing"]["volumen_max_item_cm3"],
                },
                "cantidad_bultos_optimizada": mejor["packing"]["cantidad_bultos"],
                "peso_promedio_kg": mejor["packing"]["peso_promedio_kg"],
                "items_elegidos": mejor["packing"]["items_elegidos"],
                "modo_entrega": mejor["opcion"].get("modoDeEntrega"),
                "modo_entrega_id": mejor["opcion"].get("modoDeEntregaId"),
                "contrato_id": mejor["opcion"].get("contratoId"),
                "peso_aforado": to_float(mejor["opcion"].get("pesoAforado")),
                "tarifa_con_iva": to_float(mejor["opcion"].get("tarifaConIva")),
                "tarifa_sin_iva": to_float(mejor["opcion"].get("tarifaSinIva")),
                "respuesta_opciones": mejor["opciones"],
                "payload": mejor["payload"],
                "categorias_probadas": [
                    {
                        "tipo_envio": resultado["tipo"],
                        "tipo_envio_id": resultado["tipo_id"],
                        "precio": to_float(resultado["opcion"].get("tarifaConIva")),
                        "cantidad_bultos": resultado["packing"]["cantidad_bultos"],
                    }
                    for resultado in resultados
                ],
                "medidas_totales": medidas_totales,
            },
        }


registrar_proveedor("andreani", AndreaniCotizador())
