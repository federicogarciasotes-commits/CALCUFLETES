import os
import httpx

from .base import TransportistaCotizador
from .factory import registrar_proveedor


# Cotizador web (referencia humana):
#   https://pymes.andreani.com/cotizador
#
# API REST oficial:
#   https://developers.andreani.com/
#
# Credenciales requeridas (las otorga Andreani al abrir cuenta):
#   ANDREANI_USUARIO  — variable de entorno con el usuario de API
#   ANDREANI_PASSWORD — variable de entorno con la contraseña de API

BASE_URL    = "https://apx.andreani.com"
LOGIN_URL   = BASE_URL + "/v1/login"
TARIFAS_URL = BASE_URL + "/v1/tarifas"

# Contratos estándar (los mismos para todas las cuentas)
CONTRATO_DOMICILIO = "AND00EST"   # Entrega estándar a domicilio
CONTRATO_SUCURSAL  = "AND00SUC"   # Retiro en sucursal Andreani


class AndreaniCotizador(TransportistaCotizador):

    nombre = "andreani"

    def __init__(self):
        self._usuario  = os.environ.get("ANDREANI_USUARIO", "")
        self._password = os.environ.get("ANDREANI_PASSWORD", "")
        self._token: str | None = None

    async def _login(self, client: httpx.AsyncClient) -> str:
        """Obtiene el token Bearer. Lo cachea en la instancia."""
        if self._token:
            return self._token

        resp = await client.get(
            LOGIN_URL,
            auth=(self._usuario, self._password),
        )
        resp.raise_for_status()
        # Andreani devuelve el token en el header x-authorization-token
        self._token = resp.headers.get("x-authorization-token") or resp.text.strip()
        return self._token

    async def cotizar(self, origen_cp: str, destino_cp: str, bultos: list, **extras):
        """
        origen_cp  / destino_cp : código postal como string (ej: "5000")
        bultos                  : lista de objetos Bulto con peso en kg y medidas en metros

        extras opcionales:
            valor_declarado : float  (default 60_000)
            modalidad       : "D" = domicilio (default) | "S" = sucursal
        """
        peso_total      = sum(b.peso for b in bultos)
        alto_cm         = round(max(b.alto  for b in bultos) * 100)
        ancho_cm        = round(max(b.ancho for b in bultos) * 100)
        largo_cm        = round(max(b.largo for b in bultos) * 100)
        volumen_cc      = alto_cm * ancho_cm * largo_cm   # cm³
        valor_declarado = extras.get("valor_declarado", 60_000)
        modalidad       = extras.get("modalidad", "D")

        contrato = CONTRATO_DOMICILIO if modalidad == "D" else CONTRATO_SUCURSAL

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        try:
            async with httpx.AsyncClient(
                timeout=15,
                follow_redirects=True,
                headers=headers,
            ) as client:

                # 1. Autenticar y obtener token
                try:
                    token = await self._login(client)
                except httpx.HTTPStatusError as e:
                    return {
                        "transportista": self.nombre,
                        "precio": None,
                        "error": (
                            f"Login fallido (HTTP {e.response.status_code}). "
                            "Verificá usuario y contraseña de Andreani."
                        ),
                    }

                # 2. Cotizar
                params = {
                    "cpDestino":      str(destino_cp),
                    "cpOrigen":       str(origen_cp),
                    "contrato":       contrato,
                    "peso":           str(round(peso_total * 1000)),  # gramos
                    "volumen":        str(volumen_cc),                # cm³
                    "valorDeclarado": str(int(valor_declarado)),
                    "cantidadBultos": str(len(bultos)),
                }

                resp = await client.get(
                    TARIFAS_URL,
                    params=params,
                    headers={"x-authorization-token": token},
                )

        except httpx.RequestError as e:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"Error de conexión: {str(e)}",
            }

        if resp.status_code != 200:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
            }

        try:
            data = resp.json()
        except Exception:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": "Respuesta no es JSON válido",
                "respuesta_raw": resp.text[:300],
            }

        # La API devuelve {"tarifa": 1234.56, "pesoAforado": 2.0, ...}
        tarifa = data.get("tarifa")
        if tarifa is None:
            return {
                "transportista": self.nombre,
                "precio": None,
                "error": f"Campo 'tarifa' ausente en la respuesta: {str(data)[:200]}",
            }

        return {
            "transportista": self.nombre,
            "precio": float(tarifa),
            "detalle": {
                "contrato":        contrato,
                "modalidad":       "domicilio" if modalidad == "D" else "sucursal",
                "cp_origen":       origen_cp,
                "cp_destino":      destino_cp,
                "peso_total_kg":   peso_total,
                "peso_aforado_kg": data.get("pesoAforado"),
                "volumen_cc":      volumen_cc,
                "valor_declarado": valor_declarado,
                "cantidad_bultos": len(bultos),
            },
        }


# auto registro
registrar_proveedor("andreani", AndreaniCotizador())