import unicodedata


PROVEEDORES = {}


def normalizar_nombre(nombre: str) -> str:
    texto = unicodedata.normalize("NFKD", nombre or "")
    texto = texto.encode("ascii", "ignore").decode("ascii")
    return (
        texto.lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
        .strip()
    )


def registrar_proveedor(nombre, proveedor):
    PROVEEDORES[normalizar_nombre(nombre)] = proveedor


def obtener_proveedor(nombre):
    return PROVEEDORES.get(normalizar_nombre(nombre))
