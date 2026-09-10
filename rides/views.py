from django.db.models import Avg, Count, Max, Min, OuterRef, QuerySet, Subquery, Sum
from django.http import JsonResponse

from routing.models import StationRouteRecord, TravelMode

from .models import RideRecord

ANNUAL_SUBSCRIPTION_PRICE_EUR = 58.0
DAYS_PER_YEAR = 365
DAY_PASS_PRICE_EUR = 5.0
WEEK_PASS_PRICE_EUR = 12.0


def _round(value):
    return round(value, 2) if value is not None else None


def _with_route(rides: QuerySet) -> QuerySet:
    routes = StationRouteRecord.objects.filter(
        origin_station_id=OuterRef("origin_station_code"),
        destination_station_id=OuterRef("destination_station_code"),
        mode=TravelMode.BIKE.value,
    )

    return rides.annotate(
        distance_meters=Subquery(routes.values("distance_meters")[:1]),
        expected_duration_seconds=Subquery(routes.values("duration_seconds")[:1]),
    )


def ride_summary(request):
    rides = _with_route(RideRecord.objects.all())

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


def _actual_duration_seconds(ride: RideRecord):
    """Ride time to the second, since `duration` is only stored in whole minutes."""
    if ride.checkin_time is None or ride.checkout_time is None:
        return None
    return _round((ride.checkin_time - ride.checkout_time).total_seconds())


def _speed_kmh(ride: RideRecord):
    seconds = _actual_duration_seconds(ride)
    if ride.distance_meters is None or not seconds:
        return None
    return _round((ride.distance_meters / 1000) / (seconds / 3600))


def _duration_vs_expected_seconds(ride: RideRecord):
    """Actual minus expected: negative means faster than the router predicted."""
    actual = _actual_duration_seconds(ride)
    if actual is None or ride.expected_duration_seconds is None:
        return None
    return _round(actual - ride.expected_duration_seconds)


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
        "expected_duration_seconds": _round(ride.expected_duration_seconds),
        "actual_duration_seconds": _actual_duration_seconds(ride),
        "duration_vs_expected_seconds": _duration_vs_expected_seconds(ride),
        "weather": _serialize_weather(ride),
    }


def ride_list(request):
    rides = _with_route(RideRecord.objects.select_related("weather")).order_by("-checkout_time")

    return JsonResponse({"results": [_serialize_ride(ride) for ride in rides]})


def ride_cost(request):
    total_rides = RideRecord.objects.count()

    if total_rides == 0:
        return JsonResponse(
            {
                "total_rides": 0,
                "first_ride_date": None,
                "last_ride_date": None,
                "date_range_days": None,
                "subscription_price_eur": ANNUAL_SUBSCRIPTION_PRICE_EUR,
                "prorated_subscription_price_eur": None,
                "cost_per_ride_eur": None,
                "day_pass_equivalent_eur": None,
                "week_pass_equivalent_eur": None,
                "money_saved_vs_day_passes_eur": None,
                "money_saved_vs_week_passes_eur": None,
            }
        )

    checkout_times = RideRecord.objects.values_list("checkout_time", flat=True)
    first_ride_date = min(checkout_times).date()
    last_ride_date = max(checkout_times).date()
    date_range_days = (last_ride_date - first_ride_date).days + 1

    prorated_subscription_price = _round(
        ANNUAL_SUBSCRIPTION_PRICE_EUR * date_range_days / DAYS_PER_YEAR
    )
    cost_per_ride = _round(prorated_subscription_price / total_rides)

    ride_days = {checkout_time.date() for checkout_time in checkout_times}
    ride_weeks = {checkout_time.date().isocalendar()[:2] for checkout_time in checkout_times}

    day_pass_equivalent = _round(len(ride_days) * DAY_PASS_PRICE_EUR)
    week_pass_equivalent = _round(len(ride_weeks) * WEEK_PASS_PRICE_EUR)

    return JsonResponse(
        {
            "total_rides": total_rides,
            "first_ride_date": first_ride_date,
            "last_ride_date": last_ride_date,
            "date_range_days": date_range_days,
            "subscription_price_eur": ANNUAL_SUBSCRIPTION_PRICE_EUR,
            "prorated_subscription_price_eur": prorated_subscription_price,
            "cost_per_ride_eur": cost_per_ride,
            "day_pass_equivalent_eur": day_pass_equivalent,
            "week_pass_equivalent_eur": week_pass_equivalent,
            "money_saved_vs_day_passes_eur": _round(
                day_pass_equivalent - prorated_subscription_price
            ),
            "money_saved_vs_week_passes_eur": _round(
                week_pass_equivalent - prorated_subscription_price
            ),
        }
    )
