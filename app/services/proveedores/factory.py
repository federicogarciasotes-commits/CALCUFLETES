PROVEEDORES = {}

def registrar_proveedor(nombre, proveedor):
    PROVEEDORES[nombre] = proveedor

def obtener_proveedor(nombre):
    return PROVEEDORES.get(nombre)