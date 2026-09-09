import json
import urllib.request

from .interfaces import StationInformationService
from .models import Station, StationCollection

VELO_ANTWERP_STATION_INFORMATION_URL = (
    "https://gbfs.smartbike.com/antwerp/1.0/en/station_information.json"
)


class VeloAntwerpStationInformationService(StationInformationService):
    """Fetches Velo Antwerp station information from the public GBFS feed."""

    def __init__(
        self,
        url: str = VELO_ANTWERP_STATION_INFORMATION_URL,
        timeout: float = 10.0,
    ):
        self._url = url
        self._timeout = timeout

    def fetch_stations(self) -> StationCollection:
        with urllib.request.urlopen(self._url, timeout=self._timeout) as response:
            payload = json.load(response)

        stations = (
            Station.from_dict(station_data)
            for station_data in payload["data"]["stations"]
        )
        return StationCollection(stations)
