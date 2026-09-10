from abc import ABC, abstractmethod

from .models import Coordinate, Route, TravelMode


class RouteService(ABC):
    @abstractmethod
    def get_route(self, origin: Coordinate, destination: Coordinate, mode: TravelMode) -> Route: ...
