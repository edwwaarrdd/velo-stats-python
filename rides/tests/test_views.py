from django.test import TestCase
from django.utils import timezone

from rides.models import RideRecord
from routing.models import StationRouteRecord, TravelMode
from stations.models import StationRecord
from weather.models import WeatherRecord


def _make_station(station_id):
    return StationRecord.objects.create(
        station_id=station_id,
        name=station_id,
        short_name=station_id,
        lat=0,
        lon=0,
        address="",
        post_code="",
    )


def _make_ride(
    ride_id,
    duration,
    origin_station_code,
    destination_station_code,
    checkout_time=None,
):
    return RideRecord.objects.create(
        ride_id=ride_id,
        account_id=1,
        status="completed",
        duration=duration,
        bike_number="B1",
        origin_station_code=origin_station_code,
        origin_station="Origin",
        origin_slot_id="1",
        checkout_time=checkout_time or timezone.now(),
        destination_station_code=destination_station_code,
        destination_station="Destination",
        destination_slot_id="2",
        checkin_time=checkout_time or timezone.now(),
    )


class RideSummaryViewTests(TestCase):
    def test_returns_zeroed_summary_when_no_rides(self):
        response = self.client.get("/rides/summary")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "total_rides": 0,
                "total_duration": None,
                "average_duration": None,
                "longest_ride_duration": None,
                "shortest_ride_duration": None,
                "total_distance_meters": None,
                "average_distance_meters": None,
            },
        )

    def test_summarizes_duration_and_distance_across_rides(self):
        origin = _make_station("001")
        destination = _make_station("002")
        other_destination = _make_station("003")
        StationRouteRecord.objects.create(
            origin_station=origin,
            destination_station=destination,
            mode=TravelMode.BIKE.value,
            distance_meters=1000.0,
            duration_seconds=200.0,
        )
        StationRouteRecord.objects.create(
            origin_station=origin,
            destination_station=other_destination,
            mode=TravelMode.BIKE.value,
            distance_meters=3000.0,
            duration_seconds=400.0,
        )

        _make_ride(1, duration=5, origin_station_code="001", destination_station_code="002")
        _make_ride(2, duration=15, origin_station_code="001", destination_station_code="003")

        response = self.client.get("/rides/summary")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "total_rides": 2,
                "total_duration": 20,
                "average_duration": 10.0,
                "longest_ride_duration": 15,
                "shortest_ride_duration": 5,
                "total_distance_meters": 4000.0,
                "average_distance_meters": 2000.0,
            },
        )

    def test_excludes_rides_with_no_cached_route_from_distance_stats(self):
        _make_ride(1, duration=5, origin_station_code="001", destination_station_code="002")

        response = self.client.get("/rides/summary")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total_distance_meters"], None)
        self.assertEqual(body["average_distance_meters"], None)
        self.assertEqual(body["total_rides"], 1)


class RideListViewTests(TestCase):
    def test_returns_empty_results_when_no_rides(self):
        response = self.client.get("/rides/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": []})

    def test_includes_basic_info_distance_speed_and_weather(self):
        origin = _make_station("001")
        destination = _make_station("002")
        StationRouteRecord.objects.create(
            origin_station=origin,
            destination_station=destination,
            mode=TravelMode.BIKE.value,
            distance_meters=3000.0,
            duration_seconds=400.0,
        )
        ride = _make_ride(
            1, duration=15, origin_station_code="001", destination_station_code="002"
        )
        WeatherRecord.objects.create(
            ride=ride,
            temperature_c=18.5,
            apparent_temperature_c=17.0,
            precipitation_mm=0.0,
            rain_mm=0.0,
            snowfall_cm=0.0,
            cloud_cover_percent=40.0,
            wind_speed_kmh=12.0,
            wind_gusts_kmh=20.0,
            wind_direction_degrees=180.0,
            relative_humidity_percent=65.0,
            weather_code=1,
            observed_at=ride.checkin_time,
        )

        response = self.client.get("/rides/")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body["results"]), 1)
        result = body["results"][0]

        self.assertEqual(result["ride_id"], 1)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["duration"], 15)
        self.assertEqual(result["origin_station_code"], "001")
        self.assertEqual(result["destination_station_code"], "002")
        self.assertEqual(result["distance_meters"], 3000.0)
        # 3km in 15 minutes (0.25h) = 12 km/h
        self.assertEqual(result["speed_kmh"], 12.0)
        self.assertEqual(
            result["weather"],
            {
                "temperature_c": 18.5,
                "apparent_temperature_c": 17.0,
                "precipitation_mm": 0.0,
                "rain_mm": 0.0,
                "snowfall_cm": 0.0,
                "cloud_cover_percent": 40.0,
                "wind_speed_kmh": 12.0,
                "wind_gusts_kmh": 20.0,
                "wind_direction_degrees": 180.0,
                "relative_humidity_percent": 65.0,
                "weather_code": 1,
                "observed_at": result["weather"]["observed_at"],
            },
        )

    def test_returns_null_distance_speed_and_weather_when_unavailable(self):
        _make_ride(1, duration=10, origin_station_code="001", destination_station_code="002")

        response = self.client.get("/rides/")

        result = response.json()["results"][0]
        self.assertEqual(result["distance_meters"], None)
        self.assertEqual(result["speed_kmh"], None)
        self.assertEqual(result["weather"], None)

    def test_orders_rides_by_most_recent_checkout_first(self):
        older = timezone.now() - timezone.timedelta(days=1)
        newer = timezone.now()
        _make_ride(
            1, duration=5, origin_station_code="001", destination_station_code="002",
            checkout_time=older,
        )
        _make_ride(
            2, duration=5, origin_station_code="001", destination_station_code="002",
            checkout_time=newer,
        )

        response = self.client.get("/rides/")

        ride_ids = [result["ride_id"] for result in response.json()["results"]]
        self.assertEqual(ride_ids, [2, 1])
