import os

import httpx

from .base import TransportistaCotizador
from .factory import registrar_proveedor
from .utils import calcular_medidas_bultos, calcular_medidas_por_bulto


# API de tarifas documentada en api-cotizador-v2-1.xlsx:
#   QA:   https://apisqa.andreani.com/v1/tarifas
#   PROD: https://apis.andreani.com/v1/tarifas
#
# Variables esperadas en .env:
#   ANDREANI_AMBIENTE=qa | prod
#   ANDREANI_CLIENTE=<codigo cliente otorgado por Andreani>
#   ANDREANI_CONTRATO=<codigo contrato otorgado por Andreani>
#   ANDREANI_SUCURSAL_ORIGEN=<opcional>
#   ANDREANI_VALOR_DECLARADO=60000
#
# Si Andreani confirma autenticacion por header:
#   ANDREANI_API_KEY=<token o key>
#   ANDREANI_AUTH_HEADER=x-api-key | Authorization | ...
#   ANDREANI_AUTH_SCHEME=Bearer  # opcional, solo para Authorization: Bearer <token>

QA_TARIFAS_URL = "https://apisqa.andreani.com/v1/tarifas"
PROD_TARIFAS_URL = "https://apis.andreani.com/v1/tarifas"


class AndreaniCotizador(TransportistaCotizador):

    nombre = "andreani"

    def _config(self, extras):
        ambiente = extras.get("ambiente") or os.environ.get("ANDREANI_AMBIENTE", "qa")
        ambiente = ambiente.strip().lower()

        base_url = extras.get("base_url") or os.environ.get("ANDREANI_BASE_URL", "")
        if base_url:
            tarifas_url = base_url.rstrip("/") + "/v1/tarifas"
        elif ambiente == "prod":
            tarifas_url = PROD_TARIFAS_URL
        else:
            tarifas_url = QA_TARIFAS_URL

        cliente = extras.get("cliente") or os.environ.get("ANDREANI_CLIENTE", "")
        contrato = extras.get("contrato") or os.environ.get("ANDREANI_CONTRATO", "")
        sucursal_origen = (
            extras.get("sucursal_origen")
            or os.environ.get("ANDREANI_SUCURSAL_ORIGEN", "")
        )
        valor_declarado = (
            extras.get("valor_declarado")
            or os.environ.get("ANDREANI_VALOR_DECLARADO")
            or 60000
        )

        return {
            "ambiente": ambiente,
            "tarifas_url": tarifas_url,
            "cliente": str(cliente).strip(),
            "contrato": str(contrato).strip(),
            "sucursal_origen": str(sucursal_origen).strip(),
            "valor_declarado": valor_declarado,
        }

    def _headers(self):
        headers = {
            "Accept": "application/json",
            "User-Agent": "CALCUFLETES/1.0",
        }

        api_key = os.environ.get("ANDREANI_API_KEY", "").strip()
        if not api_key:
            return headers

        header_name = os.environ.get("ANDREANI_AUTH_HEADER", "x-api-key").strip()
        auth_scheme = os.environ.get("ANDREANI_AUTH_SCHEME", "").strip()
        headers[header_name] = f"{auth_scheme} {api_key}".strip()
        return headers

    def _params(self, config, destino, bultos):
        params = [
            ("cpDestino", str(destino["cp"])),
            ("contrato", config["contrato"]),
            ("cliente", config["cliente"]),
        ]

        if config["sucursal_origen"]:
            params.append(("sucursalOrigen", config["sucursal_origen"]))

        for index, medidas in enumerate(calcular_medidas_por_bulto(bultos)):
            params.extend(
                [
                    (f"bultos[{index}][valorDeclarado]", str(int(float(config["valor_declarado"])))),
                    (f"bultos[{index}][volumen]", str(medidas["volumen_cm3"])),
                    (f"bultos[{index}][kilos]", str(round(medidas["peso"], 2))),
                    (f"bultos[{index}][altoCm]", str(medidas["alto_cm"])),
                    (f"bultos[{index}][largoCm]", str(medidas["largo_cm"])),
                    (f"bultos[{index}][anchoCm]", str(medidas["ancho_cm"])),
                ]
            )

        return params

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

    def _extraer_precio(self, data):
        tarifa_con_iva = data.get("tarifaConIva") or {}
        tarifa_sin_iva = data.get("tarifaSinIva") or {}

        precio = self._to_float(tarifa_con_iva.get("total"))
        precio_sin_iva = self._to_float(tarifa_sin_iva.get("total"))

        if precio is not None:
            return precio, "tarifaConIva.total"
        if precio_sin_iva is not None:
            return precio_sin_iva, "tarifaSinIva.total"

        precio_legacy = self._to_float(data.get("tarifa"))
        if precio_legacy is not None:
            return precio_legacy, "tarifa"

        return None, None

    async def cotizar(self, origen: dict, destino: dict, bultos: list, **extras):
        """
        origen / destino: dicts con codigo postal y localidad.
        bultos: lista de objetos Bulto con peso en kg y medidas en metros.
        """
        config = self._config(extras)
        medidas = calcular_medidas_bultos(bultos)

        faltantes = [
            nombre
            for nombre in ("ANDREANI_CLIENTE", "ANDREANI_CONTRATO")
            if not config["cliente" if nombre == "ANDREANI_CLIENTE" else "contrato"]
        ]
        if faltantes:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"Faltan variables en .env: {', '.join(faltantes)}",
                "detalle": {
                    "ambiente": config["ambiente"],
                    "endpoint": config["tarifas_url"],
                    "cp_destino": destino["cp"],
                },
            }

        try:
            async with httpx.AsyncClient(
                timeout=20,
                follow_redirects=True,
                headers=self._headers(),
            ) as client:
                resp = await client.get(
                    config["tarifas_url"],
                    params=self._params(config, destino, bultos),
                )

        except httpx.RequestError as e:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"Error de conexion: {str(e)}",
                "detalle": {
                    "ambiente": config["ambiente"],
                    "endpoint": config["tarifas_url"],
                },
            }

        if resp.status_code != 200:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"HTTP {resp.status_code}: {resp.text[:300]}",
                "detalle": {
                    "ambiente": config["ambiente"],
                    "endpoint": str(resp.request.url),
                },
            }

        try:
            data = resp.json()
        except Exception:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "Respuesta no es JSON valido",
                "respuesta_raw": resp.text[:300],
            }

        precio, campo_precio = self._extraer_precio(data)
        if precio is None:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"No se pudo encontrar total de tarifa en la respuesta: {str(data)[:300]}",
                "detalle": {
                    "ambiente": config["ambiente"],
                    "endpoint": config["tarifas_url"],
                    "respuesta": data,
                },
            }

        return {
            "transportista": self.nombre,
            "precio": precio,
            "detalle": {
                "ambiente": config["ambiente"],
                "endpoint": config["tarifas_url"],
                "campo_precio": campo_precio,
                "cliente": config["cliente"],
                "contrato": config["contrato"],
                "sucursal_origen": config["sucursal_origen"] or None,
                "cp_origen": origen["cp"],
                "cp_destino": destino["cp"],
                "peso_total_kg": medidas["peso_total"],
                "peso_aforado_kg": self._to_float(data.get("pesoAforado")),
                "volumen_cm3": medidas["volumen_cm3"],
                "cantidad_bultos": medidas["cantidad_bultos"],
                "tarifa_sin_iva": data.get("tarifaSinIva"),
                "tarifa_con_iva": data.get("tarifaConIva"),
            },
        }


registrar_proveedor("andreani", AndreaniCotizador())
