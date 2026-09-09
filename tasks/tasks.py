import logging

from celery import shared_task
from django.utils import timezone

from routing.models import TravelMode
from routing.services import CachedStationRouteService, OsrmRouteService
from rides.models import RideRecord
from stations.models import StationRecord

logger = logging.getLogger("tasks")


@shared_task
def log_test_message(message: str) -> None:
    logger.info("Test task received: %s", message)


@shared_task
def check_ride_distance(ride_id: int) -> None:
    ride = RideRecord.objects.get(ride_id=ride_id)
    if ride.distance_checked_at is not None:
        return

    try:
        origin = StationRecord.objects.get(station_id=ride.origin_station_code)
        destination = StationRecord.objects.get(
            station_id=ride.destination_station_code
        )
    except StationRecord.DoesNotExist:
        logger.error(
            "Cannot check distance for ride %s: unknown station code(s) %s / %s",
            ride_id,
            ride.origin_station_code,
            ride.destination_station_code,
        )
        return

    service = CachedStationRouteService(OsrmRouteService())
    service.get_route(origin.to_station(), destination.to_station(), TravelMode.BIKE)

    ride.distance_checked_at = timezone.now()
    ride.save(update_fields=["distance_checked_at"])
