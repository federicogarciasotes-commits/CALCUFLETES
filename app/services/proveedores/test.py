import asyncio
from app.services.proveedores.lancioni import LancioniCotizador
from app.schemas.cotizacion import Bulto

async def test():
    lc = LancioniCotizador()
    bultos = [Bulto(peso=10, alto=0.5, ancho=1.0, largo=2.0, volumen=1.0)]
    result = await lc.cotizar("Córdoba", "Buenos Aires", bultos)
    print(result)

asyncio.run(test())