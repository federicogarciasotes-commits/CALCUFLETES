import httpx
import math

from .base import TransportistaCotizador
from .factory import registrar_proveedor
from .utils import (
    calcular_medidas_bultos,
    normalizar_texto,
    to_float,
)


BASE_URL = "https://ventasweb.intranetflash.com/tarifario"
COTIZADOR_URL = BASE_URL + "/nuevo2"

TIPO_GESTION_RETIRO_Y_ENTREGA = "2"
TIPO_PAQUETERIA_BULTOS = 1
TIPO_PAQUETERIA_PALETS = 2

MIN_DIMENSION_BULTO_CM = 5
MAX_VOLUMEN_BULTO_CM3 = 1_600_000
MAX_PESO_BULTO_KG = 200
MAX_PALETS = 10


class FlashLogisticaCotizador(TransportistaCotizador):

    nombre = "flashlogistica"

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
        objetivo = normalizar_texto(nombre)
        for provincia in provincias:
            if normalizar_texto(provincia.get("nombre")) == objetivo:
                return provincia
        return None

    def _buscar_localidad(self, localidades, nombre):
        objetivo = normalizar_texto(nombre)
        objetivo_tokens = objetivo.split()
        objetivo_sin_capital = " ".join(
            token
            for token in objetivo_tokens
            if token not in {"CAPITAL", "CIUDAD", "CENTRO"}
        )
        mejor = None

        for localidad in localidades:
            actual = normalizar_texto(localidad.get("nombre"))
            if actual == objetivo:
                return localidad

        for localidad in localidades:
            actual = normalizar_texto(localidad.get("nombre"))
            score = 0

            if actual.startswith(objetivo + " "):
                score += 120
            elif objetivo and objetivo in actual:
                score += 80
            elif actual and actual in objetivo:
                score += 60

            if objetivo_sin_capital and objetivo_sin_capital != objetivo:
                if actual == objetivo_sin_capital:
                    score += 130
                elif actual.startswith(objetivo_sin_capital + " "):
                    score += 100
                elif objetivo_sin_capital in actual:
                    score += 70

            if (
                objetivo
                and objetivo in {"CORDOBA", "MENDOZA", "SAN LUIS", "SAN JUAN"}
                and actual.startswith(objetivo + " CAPITAL")
            ):
                score += 160

            if "CAPITAL" in actual:
                score += 10

            if score > 0 and (mejor is None or score > mejor[0]):
                mejor = (score, localidad)

        return mejor[1] if mejor else None

    def _distribuir_valor_declarado(self, medidas_por_bulto, valor_declarado):
        if not valor_declarado:
            return [None] * len(medidas_por_bulto)

        total_peso = sum(max(medidas["peso"], 0) for medidas in medidas_por_bulto)
        if total_peso > 0:
            proporciones = [max(medidas["peso"], 0) / total_peso for medidas in medidas_por_bulto]
        else:
            proporcion = 1 / len(medidas_por_bulto)
            proporciones = [proporcion] * len(medidas_por_bulto)

        valores = []
        acumulado = 0.0
        for indice, proporcion in enumerate(proporciones):
            if indice == len(proporciones) - 1:
                valor = round(valor_declarado - acumulado, 2)
            else:
                valor = round(valor_declarado * proporcion, 2)
                acumulado += valor
            valores.append(valor if valor > 0 else None)
        return valores

    def _bulto_es_compatible(self, medidas):
        dimensiones = (medidas["ancho_cm"], medidas["largo_cm"], medidas["alto_cm"])
        return (
            all(dimension >= MIN_DIMENSION_BULTO_CM for dimension in dimensiones)
            and medidas["volumen_cm3"] < MAX_VOLUMEN_BULTO_CM3
            and medidas["peso"] <= MAX_PESO_BULTO_KG
        )

    def _medidas_promedio_por_palet(self, medidas_totales, cantidad_palets):
        volumen_por_palet = medidas_totales["volumen_cm3"] / cantidad_palets
        peso_por_palet = medidas_totales["peso_total"] / cantidad_palets
        lado_cm = max(MIN_DIMENSION_BULTO_CM, round(volumen_por_palet ** (1 / 3)))

        return {
            "alto_cm": lado_cm,
            "ancho_cm": lado_cm,
            "largo_cm": lado_cm,
            "peso": round(peso_por_palet, 3),
        }

    def _cantidad_palets_estimada(self, medidas_totales):
        return max(
            1,
            math.ceil(medidas_totales["volumen_cm3"] / MAX_VOLUMEN_BULTO_CM3),
            math.ceil(medidas_totales["peso_total"] / MAX_PESO_BULTO_KG),
        )

    def _tipos_paqueteria_disponibles(self, medidas_totales):
        tipos = []
        medidas_por_bulto = medidas_totales["por_bulto"]
        if medidas_por_bulto and all(self._bulto_es_compatible(medidas) for medidas in medidas_por_bulto):
            tipos.append((TIPO_PAQUETERIA_BULTOS, None))

        cantidad_palets = self._cantidad_palets_estimada(medidas_totales)
        if cantidad_palets <= MAX_PALETS:
            tipos.append((TIPO_PAQUETERIA_PALETS, cantidad_palets))

        return tipos, cantidad_palets

    def _armar_piezas_bultos(self, medidas_por_bulto, valor_declarado):
        valores_declarados = self._distribuir_valor_declarado(medidas_por_bulto, valor_declarado)
        piezas = []
        for medidas, valor_piece in zip(medidas_por_bulto, valores_declarados):
            piezas.append(
                {
                    # El cotizador web de Flash arma estas claves con este mismo orden.
                    "alto": medidas["ancho_cm"],
                    "largo": medidas["largo_cm"],
                    "ancho": medidas["alto_cm"],
                    "peso": round(medidas["peso"], 3),
                    "palets": None,
                    "descripcion": "Mercaderia general",
                    "valor_declarado": valor_piece,
                }
            )
        return piezas

    def _armar_piezas_palets(self, medidas_totales, valor_declarado, cantidad_palets):
        medidas = self._medidas_promedio_por_palet(medidas_totales, cantidad_palets)
        return [
            {
                "alto": medidas["ancho_cm"],
                "largo": medidas["largo_cm"],
                "ancho": medidas["alto_cm"],
                "peso": medidas["peso"],
                "palets": cantidad_palets,
                "descripcion": "Mercaderia general",
                "valor_declarado": round(valor_declarado, 2) if valor_declarado else None,
            }
        ]

    async def _cotizar_tipo(
        self,
        client,
        localidad_origen_id,
        localidad_destino_id,
        tipo_paqueteria,
        piezas,
    ):
        return await self._post_json(
            client,
            "ajaxGetPrecio",
            {
                "localidad_origen": localidad_origen_id,
                "localidad_destino": localidad_destino_id,
                "piezas": piezas,
                "tipo_gestion_paqueteria": TIPO_GESTION_RETIRO_Y_ENTREGA,
                "tipo_paqueteria_seleccionada": tipo_paqueteria,
            },
        )

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
        tipos_disponibles, cantidad_palets_estimada = self._tipos_paqueteria_disponibles(medidas)

        if not tipos_disponibles:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": (
                    f"Flash requiere {cantidad_palets_estimada} pallets estimados y supera el maximo "
                    f"permitido de {MAX_PALETS}."
                ),
                "detalle": {
                    "peso_total_kg": medidas["peso_total"],
                    "volumen_cm3": medidas["volumen_cm3"],
                    "cantidad_bultos": medidas["cantidad_bultos"],
                },
            }

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

                cotizaciones = []
                for tipo_paqueteria, cantidad_palets in tipos_disponibles:
                    if tipo_paqueteria == TIPO_PAQUETERIA_BULTOS:
                        piezas = self._armar_piezas_bultos(medidas["por_bulto"], valor_declarado)
                    else:
                        piezas = self._armar_piezas_palets(
                            medidas,
                            valor_declarado,
                            cantidad_palets,
                        )

                    precio_data = await self._cotizar_tipo(
                        client,
                        localidad_origen["localidad_id"],
                        localidad_destino["localidad_id"],
                        tipo_paqueteria,
                        piezas,
                    )

                    if precio_data.get("error"):
                        cotizaciones.append(
                            {
                                "tipo_paqueteria": (
                                    "palets"
                                    if tipo_paqueteria == TIPO_PAQUETERIA_PALETS
                                    else "bultos"
                                ),
                                "cantidad_palets": cantidad_palets,
                                "piezas": piezas,
                                "error": precio_data.get("mensaje")
                                or "Flash devolvio error al cotizar.",
                                "respuesta": precio_data,
                            }
                        )
                        continue

                    precio = to_float(precio_data.get("total"))
                    if precio is None:
                        cotizaciones.append(
                            {
                                "tipo_paqueteria": (
                                    "palets"
                                    if tipo_paqueteria == TIPO_PAQUETERIA_PALETS
                                    else "bultos"
                                ),
                                "cantidad_palets": cantidad_palets,
                                "piezas": piezas,
                                "error": "No se pudo parsear total de Flash.",
                                "respuesta": precio_data,
                            }
                        )
                        continue

                    cotizaciones.append(
                        {
                            "tipo_paqueteria": (
                                "palets"
                                if tipo_paqueteria == TIPO_PAQUETERIA_PALETS
                                else "bultos"
                            ),
                            "cantidad_palets": cantidad_palets,
                            "piezas": piezas,
                            "precio": precio,
                            "subtotal_neto": to_float(precio_data.get("subTotalPrecioNeto")),
                            "iva": to_float(precio_data.get("iva")),
                            "costo_administrativo": precio_data.get("costoAdministrativo"),
                            "respuesta": precio_data,
                        }
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

        exitosas = [cotizacion for cotizacion in cotizaciones if cotizacion.get("precio") is not None]
        if not exitosas:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "Flash no devolvio una tarifa valida para ningun tipo de paqueteria probado.",
                "detalle": {
                    "origen_flash": localidad_origen,
                    "destino_flash": localidad_destino,
                    "cotizaciones_probadas": cotizaciones,
                },
            }

        mejor = min(exitosas, key=lambda cotizacion: cotizacion["precio"])

        return {
            "transportista": self.nombre,
            "precio": mejor["precio"],
            "detalle": {
                "origen_flash": localidad_origen,
                "destino_flash": localidad_destino,
                "tipo_paqueteria": mejor["tipo_paqueteria"],
                "cantidad_palets": mejor["cantidad_palets"],
                "piezas_enviadas": mejor["piezas"],
                "peso_total_kg": medidas["peso_total"],
                "volumen_cm3": medidas["volumen_cm3"],
                "cantidad_bultos": medidas["cantidad_bultos"],
                "subtotal_neto": mejor["subtotal_neto"],
                "iva": mejor["iva"],
                "costo_administrativo": mejor["costo_administrativo"],
                "cotizaciones_probadas": cotizaciones,
                "respuesta": mejor["respuesta"],
            },
        }


registrar_proveedor("flashlogistica", FlashLogisticaCotizador())
registrar_proveedor("flash", FlashLogisticaCotizador())
