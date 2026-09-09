from dataclasses import dataclass
from enum import Enum


class TravelMode(str, Enum):
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
