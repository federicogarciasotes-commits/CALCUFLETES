import asyncio
from .proveedores.factory import obtener_proveedor
from app.repositories.transportista_repository import TransportistaRepository
from app.schemas.cotizacion import Bulto


class CotizadorService:

    def __init__(self, db):
        self.repo = TransportistaRepository(db)

    def generar_bultos(self, cantidad_bultos, peso_total):

        ALTO   = 0.5
        ANCHO  = 1
        LARGO  = 2
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
                    volumen=VOLUMEN
                )
            )
        return bultos

    async def cotizar_envio(self, data):

        # Localidad origen
        localidad_origen = self.repo.obtener_localidad(data.localidad_origen_id)
        cp_origen        = localidad_origen.cp_principal
        nombre_origen    = localidad_origen.nombre

        # Localidad destino
        localidad_destino = self.repo.obtener_localidad(data.localidad_destino_id)
        cp_destino        = localidad_destino.cp_principal
        nombre_destino    = localidad_destino.nombre

        # Transportistas que llegan al destino
        transportistas = self.repo.obtener_por_localidad(data.localidad_destino_id)

        bultos = self.generar_bultos(data.cantidad_bultos, data.peso_total)

        tareas = []

        for t in transportistas:

            nombre_normalizado = t.nombre.lower().replace(" ", "")
            proveedor = obtener_proveedor(nombre_normalizado)
            if not proveedor:
                continue

            # Cada proveedor recibe el formato que necesita
            if t.nombre == "Via cargo":
                tareas.append(proveedor.cotizar(cp_origen, cp_destino, bultos))

            elif t.nombre == "Lancioni":
                tareas.append(proveedor.cotizar(nombre_origen, nombre_destino, bultos))

            elif t.nombre == "andreani":
                tareas.append(proveedor.cotizar(cp_origen, cp_destino, bultos))

            else:
                # Fallback genérico: CP
                tareas.append(proveedor.cotizar(cp_origen, cp_destino, bultos))

        if not tareas:
            return []

        resultados = await asyncio.gather(*tareas, return_exceptions=True)

        # Filtrar excepciones inesperadas
        limpios = []
        for r in resultados:
            if isinstance(r, Exception):
                limpios.append({"transportista": "desconocido", "precio": None, "error": str(r)})
            else:
                limpios.append(r)

        # Ordenar por precio (los que tienen precio primero, los errores al final)
        limpios.sort(key=lambda x: (x.get("precio") is None, x.get("precio") or 0))

        return limpios