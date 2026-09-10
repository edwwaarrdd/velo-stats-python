import json
from pathlib import Path

from django.conf import settings

from .interfaces import RideDataSource
from .models import Ride, RideCollection

DEFAULT_RIDES_FILE = Path(settings.BASE_DIR) / "data" / "rides.json"


class JsonFileRideService(RideDataSource):
    def __init__(self, path: str | Path = DEFAULT_RIDES_FILE):
        self._path = Path(path)

    def fetch_rides(self) -> RideCollection:
        with self._path.open(encoding="utf-8") as f:
            payload = json.load(f)

        rides = (Ride.from_dict(ride_data) for ride_data in payload["data"]["CustomerRides"])
        return RideCollection(rides)
