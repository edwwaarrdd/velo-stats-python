from abc import ABC, abstractmethod

from .models import StationCollection


class StationInformationService(ABC):
    @abstractmethod
    def fetch_stations(self) -> StationCollection: ...
