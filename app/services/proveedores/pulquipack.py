import asyncio
import logging
import unicodedata
from datetime import datetime, timedelta, timezone

import httpx

from .base import TransportistaCotizador
from .factory import registrar_proveedor
from .utils import calcular_medidas_por_bulto


logger = logging.getLogger(__name__)

SYNC_URL = "https://www.pulquipack.com/api/admin/sync?action=sync-all"
SYNC_TTL = timedelta(minutes=30)
SYNC_RETRIES = 3
SYNC_RETRY_DELAY_SECONDS = 1

TIPOS_PAQUETE = (
    ("SOBRE", 0, 0.5, 1),
    ("CAJA_CH", 0.5, 5, 1.05),
    ("CAJA_MED", 5, 15, 1.15),
    ("CAJA_GR", 15, 30, 1.25),
    ("ESPECIAL", 30, None, 1.5),
)


class PulquipackCotizador(TransportistaCotizador):

    nombre = "pulquipack"

    def __init__(self):
        self._sync_cache = None
        self._sync_cache_at = None

    def _normalizar(self, texto):
        texto = unicodedata.normalize("NFKD", texto or "")
        texto = texto.encode("ascii", "ignore").decode("ascii")
        for caracter in (".", ",", "-", "_", "(", ")"):
            texto = texto.replace(caracter, " ")
        return " ".join(texto.upper().split())

    def _to_float(self, value, default=0):
        if value is None:
            return default
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
            return default

    def _score_nombre(self, actual, objetivo):
        actual_norm = self._normalizar(actual)
        objetivo_norm = self._normalizar(objetivo)
        if not actual_norm or not objetivo_norm:
            return 0
        if actual_norm == objetivo_norm:
            return 100
        if actual_norm.startswith(objetivo_norm) or objetivo_norm.startswith(actual_norm):
            return 85
        if objetivo_norm in actual_norm or actual_norm in objetivo_norm:
            return 70
        actual_partes = set(actual_norm.split())
        objetivo_partes = set(objetivo_norm.split())
        comunes = actual_partes & objetivo_partes
        if comunes:
            return 40 + (len(comunes) * 5)
        return 0

    def _buscar_mejor(self, items, campo, nombre):
        candidatos = []
        for item in items:
            score = self._score_nombre(item.get(campo), nombre)
            if score:
                candidatos.append((score, item))
        if not candidatos:
            return None
        candidatos.sort(key=lambda item: item[0], reverse=True)
        return candidatos[0][1]

    def _extraer_origenes(self, tarifas):
        origenes = {}
        for tarifa in tarifas:
            codigo = str(tarifa.get("pvOrigen") or "").strip()
            nombre = str(tarifa.get("sucursalOrigen") or "").strip()
            if codigo and nombre and nombre != "." and codigo not in origenes:
                origenes[codigo] = {
                    "codigo": codigo,
                    "nombre": nombre,
                }
        return list(origenes.values())

    def _extraer_destinos(self, tarifas, codigo_origen):
        destinos = {}
        for tarifa in tarifas:
            if str(tarifa.get("pvOrigen") or "").strip() != codigo_origen:
                continue
            codigo = str(tarifa.get("pvDestino") or "").strip()
            nombre = str(tarifa.get("destino") or "").strip()
            if codigo and nombre and nombre != "." and codigo not in destinos:
                destinos[codigo] = {
                    "codigo": codigo,
                    "nombre": nombre,
                    "codTarifa": str(tarifa.get("codTarifa") or "").strip(),
                    "descripcionTarifa": tarifa.get("descripcionTarifa"),
                }
        return list(destinos.values())

    def _buscar_tarifa_ruta(self, tarifas, origen, destino):
        for tarifa in tarifas:
            if (
                str(tarifa.get("pvOrigen") or "").strip() == origen["codigo"]
                and str(tarifa.get("pvDestino") or "").strip() == destino["codigo"]
            ):
                return tarifa
        return None

    def _tipo_paquete(self, peso):
        for tipo, desde, hasta, factor in TIPOS_PAQUETE:
            if hasta is None and peso > desde:
                return tipo, factor
            if peso > desde and peso <= hasta:
                return tipo, factor
            if desde == 0 and peso <= hasta:
                return tipo, factor
        return "ESPECIAL", 1.5

    def _calcular_medidas(self, bultos):
        medidas = calcular_medidas_por_bulto(bultos)
        peso_total = sum(self._to_float(m["peso"]) for m in medidas)
        volumenes_bulto_m3 = [
            self._to_float(m["volumen_cm3"]) / 1_000_000 for m in medidas
        ]
        volumen_total_m3 = sum(volumenes_bulto_m3)
        volumen_cotizable_m3 = max(volumenes_bulto_m3) if volumenes_bulto_m3 else 0
        peso_volumetrico = 250 * volumen_total_m3
        peso_facturado = max(peso_total, peso_volumetrico)

        return {
            "peso_total": peso_total,
            "volumen_m3": volumen_total_m3,
            "volumen_cotizable_m3": volumen_cotizable_m3,
            "peso_volumetrico": peso_volumetrico,
            "peso_facturado": peso_facturado,
            "cantidad_bultos": len(bultos),
            "por_bulto": medidas,
        }

    def _buscar_importe(self, importes, cod_tarifa, volumen_m3, express):
        for importe in importes:
            if str(importe.get("codTarifa") or "").strip() != cod_tarifa:
                continue
            desde = self._to_float(importe.get("m3Desde"))
            hasta = self._to_float(importe.get("m3Hasta"))
            if volumen_m3 >= desde and volumen_m3 <= hasta:
                precio = self._to_float(
                    importe.get("fleteExpress" if express else "flete"),
                    default=None,
                )
                if precio is None or precio <= 0:
                    return None, importe
                return precio, importe
        return None, None

    async def _obtener_sync(self):
        ahora = datetime.now(timezone.utc)
        if (
            self._sync_cache is not None
            and self._sync_cache_at is not None
            and ahora - self._sync_cache_at < SYNC_TTL
        ):
            return self._sync_cache

        ultimo_error = None

        for intento in range(1, SYNC_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
                    resp = await client.get(SYNC_URL)
                    resp.raise_for_status()
                    data = resp.json()

                self._sync_cache = data
                self._sync_cache_at = ahora
                return data

            except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as exc:
                ultimo_error = exc
                logger.warning(
                    "Pulquipack sync fallo intento=%s/%s error=%s",
                    intento,
                    SYNC_RETRIES,
                    exc,
                )
                if intento < SYNC_RETRIES:
                    await asyncio.sleep(SYNC_RETRY_DELAY_SECONDS)

        if self._sync_cache is not None:
            logger.warning(
                "Pulquipack usa cache vencida por fallo de red/error remoto. cache_at=%s error=%s",
                self._sync_cache_at,
                ultimo_error,
            )
            return self._sync_cache

        raise ultimo_error or RuntimeError("Pulquipack no pudo obtener tarifas.")

    async def cotizar(self, origen: dict, destino: dict, bultos: list, **extras):
        origen_nombre = extras.get("pulquipack_origen") or origen.get("localidad")
        destino_nombre = extras.get("pulquipack_destino") or destino.get("localidad")
        express = bool(extras.get("pulquipack_express", False))

        if not origen_nombre or not destino_nombre:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "Pulquipack requiere localidad de origen y destino.",
            }

        try:
            data = await self._obtener_sync()
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
                "error": f"Error procesando respuesta de Pulquipack: {str(e)}",
            }

        if not data.get("success"):
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": data.get("error") or "Pulquipack no devolvio datos de tarifas.",
                "detalle": data,
            }

        tarifas = data.get("tarifas") or []
        importes = data.get("importes") or []
        origenes = self._extraer_origenes(tarifas)
        origen_pulquipack = self._buscar_mejor(origenes, "nombre", origen_nombre)
        if not origen_pulquipack:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"Pulquipack no encontro sucursal origen para: {origen_nombre}",
                "detalle": {"origenes_disponibles": origenes[:30]},
            }

        destinos = self._extraer_destinos(tarifas, origen_pulquipack["codigo"])
        destino_pulquipack = self._buscar_mejor(destinos, "nombre", destino_nombre)
        if not destino_pulquipack:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"Pulquipack no encontro destino para: {destino_nombre}",
                "detalle": {
                    "origen_pulquipack": origen_pulquipack,
                    "destinos_disponibles": destinos[:30],
                },
            }

        tarifa_ruta = self._buscar_tarifa_ruta(
            tarifas,
            origen_pulquipack,
            destino_pulquipack,
        )
        if not tarifa_ruta:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "Pulquipack no encontro tarifa para la ruta seleccionada.",
                "detalle": {
                    "origen_pulquipack": origen_pulquipack,
                    "destino_pulquipack": destino_pulquipack,
                },
            }

        medidas = self._calcular_medidas(bultos)
        cod_tarifa = str(tarifa_ruta.get("codTarifa") or "").strip()
        precio_base, importe = self._buscar_importe(
            importes,
            cod_tarifa,
            medidas["volumen_cotizable_m3"],
            express,
        )
        if precio_base is None:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "Pulquipack no encontro rango de precio para el volumen del envio.",
                "detalle": {
                    "cod_tarifa": cod_tarifa,
                    "volumen_m3": medidas["volumen_m3"],
                    "volumen_cotizable_m3": medidas["volumen_cotizable_m3"],
                    "express": express,
                },
            }

        tipo_paquete, factor_tipo = self._tipo_paquete(medidas["peso_facturado"])
        precio = precio_base * factor_tipo
        incremento_bulto = self._to_float(importe.get("incrementoBulto"))
        if medidas["cantidad_bultos"] > 1:
            precio *= 1 + (((medidas["cantidad_bultos"] - 1) * incremento_bulto) / 100)

        return {
            "transportista": self.nombre,
            "precio": round(precio, 2),
            "detalle": {
                "origen_pulquipack": origen_pulquipack,
                "destino_pulquipack": destino_pulquipack,
                "tarifa_ruta": tarifa_ruta,
                "importe": importe,
                "precio_base": precio_base,
                "tipo_paquete": tipo_paquete,
                "factor_tipo": factor_tipo,
                "incremento_bulto": incremento_bulto,
                "express": express,
                "medidas": medidas,
                "last_sync": data.get("lastSync"),
            },
        }


registrar_proveedor("pulquipack", PulquipackCotizador())
registrar_proveedor("pulqui", PulquipackCotizador())
registrar_proveedor("pulquipacksrl", PulquipackCotizador())
