from abc import ABC, abstractmethod
from datetime import datetime

from routing.models import Coordinate

from .models import WeatherObservation


class WeatherService(ABC):
    @abstractmethod
    def get_weather(self, location: Coordinate, at: datetime) -> WeatherObservation: ...
