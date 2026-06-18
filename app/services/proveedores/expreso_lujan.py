import json
import re
import time
from html import unescape
from math import ceil

import httpx

from .base import TransportistaCotizador
from .factory import registrar_proveedor
from .utils import calcular_medidas_bultos, normalizar_texto, to_float


BASE_URL = "https://cotizaciones.expresolujan.com/tarifadorelc"
ENCOMIENDA_URL = BASE_URL + "/com.tarifadorelc.encomienda"

DESCRIPCION_GENERICA = "Mercaderia general"
TIPO_BULTO = "Cajas"
RESPONSABLE_PAGO = "Remitente"
TIPO_TARIFA_PUERTA_A_PUERTA = "PP"

MAX_PESO_TOTAL_KG = 2000
MAX_ANCHO_CM = 260
MAX_ALTO_CM = 250
MAX_LARGO_CM = 1400
MAX_VOLUMEN_BULTO_CM3 = MAX_ANCHO_CM * MAX_ALTO_CM * MAX_LARGO_CM
IVA = 0.21


class ExpresoLujanCotizador(TransportistaCotizador):

    nombre = "expresolujan"

    def _headers(self):
        return {
            "Accept": "*/*",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124 Safari/537.36"
            ),
        }

    def _ajax_headers(self, token, auth_token):
        headers = self._headers()
        headers.update(
            {
                "Content-Type": "application/json",
                "Origin": "https://cotizaciones.expresolujan.com",
                "Referer": ENCOMIENDA_URL,
                "gxajaxrequest": "1",
                "ajax_security_token": token,
                "x-gxauth-token": auth_token,
            }
        )
        return headers

    def _extraer_gxstate(self, html):
        match = re.search(r'name="GXState" value=\'(.*)\'/></div>', html, re.S)
        if not match:
            raise ValueError("No se encontro GXState en Expreso Lujan.")
        return json.loads(unescape(match.group(1)))

    def _desarmar_localidad(self, nombre):
        partes = [parte.strip() for parte in str(nombre or "").split(",", 1)]
        localidad = normalizar_texto(partes[0]) if partes else ""
        provincia = normalizar_texto(partes[1]) if len(partes) > 1 else ""
        return localidad, provincia

    def _score_localidad(self, buscada, candidata):
        if not buscada or not candidata:
            return 0
        if candidata == buscada:
            return 400
        if candidata.startswith(buscada):
            return 260
        if buscada.startswith(candidata):
            return 220
        if buscada in candidata:
            return 180

        palabras_buscada = set(buscada.split())
        palabras_candidata = set(candidata.split())
        comunes = palabras_buscada & palabras_candidata
        if comunes:
            return 120 + (len(comunes) * 20)
        return 0

    def _buscar_localidad(self, localidades, localidad, cp=None, provincia=None):
        objetivo_localidad = normalizar_texto(localidad)
        objetivo_provincia = normalizar_texto(provincia)
        cp_texto = str(cp).strip() if cp else None

        candidatos = []
        for item in localidades:
            localidad_item, provincia_item = self._desarmar_localidad(item.get("name", ""))
            score_localidad = self._score_localidad(
                objetivo_localidad,
                localidad_item,
            )
            if score_localidad <= 0:
                continue

            score = score_localidad

            if objetivo_provincia and provincia_item == objetivo_provincia:
                score += 250
            elif objetivo_provincia:
                score -= 200

            if (
                objetivo_localidad
                and objetivo_provincia
                and objetivo_localidad == objetivo_provincia
                and provincia_item == objetivo_provincia
                and (
                    "CAPITAL" in localidad_item
                    or "CIUDAD" in localidad_item
                )
                and localidad_item.startswith(objetivo_localidad)
            ):
                score += 180

            if cp_texto and str(item.get("cp", "")).strip() == cp_texto:
                score += 35

            candidatos.append((score, item))

        if not candidatos and cp_texto:
            for item in localidades:
                if str(item.get("cp", "")).strip() == cp_texto:
                    candidatos.append((20, item))

        if not candidatos:
            return None

        candidatos.sort(key=lambda x: x[0], reverse=True)
        return candidatos[0][1]

    def _optimizar_bultos(self, medidas_totales):
        peso_total = float(medidas_totales["peso_total"])
        volumen_total_cm3 = max(1, int(round(medidas_totales["volumen_cm3"])))
        cantidad_bultos = max(1, ceil(volumen_total_cm3 / MAX_VOLUMEN_BULTO_CM3))

        while True:
            volumen_promedio_cm3 = ceil(volumen_total_cm3 / cantidad_bultos)
            dimensiones = self._dimensiones_equilibradas(volumen_promedio_cm3)
            if dimensiones:
                break
            cantidad_bultos += 1

        return {
            "cantidad_bultos": cantidad_bultos,
            "peso_total_kg": peso_total,
            "volumen_total_cm3": volumen_total_cm3,
            "volumen_promedio_cm3": volumen_promedio_cm3,
            "ancho_cm": dimensiones["ancho_cm"],
            "alto_cm": dimensiones["alto_cm"],
            "largo_cm": dimensiones["largo_cm"],
        }

    def _dimensiones_equilibradas(self, volumen_cm3):
        lado_base = max(1, ceil(volumen_cm3 ** (1 / 3)))
        lado_base = min(lado_base, MAX_ANCHO_CM, MAX_ALTO_CM, MAX_LARGO_CM)

        candidatos = []
        for ancho_cm in range(lado_base, MAX_ANCHO_CM + 1):
            for alto_cm in range(lado_base, MAX_ALTO_CM + 1):
                largo_cm = ceil(volumen_cm3 / (ancho_cm * alto_cm))
                if largo_cm > MAX_LARGO_CM:
                    continue
                candidatos.append(
                    {
                        "ancho_cm": ancho_cm,
                        "alto_cm": alto_cm,
                        "largo_cm": max(1, largo_cm),
                    }
                )
            if candidatos:
                break

        if not candidatos:
            return None

        candidatos.sort(
            key=lambda d: (
                max(d["ancho_cm"], d["alto_cm"], d["largo_cm"])
                - min(d["ancho_cm"], d["alto_cm"], d["largo_cm"]),
                d["ancho_cm"] * d["alto_cm"] * d["largo_cm"],
            )
        )
        return candidatos[0]

    def _armar_encfinlist(
        self,
        base_encfinlist,
        origen_item,
        destino_item,
        bulto_optimizado,
        valor_declarado,
    ):
        encfinlist = json.loads(json.dumps(base_encfinlist))
        encfinlist.setdefault("SdtDatosTarifa", {})
        encfinlist.setdefault("SdtEnvio", {})
        encfinlist.setdefault("SdtEncomienda", {})

        encfinlist["SdtDatosTarifa"].update(
            {
                "DepositoOri": origen_item["id"],
                "LocalidadOri": origen_item["description"],
                "DepositoDes": destino_item["id"],
                "LocalidadDes": destino_item["description"],
                "Peso": int(ceil(bulto_optimizado["peso_total_kg"])),
                "Alto": int(bulto_optimizado["alto_cm"]),
                "Ancho": int(bulto_optimizado["ancho_cm"]),
                "Largo": int(bulto_optimizado["largo_cm"]),
                "ValorDeclarado": float(valor_declarado),
                "bultos": int(bulto_optimizado["cantidad_bultos"]),
                "Session": "",
                "Accion": 0,
            }
        )

        encfinlist["SdtEnvio"]["modalidad"] = "ZZ"

        encfinlist["SdtEncomienda"].update(
            {
                "localidadOrigen": origen_item["name"],
                "sucursalOrigen": "",
                "cpOrigen": str(origen_item["cp"]),
                "localidadDestino": destino_item["name"],
                "sucursalDestino": "",
                "cpDestino": str(destino_item["cp"]),
                "responsablePago": RESPONSABLE_PAGO,
                "descripcionBulto": DESCRIPCION_GENERICA,
                "tipoBulto": TIPO_BULTO,
                "superakg": 1,
                "superamed": 0,
                "ruta": "",
                "imagen": "",
            }
        )

        return encfinlist

    def _armar_payload(
        self,
        state,
        localidades,
        origen_item,
        destino_item,
        bulto_optimizado,
        valor_declarado,
    ):
        encfinlist = self._armar_encfinlist(
            state.get("vENCFINLIST", {}),
            origen_item,
            destino_item,
            bulto_optimizado,
            valor_declarado,
        )

        return {
            "MPage": False,
            "cmpCtx": "",
            "objClass": "encomienda",
            "pkgName": "com.tarifadorelc",
            "events": ["'COTIZAR'"],
            "grids": {},
            "parms": [
                localidades,
                int(ceil(bulto_optimizado["peso_total_kg"])),
                int(state.get("vPESOCUBIC", 0) or 0),
                state.get("vFLAG", ""),
                encfinlist,
                origen_item["id"],
                origen_item["description"],
                destino_item["id"],
                destino_item["description"],
                int(bulto_optimizado["cantidad_bultos"]),
                f"{float(valor_declarado):.2f}",
                int(bulto_optimizado["alto_cm"]),
                int(bulto_optimizado["ancho_cm"]),
                int(bulto_optimizado["largo_cm"]),
                DESCRIPCION_GENERICA,
                TIPO_BULTO,
                TIPO_BULTO,
                origen_item["name"],
                str(origen_item["cp"]),
                destino_item["name"],
                str(destino_item["cp"]),
                "",
                RESPONSABLE_PAGO,
                RESPONSABLE_PAGO,
            ],
            "hsh": [
                {
                    "fld": "vPESOCUBIC",
                    "hsh": state.get("gxhash_vPESOCUBIC", ""),
                },
                {
                    "fld": "vPESOMAX",
                    "hsh": state.get("gxhash_vPESOMAX", ""),
                },
                {
                    "fld": "vJSONSDTENCOMIENDAIN",
                    "hsh": state.get("gxhash_vJSONSDTENCOMIENDAIN", ""),
                },
            ],
        }

    def _payload_debug(self, origen_item, destino_item, bulto_optimizado, valor_declarado):
        return {
            "origen": {
                "nombre": origen_item["name"],
                "codigo": origen_item["id"],
                "descripcion": origen_item["description"],
                "cp": str(origen_item["cp"]),
            },
            "destino": {
                "nombre": destino_item["name"],
                "codigo": destino_item["id"],
                "descripcion": destino_item["description"],
                "cp": str(destino_item["cp"]),
            },
            "cantidad_bultos": int(bulto_optimizado["cantidad_bultos"]),
            "peso_total_kg": round(bulto_optimizado["peso_total_kg"], 3),
            "valor_declarado": float(valor_declarado),
            "ancho_cm": int(bulto_optimizado["ancho_cm"]),
            "alto_cm": int(bulto_optimizado["alto_cm"]),
            "largo_cm": int(bulto_optimizado["largo_cm"]),
            "descripcion": DESCRIPCION_GENERICA,
            "tipo_bulto": TIPO_BULTO,
            "responsable_pago": RESPONSABLE_PAGO,
        }

    async def _obtener_tarifas(
        self,
        client,
        state,
        payload,
    ):
        ajax_iv = str(state["GX_AJAX_IV"]).lower()
        url = ENCOMIENDA_URL + "?" + ajax_iv + ",gx-no-cache=" + str(int(time.time() * 1000))

        resp = await client.post(
            url,
            json=payload,
            headers=self._ajax_headers(
                state["AJAX_SECURITY_TOKEN"],
                state["GX_AUTH_ENCOMIENDA"],
            ),
        )
        resp.raise_for_status()
        data = resp.json()

        redireccion = (
            data.get("gxCommands", [{}])[0]
            .get("redirect", {})
            .get("url")
        )
        if not redireccion:
            raise ValueError("Expreso Lujan no devolvio redirect de cotizacion.")

        resp_mod = await client.get(BASE_URL + "/" + redireccion, headers=self._headers())
        resp_mod.raise_for_status()
        state_mod = self._extraer_gxstate(resp_mod.text)
        tarifas = (
            state_mod.get("vSDTOUTCOTIZACION")
            or state_mod.get("Sdtoutcotizacion")
            or {}
        )
        return tarifas.get("data", [])

    def _seleccionar_tarifa(self, tarifas):
        for tarifa in tarifas:
            if tarifa.get("TipoTarifa") == TIPO_TARIFA_PUERTA_A_PUERTA:
                return tarifa
        return None

    async def cotizar(self, origen: dict, destino: dict, bultos: list, **extras):
        valor_declarado = extras.get("valor_declarado", 55000)
        medidas_totales = calcular_medidas_bultos(bultos)

        if medidas_totales["peso_total"] > MAX_PESO_TOTAL_KG:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": (
                    f"Expreso Lujan permite hasta {MAX_PESO_TOTAL_KG} kg "
                    "por esta modalidad de cotizacion."
                ),
            }

        bulto_optimizado = self._optimizar_bultos(medidas_totales)

        try:
            async with httpx.AsyncClient(
                timeout=30,
                follow_redirects=True,
                headers=self._headers(),
            ) as client:
                resp = await client.get(ENCOMIENDA_URL)
                resp.raise_for_status()
                state = self._extraer_gxstate(resp.text)
                localidades = state.get("vUCSUGGESTDATA", [])

                origen_item = self._buscar_localidad(
                    localidades,
                    origen.get("localidad", ""),
                    origen.get("cp"),
                    origen.get("provincia"),
                )
                if not origen_item:
                    return {
                        "transportista": self.nombre,
                        "precio": None,
                        "error": f"Expreso Lujan no encontro origen: {origen.get('localidad')}",
                    }

                destino_item = self._buscar_localidad(
                    localidades,
                    destino.get("localidad", ""),
                    destino.get("cp"),
                    destino.get("provincia"),
                )
                if not destino_item:
                    return {
                        "transportista": self.nombre,
                        "precio": None,
                        "error": f"Expreso Lujan no encontro destino: {destino.get('localidad')}",
                    }

                payload = self._armar_payload(
                    state,
                    localidades,
                    origen_item,
                    destino_item,
                    bulto_optimizado,
                    valor_declarado,
                )
                tarifas = await self._obtener_tarifas(client, state, payload)
                payload_debug = self._payload_debug(
                    origen_item,
                    destino_item,
                    bulto_optimizado,
                    valor_declarado,
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
                "error": f"Error procesando respuesta de Expreso Lujan: {str(e)}",
            }

        if not tarifas:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "Expreso Lujan no devolvio tarifas para ese envio.",
                "detalle": {
                    "payload_tarifador": payload_debug,
                },
            }

        tarifa = self._seleccionar_tarifa(tarifas)
        if not tarifa:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "Expreso Lujan no devolvio tarifa puerta a puerta para ese envio.",
                "detalle": {
                    "tarifas": tarifas,
                    "payload_tarifador": payload_debug,
                },
            }

        precio = to_float(tarifa.get("Importe"))
        if precio is None:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "No se pudo interpretar el precio de Expreso Lujan.",
                "detalle": {
                    "tarifa": tarifa,
                    "payload_tarifador": payload_debug,
                },
            }

        precio_con_iva = round(precio * (1 + IVA), 2)

        return {
            "transportista": self.nombre,
            "precio": precio_con_iva,
            "detalle": {
                "tipo_tarifa": tarifa.get("TipoTarifa"),
                "precio_sin_iva": precio,
                "precio_con_iva": precio_con_iva,
                "iva": round(precio_con_iva - precio, 2),
                "peso_total_kg": medidas_totales["peso_total"],
                "volumen_total_cm3": medidas_totales["volumen_cm3"],
                "cantidad_bultos_original": medidas_totales["cantidad_bultos"],
                "cantidad_bultos_cotizada": bulto_optimizado["cantidad_bultos"],
                "volumen_promedio_cm3": bulto_optimizado["volumen_promedio_cm3"],
                "medidas_bulto_cotizado": {
                    "ancho_cm": bulto_optimizado["ancho_cm"],
                    "alto_cm": bulto_optimizado["alto_cm"],
                    "largo_cm": bulto_optimizado["largo_cm"],
                },
                "preciotroncal": to_float(tarifa.get("preciotroncal")),
                "precioretiro": to_float(tarifa.get("precioretiro")),
                "precioentrega": to_float(tarifa.get("precioentrega")),
                "kilostarifados": to_float(tarifa.get("kilostarifados")),
                "direcciones": tarifa.get("direcciones", []),
                "origen_lujan": origen_item,
                "destino_lujan": destino_item,
                "payload_tarifador": payload_debug,
                "tarifas": tarifas,
            },
        }


registrar_proveedor("expresolujan", ExpresoLujanCotizador())
registrar_proveedor("expreso lujan", ExpresoLujanCotizador())
