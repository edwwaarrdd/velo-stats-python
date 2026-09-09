from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional


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

    def get(self, station_id: str) -> Optional[Station]:
        return self._stations_by_id.get(station_id)

    def all(self) -> list[Station]:
        return list(self._stations_by_id.values())
