from abc import ABC, abstractmethod


class TransportistaCotizador(ABC):

    @abstractmethod
    async def cotizar(self, origen: dict, destino: dict, bultos: list, **extras):
        pass