from dataclasses import dataclass
from datetime import UTC, datetime

from django.db import models
from django.utils import timezone

from rides.models import RideRecord


@dataclass(frozen=True)
class WeatherObservation:
    temperature_c: float
    apparent_temperature_c: float
    precipitation_mm: float
    rain_mm: float
    snowfall_cm: float
    cloud_cover_percent: float
    wind_speed_kmh: float
    wind_gusts_kmh: float
    wind_direction_degrees: float
    relative_humidity_percent: float
    weather_code: int
    observed_at: datetime

    @classmethod
    def from_open_meteo_hourly(cls, hourly: dict, index: int) -> "WeatherObservation":
        observed_at = datetime.fromisoformat(hourly["time"][index])
        if timezone.is_naive(observed_at):
            observed_at = timezone.make_aware(observed_at, UTC)

        return cls(
            temperature_c=hourly["temperature_2m"][index],
            apparent_temperature_c=hourly["apparent_temperature"][index],
            precipitation_mm=hourly["precipitation"][index],
            rain_mm=hourly["rain"][index],
            snowfall_cm=hourly["snowfall"][index],
            cloud_cover_percent=hourly["cloud_cover"][index],
            wind_speed_kmh=hourly["wind_speed_10m"][index],
            wind_gusts_kmh=hourly["wind_gusts_10m"][index],
            wind_direction_degrees=hourly["wind_direction_10m"][index],
            relative_humidity_percent=hourly["relative_humidity_2m"][index],
            weather_code=hourly["weather_code"][index],
            observed_at=observed_at,
        )


class WeatherRecord(models.Model):
    """Caches the biking-relevant weather observed for a ride's checkin time and origin station."""

    ride = models.OneToOneField(
        RideRecord, on_delete=models.CASCADE, related_name="weather"
    )
    temperature_c = models.FloatField()
    apparent_temperature_c = models.FloatField()
    precipitation_mm = models.FloatField()
    rain_mm = models.FloatField()
    snowfall_cm = models.FloatField()
    cloud_cover_percent = models.FloatField()
    wind_speed_kmh = models.FloatField()
    wind_gusts_kmh = models.FloatField()
    wind_direction_degrees = models.FloatField()
    relative_humidity_percent = models.FloatField()
    weather_code = models.IntegerField()
    observed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Weather for ride {self.ride_id} at {self.observed_at}"

    def to_observation(self) -> WeatherObservation:
        return WeatherObservation(
            temperature_c=self.temperature_c,
            apparent_temperature_c=self.apparent_temperature_c,
            precipitation_mm=self.precipitation_mm,
            rain_mm=self.rain_mm,
            snowfall_cm=self.snowfall_cm,
            cloud_cover_percent=self.cloud_cover_percent,
            wind_speed_kmh=self.wind_speed_kmh,
            wind_gusts_kmh=self.wind_gusts_kmh,
            wind_direction_degrees=self.wind_direction_degrees,
            relative_humidity_percent=self.relative_humidity_percent,
            weather_code=self.weather_code,
            observed_at=self.observed_at,
        )
