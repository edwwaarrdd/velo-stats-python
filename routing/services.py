import json
import urllib.request

from .interfaces import RouteService
from .models import Coordinate, Route, TravelMode

OSRM_BASE_URL = "https://router.project-osrm.org"


class OsrmRouteService(RouteService):
    """Calculates routes using the public OSRM routing API."""

    def __init__(self, base_url: str = OSRM_BASE_URL, timeout: float = 10.0):
        self._base_url = base_url
        self._timeout = timeout

    def get_route(
        self, origin: Coordinate, destination: Coordinate, mode: TravelMode
    ) -> Route:
        # OSRM expects coordinates as "lon,lat", not "lat,lon".
        url = (
            f"{self._base_url}/route/v1/{mode.value}/"
            f"{origin.lon},{origin.lat};{destination.lon},{destination.lat}"
            f"?overview=false"
        )

        with urllib.request.urlopen(url, timeout=self._timeout) as response:
            payload = json.load(response)

        if payload.get("code") != "Ok":
            raise RuntimeError(
                f"OSRM request failed: {payload.get('message', payload.get('code'))}"
            )

        return Route.from_osrm_route(payload["routes"][0])
