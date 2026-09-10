from abc import ABC, abstractmethod

from .models import RideCollection


class RideDataSource(ABC):
    @abstractmethod
    def fetch_rides(self) -> RideCollection: ...
