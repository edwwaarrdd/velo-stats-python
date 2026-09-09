from django.db.models import Avg, Count, Max, Min, OuterRef, Subquery, Sum
from django.http import JsonResponse

from routing.models import StationRouteRecord, TravelMode

from .models import RideRecord


def _round(value):
    return round(value, 2) if value is not None else None


def ride_summary(request):
    distance_subquery = StationRouteRecord.objects.filter(
        origin_station_id=OuterRef("origin_station_code"),
        destination_station_id=OuterRef("destination_station_code"),
        mode=TravelMode.BIKE.value,
    ).values("distance_meters")[:1]

    rides = RideRecord.objects.annotate(
        distance_meters=Subquery(distance_subquery)
    )

    stats = rides.aggregate(
        total_rides=Count("ride_id"),
        total_duration=Sum("duration"),
        average_duration=Avg("duration"),
        longest_ride_duration=Max("duration"),
        shortest_ride_duration=Min("duration"),
        total_distance_meters=Sum("distance_meters"),
        average_distance_meters=Avg("distance_meters"),
    )

    stats["average_duration"] = _round(stats["average_duration"])
    stats["average_distance_meters"] = _round(stats["average_distance_meters"])

    return JsonResponse(stats)
