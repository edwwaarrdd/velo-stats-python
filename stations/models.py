from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

from django.db import models


@dataclass(frozen=True)
class Station:
    station_id: str
    name: str
    short_name: str
    lat: float
    lon: float
    address: str
    post_code: str
    rental_methods: list[str] = field(default_factory=list)
    capacity: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "Station":
        return cls(
            station_id=data["station_id"],
            name=data["name"],
            short_name=data["short_name"],
            lat=data["lat"],
            lon=data["lon"],
            address=data["address"],
            post_code=data["post_code"],
            rental_methods=list(data.get("rental_methods", [])),
            capacity=data.get("capacity", 0),
        )


class StationCollection:
    """An accessible, queryable collection of Station objects, keyed by station_id."""

    def __init__(self, stations: Iterable[Station] = ()):
        self._stations_by_id = {station.station_id: station for station in stations}

    def __len__(self) -> int:
        return len(self._stations_by_id)

    def __iter__(self) -> Iterator[Station]:
        return iter(self._stations_by_id.values())

    def __contains__(self, station_id: str) -> bool:
        return station_id in self._stations_by_id

    def get(self, station_id: str) -> Station | None:
        return self._stations_by_id.get(station_id)

    def all(self) -> list[Station]:
        return list(self._stations_by_id.values())


class StationRecord(models.Model):
    """Database entity persisting a Station."""

    station_id = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=32)
    lat = models.FloatField()
    lon = models.FloatField()
    address = models.CharField(max_length=255)
    post_code = models.CharField(max_length=16)
    rental_methods = models.JSONField(default=list)
    capacity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.station_id} - {self.name}"

    def to_station(self) -> Station:
        return Station(
            station_id=self.station_id,
            name=self.name,
            short_name=self.short_name,
            lat=self.lat,
            lon=self.lon,
            address=self.address,
            post_code=self.post_code,
            rental_methods=list(self.rental_methods),
            capacity=self.capacity,
        )
