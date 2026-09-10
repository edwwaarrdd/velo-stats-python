from abc import ABC, abstractmethod
from datetime import datetime

from routing.models import Coordinate

from .models import WeatherObservation


class WeatherService(ABC):
    """Interface for fetching the historical weather at a location and time."""

    @abstractmethod
    def get_weather(self, location: Coordinate, at: datetime) -> WeatherObservation:
        """Fetch the weather observed closest to the given time at the given location."""
