import httpx

from .base import TransportistaCotizador
from .factory import registrar_proveedor


BASE_URL = "https://expresolancioni.com"
AJAX_URL = BASE_URL + "/includes/consultas_ajax.php"

# Datos requeridos por el formulario — no afectan el precio
DATOS_REMITENTE = {
    "txt_nombre":   "Cotizador",
    "txt_telefono": "3510000000",
    "txt_email":    "cotizador@empresa.com",
    "cuit":         "20000000000",
}


class LancioniCotizador(TransportistaCotizador):

    nombre = "lancioni"

    async def _buscar_localidad(self, client: httpx.AsyncClient, nombre: str, loco: str = "", suco: str = "") -> dict | None:
        """Autocomplete de localidades. Devuelve la primera opción."""
        params = {"modulo": "buscar_localidad2", "term": nombre}
        if loco:
            params["ret"]  = "1"
            params["loco"] = loco
            params["suco"] = suco

        resp = await client.get(AJAX_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None

    async def _obtener_id_bulto(self, client: httpx.AsyncClient) -> str | None:
        """
        Llama a buscar_detalle_envio para inicializar la sesión de cotización.
        Devuelve el ID del bulto que viene al final de la respuesta: ...|1|ID
        """
        params = {"modulo": "buscar_detalle_envio", "tipo": "2", "int": "0"}
        resp = await client.get(AJAX_URL, params=params)
        resp.raise_for_status()

        # La respuesta es HTML|cantidad|id_bulto
        partes = resp.text.split("|")
        if len(partes) >= 3:
            return partes[-1].strip()
        return None

    async def _guardar_campo_bulto(self, client: httpx.AsyncClient, campo: str, id_bulto: str, valor: str):
        """Guarda un campo del bulto en el servidor."""
        params = {
            "modulo": "actualiza_campo_coti",
            "campo":  campo,
            "id":     id_bulto,
            "valor":  valor,
            "tipo":   "2",
        }
        await client.get(AJAX_URL, params=params)

    async def cotizar(self, origen: str, destino: str, bultos: list, **extras):
        """
        origen / destino: nombre de ciudad (ej: "Córdoba", "Buenos Aires")
        bultos: lista de objetos Bulto con peso en kg y medidas en metros

        extras opcionales:
            valor_declarado: float (default 60000)
            con_retiro:      bool  (default True)
            con_entrega:     bool  (default True)
        """
        valor_declarado = extras.get("valor_declarado", 60000)
        con_retiro      = extras.get("con_retiro", True)
        con_entrega     = extras.get("con_entrega", True)

        # Consolidar bultos: peso total, dimensiones máximas en CM
        peso_total = sum(b.peso for b in bultos)
        alto_cm    = round(max(b.alto  for b in bultos) * 100)
        ancho_cm   = round(max(b.ancho for b in bultos) * 100)
        largo_cm   = round(max(b.largo for b in bultos) * 100)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer":    BASE_URL + "/cotizador",
        }

        try:
            async with httpx.AsyncClient(
                timeout=15,
                follow_redirects=True,
                headers=headers,
            ) as client:

                # 1. Resolver localidad origen
                loc_origen = await self._buscar_localidad(client, origen)
                if not loc_origen:
                    return {"transportista": self.nombre, "precio": None,
                            "error": f"Localidad origen no encontrada: '{origen}'"}

                id_origen  = str(loc_origen["id"])
                suc_origen = str(loc_origen["sucid"])

                # 2. Resolver localidad destino
                loc_destino = await self._buscar_localidad(
                    client, destino, loco=id_origen, suco=suc_origen
                )
                if not loc_destino:
                    return {"transportista": self.nombre, "precio": None,
                            "error": f"Localidad destino no encontrada: '{destino}'"}

                id_destino  = str(loc_destino["id"])
                suc_destino = str(loc_destino["sucid"])

                # 3. Obtener ID del bulto de la sesión
                id_bulto = await self._obtener_id_bulto(client)
                if not id_bulto:
                    return {"transportista": self.nombre, "precio": None,
                            "error": "No se pudo obtener el ID de bulto de la sesión"}

                # 4. Guardar dimensiones del bulto en el servidor
                await self._guardar_campo_bulto(client, "cpc_kilos", id_bulto, str(round(peso_total, 2)))
                await self._guardar_campo_bulto(client, "cpc_ancho", id_bulto, str(ancho_cm))
                await self._guardar_campo_bulto(client, "cpc_alto",  id_bulto, str(alto_cm))
                await self._guardar_campo_bulto(client, "cpc_largo", id_bulto, str(largo_cm))

                # 5. Cotizar
                payload = {
                    "modulo":        "procesar_cotizacion",
                    "tipo":          "2",
                    "vcontra":       "",
                    "vdeclarado":    str(int(valor_declarado)),
                    "eentrega":      "1" if con_entrega else "2",
                    "rretira":       "1" if con_retiro  else "2",
                    "locaorigen":    id_origen,
                    "locadestino":   id_destino,
                    "sucorigen":     suc_origen,
                    "sucdestino":    suc_destino,
                    "calleo":        "",
                    "alturao":       "",
                    "pisoo":         "",
                    "deptoo":        "",
                    "called":        "",
                    "alturad":       "",
                    "pisod":         "",
                    "deptod":        "",
                    "txt_nrocot":    "",
                    "txt_nombre":    DATOS_REMITENTE["txt_nombre"],
                    "txt_telefono":  DATOS_REMITENTE["txt_telefono"],
                    "txt_dni":       "",
                    "txt_email":     DATOS_REMITENTE["txt_email"],
                    "txt_nombre2":   "",
                    "txt_telefono2": "",
                    "txt_dni2":      "",
                    "txt_email2":    "",
                    "tipocontra":    "0",
                    "cuit":          DATOS_REMITENTE["cuit"],
                    "ageorigen":     "",
                    "agedestino":    "",
                    "ageinternacional": "",
                }

                resp = await client.get(AJAX_URL, params=payload)

        except httpx.RequestError as e:
            return {"transportista": self.nombre, "precio": None,
                    "error": f"Error de conexión: {str(e)}"}

        if resp.status_code != 200:
            return {"transportista": self.nombre, "precio": None,
                    "error": f"HTTP {resp.status_code}"}

        # Respuesta: nrocot|precio|error|descuento
        partes = resp.text.split("|")

        if len(partes) >= 3 and partes[2].strip():
            return {"transportista": self.nombre, "precio": None,
                    "error": partes[2].strip(),
                    "respuesta_raw": resp.text[:300]}

        try:
            precio = float(partes[1].replace(",", "."))
        except (IndexError, ValueError):
            return {"transportista": self.nombre, "precio": None,
                    "error": "No se pudo parsear el precio",
                    "respuesta_raw": resp.text[:300]}

        return {
            "transportista": self.nombre,
            "precio":        precio,
            "detalle": {
                "nro_cotizacion":    partes[0] if partes else "",
                "localidad_origen":  loc_origen.get("value", origen),
                "localidad_destino": loc_destino.get("value", destino),
                "con_retiro":        con_retiro,
                "con_entrega":       con_entrega,
                "valor_declarado":   valor_declarado,
                "peso_total_kg":     peso_total,
            }
        }


# auto registro
registrar_proveedor("lancioni", LancioniCotizador())