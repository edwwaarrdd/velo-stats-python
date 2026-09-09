import json
import urllib.request

from stations.models import Station

from .interfaces import RouteService
from .models import Coordinate, Route, StationRouteRecord, TravelMode

OSRM_BASE_URL = "https://routing.openstreetmap.de"

# The OSRM demo server at router.project-osrm.org only hosts the car profile and
# silently ignores the profile named in the URL, so every mode came back with car
# driving times. FOSSGIS runs a separate instance per profile instead, and the
# profile is selected by the host path rather than by the URL segment.
OSRM_PROFILE_PATHS = {
    TravelMode.BIKE: "routed-bike",
    TravelMode.FOOT: "routed-foot",
}


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
            f"{self._base_url}/{OSRM_PROFILE_PATHS[mode]}/route/v1/{mode.value}/"
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


class CachedStationRouteService:
    """Calculates routes between stations, caching results so a route between
    the same pair of stations and travel mode is only ever calculated once."""

    def __init__(self, route_service: RouteService):
        self._route_service = route_service

    def get_route(
        self, origin: Station, destination: Station, mode: TravelMode
    ) -> Route:
        cached = StationRouteRecord.objects.filter(
            origin_station_id=origin.station_id,
            destination_station_id=destination.station_id,
            mode=mode.value,
        ).first()
        if cached is not None:
            return cached.to_route()

        route = self._route_service.get_route(
            Coordinate(lat=origin.lat, lon=origin.lon),
            Coordinate(lat=destination.lat, lon=destination.lon),
            mode,
        )

        StationRouteRecord.objects.create(
            origin_station_id=origin.station_id,
            destination_station_id=destination.station_id,
            mode=mode.value,
            distance_meters=route.distance_meters,
            duration_seconds=route.duration_seconds,
        )
        return route
