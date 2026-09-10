from dataclasses import dataclass
from enum import StrEnum

from django.db import models

from stations.models import StationRecord


class TravelMode(StrEnum):
    FOOT = "foot"
    BIKE = "bike"


@dataclass(frozen=True)
class Coordinate:
    lat: float
    lon: float


@dataclass(frozen=True)
class Route:
    distance_meters: float
    duration_seconds: float

    @classmethod
    def from_osrm_route(cls, data: dict) -> "Route":
        return cls(
            distance_meters=data["distance"],
            duration_seconds=data["duration"],
        )


class StationRouteRecord(models.Model):
    """Caches the calculated Route between two stations for a given travel mode."""

    origin_station = models.ForeignKey(
        StationRecord, on_delete=models.CASCADE, related_name="routes_from"
    )
    destination_station = models.ForeignKey(
        StationRecord, on_delete=models.CASCADE, related_name="routes_to"
    )
    mode = models.CharField(max_length=8, choices=[(mode.value, mode.value) for mode in TravelMode])
    distance_meters = models.FloatField()
    duration_seconds = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["origin_station", "destination_station", "mode"],
                name="unique_station_route_per_mode",
            )
        ]

    def __str__(self) -> str:
        return f"{self.origin_station_id} -> {self.destination_station_id} ({self.mode})"

    def to_route(self) -> Route:
        return Route(
            distance_meters=self.distance_meters,
            duration_seconds=self.duration_seconds,
        )
