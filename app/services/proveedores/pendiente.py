from .utils import calcular_medidas_bultos


def respuesta_pendiente(nombre, origen, destino, bultos, mensaje, canal_contacto=None):
    medidas = calcular_medidas_bultos(bultos)

    detalle = {
        "origen": origen,
        "destino": destino,
        "peso_total": medidas["peso_total"],
        "cantidad_bultos": medidas["cantidad_bultos"],
        "estado": "pendiente_integracion",
    }

    if canal_contacto:
        detalle["canal_contacto"] = canal_contacto

    return {
        "transportista": nombre,
        "precio": None,
        "error": mensaje,
        "detalle": detalle,
    }
