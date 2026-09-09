from abc import ABC, abstractmethod

from .models import Coordinate, Route, TravelMode


class RouteService(ABC):
    """Interface for calculating a route between two coordinates."""

    @abstractmethod
    def get_route(
        self, origin: Coordinate, destination: Coordinate, mode: TravelMode
    ) -> Route:
        """Calculate the route between origin and destination for the given travel mode."""
