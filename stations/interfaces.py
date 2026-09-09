from abc import ABC, abstractmethod

from .models import StationCollection


class StationInformationService(ABC):
    """Interface for fetching bike-share station information."""

    @abstractmethod
    def fetch_stations(self) -> StationCollection:
        """Fetch current station information and return it as a StationCollection."""
