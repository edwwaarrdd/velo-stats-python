from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime

from django.db import models
from django.utils import timezone

RIDE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.strptime(value, RIDE_DATETIME_FORMAT)
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)
    return parsed


@dataclass(frozen=True)
class Ride:
    ride_id: int
    account_id: int
    status: str
    duration: int
    bike_number: str
    origin_station_code: str
    origin_station: str
    origin_slot_id: str
    checkout_time: datetime
    destination_station_code: str
    destination_station: str
    destination_slot_id: str
    checkin_time: datetime

    @classmethod
    def from_dict(cls, data: dict) -> "Ride":
        return cls(
            ride_id=data["id"],
            account_id=data["accountId"],
            status=data["status"],
            duration=data["duration"],
            bike_number=data["bikeNumber"],
            origin_station_code=data["originStationCode"],
            origin_station=data["originStation"],
            origin_slot_id=data["originSlotId"],
            checkout_time=_parse_datetime(data["checkoutTime"]),
            destination_station_code=data["destinationStationCode"],
            destination_station=data["destinationStation"],
            destination_slot_id=data["destinationSlotId"],
            checkin_time=_parse_datetime(data["checkinTime"]),
        )


class RideCollection:
    def __init__(self, rides: Iterable[Ride] = ()):
        self._rides_by_id = {ride.ride_id: ride for ride in rides}

    def __len__(self) -> int:
        return len(self._rides_by_id)

    def __iter__(self) -> Iterator[Ride]:
        return iter(self._rides_by_id.values())

    def __contains__(self, ride_id: int) -> bool:
        return ride_id in self._rides_by_id

    def get(self, ride_id: int) -> Ride | None:
        return self._rides_by_id.get(ride_id)

    def all(self) -> list[Ride]:
        return list(self._rides_by_id.values())


class RideRecord(models.Model):
    ride_id = models.BigIntegerField(primary_key=True)
    account_id = models.BigIntegerField()
    status = models.CharField(max_length=32)
    duration = models.IntegerField()
    bike_number = models.CharField(max_length=32)
    origin_station_code = models.CharField(max_length=32)
    origin_station = models.CharField(max_length=255)
    origin_slot_id = models.CharField(max_length=16)
    checkout_time = models.DateTimeField()
    destination_station_code = models.CharField(max_length=32)
    destination_station = models.CharField(max_length=255)
    destination_slot_id = models.CharField(max_length=16)
    checkin_time = models.DateTimeField()
    distance_checked_at = models.DateTimeField(null=True, blank=True)
    weather_checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.ride_id} - {self.origin_station} to {self.destination_station}"

    def to_ride(self) -> Ride:
        return Ride(
            ride_id=self.ride_id,
            account_id=self.account_id,
            status=self.status,
            duration=self.duration,
            bike_number=self.bike_number,
            origin_station_code=self.origin_station_code,
            origin_station=self.origin_station,
            origin_slot_id=self.origin_slot_id,
            checkout_time=self.checkout_time,
            destination_station_code=self.destination_station_code,
            destination_station=self.destination_station,
            destination_slot_id=self.destination_slot_id,
            checkin_time=self.checkin_time,
        )
