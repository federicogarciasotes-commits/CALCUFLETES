def _medidas_bulto(bulto):
    alto_cm = round(bulto.alto * 100)
    ancho_cm = round(bulto.ancho * 100)
    largo_cm = round(bulto.largo * 100)

    return {
        "peso": bulto.peso,
        "alto_cm": alto_cm,
        "ancho_cm": ancho_cm,
        "largo_cm": largo_cm,
        "volumen_cm3": alto_cm * ancho_cm * largo_cm,
    }


def calcular_medidas_por_bulto(bultos):
    return [_medidas_bulto(bulto) for bulto in bultos]


def calcular_medidas_bultos(bultos):
    medidas = calcular_medidas_por_bulto(bultos)
    peso_total = sum(m["peso"] for m in medidas)
    bulto_mayor = max(medidas, key=lambda m: m["volumen_cm3"])

    return {
        "peso_total": peso_total,
        "alto_cm": bulto_mayor["alto_cm"],
        "ancho_cm": bulto_mayor["ancho_cm"],
        "largo_cm": bulto_mayor["largo_cm"],
        "volumen_cm3": sum(m["volumen_cm3"] for m in medidas),
        "cantidad_bultos": len(bultos),
        "bulto_mayor": bulto_mayor,
        "por_bulto": medidas,
    }
