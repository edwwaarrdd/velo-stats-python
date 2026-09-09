from abc import ABC, abstractmethod

from .models import RideCollection


class RideDataSource(ABC):
    """Interface for fetching bike-share ride history."""

    @abstractmethod
    def fetch_rides(self) -> RideCollection:
        """Fetch ride history and return it as a RideCollection."""
