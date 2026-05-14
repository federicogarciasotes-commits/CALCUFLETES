import asyncio
import logging
from math import floor

from . import proveedores as _proveedores
from .proveedores.factory import obtener_proveedor, normalizar_nombre
from app.repositories.transportista_repository import TransportistaRepository
from app.schemas.cotizacion import Bulto


logger = logging.getLogger(__name__)


class CotizadorService:

    VOLUMEN_BULTO_ESTANDAR = 1.0

    def __init__(self, db):
        self.repo = TransportistaRepository(db)

    def _clasificar_estado_resultado(self, resultado):
        if resultado.get("precio") is not None:
            return "cotizo"

        error = (resultado.get("error") or "").lower()
        patrones_cobertura = (
            "no encontro destino",
            "no encontro sucursal",
            "no encontro tarifa",
            "no encontro rango de precio",
            "requiere localidad",
            "sin cobertura",
            "no llega",
            "destino invalido",
            "origen invalido",
        )
        if any(patron in error for patron in patrones_cobertura):
            return "sin_cobertura"

        return "error_tecnico"

    def _crear_bulto_estimado(self, volumen_m3, peso):
        if volumen_m3 <= 0:
            volumen_m3 = self.VOLUMEN_BULTO_ESTANDAR

        if abs(volumen_m3 - self.VOLUMEN_BULTO_ESTANDAR) < 1e-9:
            alto = ancho = largo = 1.0
        else:
            lado = round(volumen_m3 ** (1 / 3), 4)
            alto = ancho = largo = lado

        return Bulto(
            peso=round(peso, 4),
            alto=alto,
            ancho=ancho,
            largo=largo,
            volumen=round(volumen_m3, 4),
        )

    def _generar_bultos_por_volumen(self, peso_total, volumen_total):
        volumen_total = round(volumen_total, 4)
        cantidad_bultos_enteros = floor(volumen_total / self.VOLUMEN_BULTO_ESTANDAR)
        restante = round(
            volumen_total - (cantidad_bultos_enteros * self.VOLUMEN_BULTO_ESTANDAR),
            4,
        )

        volumenes = [self.VOLUMEN_BULTO_ESTANDAR] * cantidad_bultos_enteros
        if restante > 0:
            volumenes.append(restante)

        if not volumenes:
            volumenes = [self.VOLUMEN_BULTO_ESTANDAR]
            volumen_total = self.VOLUMEN_BULTO_ESTANDAR

        bultos = []
        for volumen_bulto in volumenes:
            proporcion_peso = volumen_bulto / volumen_total
            peso_bulto = peso_total * proporcion_peso
            bultos.append(self._crear_bulto_estimado(volumen_bulto, peso_bulto))

        return bultos

    def generar_bultos(self, cantidad_bultos, peso_total, volumen_total=None):
        if volumen_total and volumen_total > 0:
            return self._generar_bultos_por_volumen(peso_total, volumen_total)

        ALTO = 0.5
        ANCHO = 1
        LARGO = 2
        VOLUMEN = ALTO * ANCHO * LARGO

        peso_por_bulto = peso_total / cantidad_bultos

        bultos = []
        for _ in range(cantidad_bultos):
            bultos.append(
                Bulto(
                    peso=peso_por_bulto,
                    alto=ALTO,
                    ancho=ANCHO,
                    largo=LARGO,
                    volumen=VOLUMEN,
                )
            )
        return bultos

    async def cotizar_con_proveedor(self, nombre, proveedor, origen, destino, bultos):
        logger.info(
            "Cotizando con proveedor=%s origen_cp=%s destino_cp=%s",
            nombre,
            origen["cp"],
            destino["cp"],
        )

        try:
            resultado = await proveedor.cotizar(origen, destino, bultos)
        except Exception as e:
            logger.exception("Error cotizando con proveedor=%s", nombre)
            return {
                "transportista": nombre,
                "precio": None,
                "estado": "error_tecnico",
                "error": str(e),
            }

        resultado["estado"] = self._clasificar_estado_resultado(resultado)

        if resultado["estado"] == "cotizo":
            logger.info(
                "Proveedor=%s estado=%s precio=%s",
                nombre,
                resultado["estado"],
                resultado.get("precio"),
            )
        elif resultado["estado"] == "sin_cobertura":
            logger.warning(
                "Proveedor=%s estado=%s error=%s",
                nombre,
                resultado["estado"],
                resultado.get("error"),
            )
        else:
            logger.error(
                "Proveedor=%s estado=%s error=%s",
                nombre,
                resultado["estado"],
                resultado.get("error"),
            )

        return resultado

    def _enriquecer_resultado(self, transportista, resultado):
        dias = [td.dia_reparto.nombre for td in transportista.dias]
        return {
            "id": transportista.id,
            "nombre": transportista.nombre,
            "descripcion": transportista.descripcion,
            "dias": dias,
            **resultado,
        }

    async def cotizar_envio(self, data):

        localidad_origen = self.repo.obtener_localidad(data.localidad_origen_id)
        localidad_destino = self.repo.obtener_localidad(data.localidad_destino_id)

        origen = {
            "localidad_id": data.localidad_origen_id,
            "localidad": localidad_origen.nombre,
            "provincia_id": localidad_origen.provincia_id,
            "provincia": localidad_origen.provincia.nombre if localidad_origen.provincia else None,
            "cp": localidad_origen.cp_principal,
        }

        destino = {
            "localidad_id": data.localidad_destino_id,
            "localidad": localidad_destino.nombre,
            "provincia_id": localidad_destino.provincia_id,
            "provincia": localidad_destino.provincia.nombre if localidad_destino.provincia else None,
            "cp": localidad_destino.cp_principal,
        }

        transportistas = self.repo.obtener_todos()
        bultos = self.generar_bultos(
            data.cantidad_bultos,
            data.peso_total,
            data.volumen_total,
        )

        logger.info(
            "Cotizando envio origen=%s destino=%s cantidad_bultos=%s peso_total=%s volumen_total=%s bultos_reales=%s transportistas=%s",
            origen,
            destino,
            data.cantidad_bultos,
            data.peso_total,
            data.volumen_total,
            len(bultos),
            len(transportistas),
        )

        tareas = []
        transportistas_en_tareas = []

        for t in transportistas:
            nombre_normalizado = normalizar_nombre(t.nombre)
            proveedor = obtener_proveedor(nombre_normalizado)
            if not proveedor:
                logger.warning(
                    "Transportista sin proveedor registrado nombre=%s normalizado=%s",
                    t.nombre,
                    nombre_normalizado,
                )
                continue

            tareas.append(
                self.cotizar_con_proveedor(
                    nombre_normalizado,
                    proveedor,
                    origen,
                    destino,
                    bultos,
                )
            )
            transportistas_en_tareas.append(t)

        if not tareas:
            return []

        resultados = await asyncio.gather(*tareas)
        resultados = [
            self._enriquecer_resultado(transportista, resultado)
            for transportista, resultado in zip(transportistas_en_tareas, resultados)
        ]

        resultados.sort(key=lambda x: (x.get("precio") is None, x.get("precio") or 0))

        logger.info("Cotizacion finalizada resultados=%s", len(resultados))

        return resultados
