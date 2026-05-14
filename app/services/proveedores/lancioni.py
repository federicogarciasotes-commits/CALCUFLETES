import httpx

from .base import TransportistaCotizador
from .factory import registrar_proveedor
from .utils import calcular_medidas_bultos


BASE_URL = "https://expresolancioni.com"
AJAX_URL = BASE_URL + "/includes/consultas_ajax.php"

# Datos requeridos por el formulario; no afectan el precio.
DATOS_REMITENTE = {
    "txt_nombre": "Cotizador",
    "txt_telefono": "3510000000",
    "txt_email": "cotizador@empresa.com",
    "cuit": "20000000000",
}


class LancioniCotizador(TransportistaCotizador):

    nombre = "lancioni"
    MAX_VOLUMEN_BULTO_CM3 = 3_000_000

    async def _buscar_localidad(
        self,
        client: httpx.AsyncClient,
        nombre: str,
        loco: str = "",
        suco: str = "",
    ) -> dict | None:
        """Autocomplete de localidades. Devuelve la primera opcion."""
        params = {"modulo": "buscar_localidad2", "term": nombre}
        if loco:
            params["ret"] = "1"
            params["loco"] = loco
            params["suco"] = suco

        resp = await client.get(AJAX_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None

    async def _obtener_id_bulto(self, client: httpx.AsyncClient) -> str | None:
        """
        Llama a buscar_detalle_envio para inicializar la sesion de cotizacion.
        Devuelve el ID del bulto que viene al final de la respuesta: ...|1|ID
        """
        params = {"modulo": "buscar_detalle_envio", "tipo": "2", "int": "0"}
        resp = await client.get(AJAX_URL, params=params)
        resp.raise_for_status()

        partes = resp.text.split("|")
        if len(partes) >= 3:
            return partes[-1].strip()
        return None

    async def _agregar_bulto(self, client: httpx.AsyncClient) -> str | None:
        """
        Agrega un bulto extra a la sesion actual.
        Devuelve el ID del nuevo bulto: ...|cantidad|ID
        """
        params = {"modulo": "add_fila_coti", "int": "0"}
        resp = await client.get(AJAX_URL, params=params)
        resp.raise_for_status()

        partes = resp.text.split("|")
        if len(partes) >= 3:
            return partes[-1].strip()
        return None

    async def _guardar_campo_bulto(
        self,
        client: httpx.AsyncClient,
        campo: str,
        id_bulto: str,
        valor: str,
    ):
        """Guarda un campo del bulto en el servidor."""
        params = {
            "modulo": "actualiza_campo_coti",
            "campo": campo,
            "id": id_bulto,
            "valor": valor,
            "tipo": "2",
        }
        await client.get(AJAX_URL, params=params)

    async def _guardar_bulto(self, client: httpx.AsyncClient, id_bulto: str, medidas: dict):
        await self._guardar_campo_bulto(
            client,
            "cpc_kilos",
            id_bulto,
            str(round(medidas["peso"], 2)),
        )
        await self._guardar_campo_bulto(client, "cpc_ancho", id_bulto, str(medidas["ancho_cm"]))
        await self._guardar_campo_bulto(client, "cpc_alto", id_bulto, str(medidas["alto_cm"]))
        await self._guardar_campo_bulto(client, "cpc_largo", id_bulto, str(medidas["largo_cm"]))

    def _construir_bulto_lancioni(self, volumen_cm3, peso):
        alto_cm = round(volumen_cm3 / 10_000, 2)
        return {
            "peso": round(peso, 2),
            "ancho_cm": 100,
            "largo_cm": 100,
            "alto_cm": alto_cm,
            "volumen_cm3": volumen_cm3,
        }

    def _consolidar_bultos(self, bultos):
        pendientes = []
        for bulto in bultos:
            volumen_cm3 = round(float(bulto.volumen) * 1_000_000)
            if volumen_cm3 <= 0:
                continue
            pendientes.append(
                {
                    "peso": float(bulto.peso),
                    "volumen_cm3": volumen_cm3,
                }
            )

        consolidados = []
        volumen_actual = 0
        peso_actual = 0.0

        for item in pendientes:
            volumen_restante = item["volumen_cm3"]
            peso_restante = item["peso"]

            while volumen_restante > 0:
                capacidad = self.MAX_VOLUMEN_BULTO_CM3 - volumen_actual
                volumen_tomado = min(volumen_restante, capacidad)
                proporcion = volumen_tomado / volumen_restante
                peso_tomado = peso_restante * proporcion

                volumen_actual += volumen_tomado
                peso_actual += peso_tomado
                volumen_restante -= volumen_tomado
                peso_restante -= peso_tomado

                if volumen_actual >= self.MAX_VOLUMEN_BULTO_CM3:
                    consolidados.append(
                        self._construir_bulto_lancioni(volumen_actual, peso_actual)
                    )
                    volumen_actual = 0
                    peso_actual = 0.0

        if volumen_actual > 0:
            consolidados.append(
                self._construir_bulto_lancioni(volumen_actual, peso_actual)
            )

        return consolidados

    async def cotizar(self, origen: dict, destino: dict, bultos: list, **extras):
        """
        origen / destino: dicts con codigo postal y localidad.
        bultos: lista de objetos Bulto con peso en kg y medidas en metros.

        extras opcionales:
            valor_declarado: float (default 60000)
            con_retiro:      bool  (default True)
            con_entrega:     bool  (default True)
        """
        origen_nombre = origen["localidad"]
        destino_nombre = destino["localidad"]
        valor_declarado = extras.get("valor_declarado", 60000)
        con_retiro = extras.get("con_retiro", True)
        con_entrega = extras.get("con_entrega", True)
        medidas = calcular_medidas_bultos(bultos)
        medidas_por_bulto = self._consolidar_bultos(bultos)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": BASE_URL + "/cotizador",
        }

        try:
            async with httpx.AsyncClient(
                timeout=15,
                follow_redirects=True,
                headers=headers,
            ) as client:

                loc_origen = await self._buscar_localidad(client, origen_nombre)
                if not loc_origen:
                    return {
                        "transportista": self.nombre,
                        "precio": None,
                        "error": f"Localidad origen no encontrada: '{origen_nombre}'",
                    }

                id_origen = str(loc_origen["id"])
                suc_origen = str(loc_origen["sucid"])

                loc_destino = await self._buscar_localidad(
                    client,
                    destino_nombre,
                    loco=id_origen,
                    suco=suc_origen,
                )
                if not loc_destino:
                    return {
                        "transportista": self.nombre,
                        "precio": None,
                        "error": f"Localidad destino no encontrada: '{destino_nombre}'",
                    }

                id_destino = str(loc_destino["id"])
                suc_destino = str(loc_destino["sucid"])

                id_bulto = await self._obtener_id_bulto(client)
                if not id_bulto:
                    return {
                        "transportista": self.nombre,
                        "precio": None,
                        "error": "No se pudo obtener el ID de bulto de la sesion",
                    }

                ids_bultos = [id_bulto]
                for _ in range(1, len(medidas_por_bulto)):
                    nuevo_id = await self._agregar_bulto(client)
                    if not nuevo_id:
                        return {
                            "transportista": self.nombre,
                            "precio": None,
                            "error": "No se pudo agregar un bulto extra en la sesion",
                        }
                    ids_bultos.append(nuevo_id)

                for id_actual, medidas_bulto in zip(ids_bultos, medidas_por_bulto):
                    await self._guardar_bulto(client, id_actual, medidas_bulto)

                payload = {
                    "modulo": "procesar_cotizacion",
                    "tipo": "2",
                    "vcontra": "",
                    "vdeclarado": str(int(valor_declarado)),
                    "eentrega": "1" if con_entrega else "2",
                    "rretira": "1" if con_retiro else "2",
                    "locaorigen": id_origen,
                    "locadestino": id_destino,
                    "sucorigen": suc_origen,
                    "sucdestino": suc_destino,
                    "calleo": "",
                    "alturao": "",
                    "pisoo": "",
                    "deptoo": "",
                    "called": "",
                    "alturad": "",
                    "pisod": "",
                    "deptod": "",
                    "txt_nrocot": "",
                    "txt_nombre": DATOS_REMITENTE["txt_nombre"],
                    "txt_telefono": DATOS_REMITENTE["txt_telefono"],
                    "txt_dni": "",
                    "txt_email": DATOS_REMITENTE["txt_email"],
                    "txt_nombre2": "",
                    "txt_telefono2": "",
                    "txt_dni2": "",
                    "txt_email2": "",
                    "tipocontra": "0",
                    "cuit": DATOS_REMITENTE["cuit"],
                    "ageorigen": "",
                    "agedestino": "",
                    "ageinternacional": "",
                }

                resp = await client.get(AJAX_URL, params=payload)

        except httpx.RequestError as e:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"Error de conexion: {str(e)}",
            }

        if resp.status_code != 200:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"HTTP {resp.status_code}",
            }

        partes = resp.text.split("|")

        if len(partes) >= 3 and partes[2].strip():
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": partes[2].strip(),
                "respuesta_raw": resp.text[:300],
            }

        try:
            precio = float(partes[1].replace(",", "."))
        except (IndexError, ValueError):
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "No se pudo parsear el precio",
                "respuesta_raw": resp.text[:300],
            }

        return {
            "transportista": self.nombre,
            "precio": precio,
            "detalle": {
                "nro_cotizacion": partes[0] if partes else "",
                "localidad_origen": loc_origen.get("value", origen_nombre),
                "localidad_destino": loc_destino.get("value", destino_nombre),
                "con_retiro": con_retiro,
                "con_entrega": con_entrega,
                "valor_declarado": valor_declarado,
                "peso_total_kg": medidas["peso_total"],
                "cantidad_bultos": medidas["cantidad_bultos"],
                "bulto_mayor": medidas["bulto_mayor"],
                "volumen_total_cm3": medidas["volumen_cm3"],
                "por_bulto": medidas_por_bulto,
            },
        }


registrar_proveedor("lancioni", LancioniCotizador())
