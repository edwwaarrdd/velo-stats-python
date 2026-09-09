import json
import urllib.request
from datetime import datetime

from routing.models import Coordinate
from rides.models import RideRecord

from .interfaces import WeatherService
from .models import WeatherObservation, WeatherRecord

OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

HOURLY_VARIABLES = ",".join(
    [
        "temperature_2m",
        "apparent_temperature",
        "precipitation",
        "rain",
        "snowfall",
        "cloud_cover",
        "wind_speed_10m",
        "wind_gusts_10m",
        "wind_direction_10m",
        "relative_humidity_2m",
        "weather_code",
    ]
)


class OpenMeteoWeatherService(WeatherService):
    """Fetches historical weather using the free Open-Meteo archive API."""

    def __init__(self, base_url: str = OPEN_METEO_ARCHIVE_URL, timeout: float = 10.0):
        self._base_url = base_url
        self._timeout = timeout

    def get_weather(self, location: Coordinate, at: datetime) -> WeatherObservation:
        date = at.date().isoformat()
        url = (
            f"{self._base_url}?latitude={location.lat}&longitude={location.lon}"
            f"&start_date={date}&end_date={date}"
            f"&hourly={HOURLY_VARIABLES}&timezone=UTC"
        )

        with urllib.request.urlopen(url, timeout=self._timeout) as response:
            payload = json.load(response)

        if "hourly" not in payload:
            raise RuntimeError(
                f"Open-Meteo request failed: {payload.get('reason', payload)}"
            )

        hourly = payload["hourly"]
        target_hour = at.replace(minute=0, second=0, microsecond=0).strftime(
            "%Y-%m-%dT%H:00"
        )
        index = hourly["time"].index(target_hour)

        return WeatherObservation.from_open_meteo_hourly(hourly, index)


class CachedRideWeatherService:
    """Fetches the weather for a ride's checkin time and origin station, caching
    results so the same ride's weather is only ever fetched once unless forced."""

    def __init__(self, weather_service: WeatherService):
        self._weather_service = weather_service

    def get_weather(
        self, ride: RideRecord, location: Coordinate, force: bool = False
    ) -> WeatherObservation:
        cached = WeatherRecord.objects.filter(ride_id=ride.ride_id).first()
        if cached is not None and not force:
            return cached.to_observation()

        observation = self._weather_service.get_weather(location, ride.checkin_time)

        WeatherRecord.objects.update_or_create(
            ride_id=ride.ride_id,
            defaults={
                "temperature_c": observation.temperature_c,
                "apparent_temperature_c": observation.apparent_temperature_c,
                "precipitation_mm": observation.precipitation_mm,
                "rain_mm": observation.rain_mm,
                "snowfall_cm": observation.snowfall_cm,
                "cloud_cover_percent": observation.cloud_cover_percent,
                "wind_speed_kmh": observation.wind_speed_kmh,
                "wind_gusts_kmh": observation.wind_gusts_kmh,
                "wind_direction_degrees": observation.wind_direction_degrees,
                "relative_humidity_percent": observation.relative_humidity_percent,
                "weather_code": observation.weather_code,
                "observed_at": observation.observed_at,
            },
        )
        return observation
