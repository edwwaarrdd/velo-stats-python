from django.db.models import Avg, Count, Max, Min, OuterRef, QuerySet, Subquery, Sum
from django.http import JsonResponse

from routing.models import StationRouteRecord, TravelMode

from .models import RideRecord


def _round(value):
    return round(value, 2) if value is not None else None


def _with_distance(rides: QuerySet) -> QuerySet:
    distance_subquery = StationRouteRecord.objects.filter(
        origin_station_id=OuterRef("origin_station_code"),
        destination_station_id=OuterRef("destination_station_code"),
        mode=TravelMode.BIKE.value,
    ).values("distance_meters")[:1]

    return rides.annotate(distance_meters=Subquery(distance_subquery))


def ride_summary(request):
    rides = _with_distance(RideRecord.objects.all())

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


def _serialize_weather(ride: RideRecord):
    if not hasattr(ride, "weather"):
        return None

    weather = ride.weather
    return {
        "temperature_c": weather.temperature_c,
        "apparent_temperature_c": weather.apparent_temperature_c,
        "precipitation_mm": weather.precipitation_mm,
        "rain_mm": weather.rain_mm,
        "snowfall_cm": weather.snowfall_cm,
        "cloud_cover_percent": weather.cloud_cover_percent,
        "wind_speed_kmh": weather.wind_speed_kmh,
        "wind_gusts_kmh": weather.wind_gusts_kmh,
        "wind_direction_degrees": weather.wind_direction_degrees,
        "relative_humidity_percent": weather.relative_humidity_percent,
        "weather_code": weather.weather_code,
        "observed_at": weather.observed_at,
    }


def _speed_kmh(ride: RideRecord):
    if ride.distance_meters is None or not ride.duration:
        return None
    return _round((ride.distance_meters / 1000) / (ride.duration / 60))


def _serialize_ride(ride: RideRecord):
    return {
        "ride_id": ride.ride_id,
        "account_id": ride.account_id,
        "status": ride.status,
        "duration": ride.duration,
        "bike_number": ride.bike_number,
        "origin_station_code": ride.origin_station_code,
        "origin_station": ride.origin_station,
        "origin_slot_id": ride.origin_slot_id,
        "checkout_time": ride.checkout_time,
        "destination_station_code": ride.destination_station_code,
        "destination_station": ride.destination_station,
        "destination_slot_id": ride.destination_slot_id,
        "checkin_time": ride.checkin_time,
        "distance_meters": ride.distance_meters,
        "speed_kmh": _speed_kmh(ride),
        "weather": _serialize_weather(ride),
    }


def ride_list(request):
    rides = _with_distance(RideRecord.objects.select_related("weather")).order_by(
        "-checkout_time"
    )

    return JsonResponse({"results": [_serialize_ride(ride) for ride in rides]})
