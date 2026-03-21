from abc import ABC, abstractmethod


class TransportistaCotizador(ABC):

    @abstractmethod
    async def cotizar(self, origen_cp: str, destino_cp: str, bultos: list):
        pass