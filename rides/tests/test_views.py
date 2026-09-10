import datetime

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
    checkin_time=None,
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
        checkin_time=checkin_time
        or (checkout_time or timezone.now()) + datetime.timedelta(minutes=duration),
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
        ride = _make_ride(1, duration=15, origin_station_code="001", destination_station_code="002")
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
        self.assertEqual(result["speed_kmh"], 12.0)
        self.assertEqual(result["expected_duration_seconds"], 400.0)
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
        self.assertEqual(result["expected_duration_seconds"], None)
        self.assertEqual(result["duration_vs_expected_seconds"], None)
        self.assertEqual(result["weather"], None)

    def test_bases_speed_on_the_exact_seconds_not_the_rounded_duration(self):
        origin = _make_station("001")
        destination = _make_station("002")
        StationRouteRecord.objects.create(
            origin_station=origin,
            destination_station=destination,
            mode=TravelMode.BIKE.value,
            distance_meters=1742.4,
            duration_seconds=248.1,
        )
        checkout_time = timezone.now()
        _make_ride(
            1,
            # The stored duration truncates 4m29s to 4 whole minutes, which would
            # overstate the speed as 26.14 km/h.
            duration=4,
            origin_station_code="001",
            destination_station_code="002",
            checkout_time=checkout_time,
            checkin_time=checkout_time + datetime.timedelta(seconds=269),
        )

        response = self.client.get("/rides/")

        self.assertEqual(response.json()["results"][0]["speed_kmh"], 23.32)

    def test_compares_actual_ride_time_against_the_expected_route_duration(self):
        origin = _make_station("001")
        destination = _make_station("002")
        StationRouteRecord.objects.create(
            origin_station=origin,
            destination_station=destination,
            mode=TravelMode.BIKE.value,
            distance_meters=3000.0,
            duration_seconds=400.0,
        )
        checkout_time = timezone.now()
        _make_ride(
            1,
            duration=5,
            origin_station_code="001",
            destination_station_code="002",
            checkout_time=checkout_time,
            checkin_time=checkout_time + datetime.timedelta(seconds=300),
        )

        response = self.client.get("/rides/")

        result = response.json()["results"][0]
        self.assertEqual(result["expected_duration_seconds"], 400.0)
        self.assertEqual(result["actual_duration_seconds"], 300.0)
        self.assertEqual(result["duration_vs_expected_seconds"], -100.0)

    def test_reports_a_positive_delta_when_slower_than_expected(self):
        origin = _make_station("001")
        destination = _make_station("002")
        StationRouteRecord.objects.create(
            origin_station=origin,
            destination_station=destination,
            mode=TravelMode.BIKE.value,
            distance_meters=3000.0,
            duration_seconds=400.0,
        )
        checkout_time = timezone.now()
        _make_ride(
            1,
            duration=10,
            origin_station_code="001",
            destination_station_code="002",
            checkout_time=checkout_time,
            checkin_time=checkout_time + datetime.timedelta(seconds=610),
        )

        response = self.client.get("/rides/")

        result = response.json()["results"][0]
        self.assertEqual(result["duration_vs_expected_seconds"], 210.0)

    def test_orders_rides_by_most_recent_checkout_first(self):
        older = timezone.now() - timezone.timedelta(days=1)
        newer = timezone.now()
        _make_ride(
            1,
            duration=5,
            origin_station_code="001",
            destination_station_code="002",
            checkout_time=older,
        )
        _make_ride(
            2,
            duration=5,
            origin_station_code="001",
            destination_station_code="002",
            checkout_time=newer,
        )

        response = self.client.get("/rides/")

        ride_ids = [result["ride_id"] for result in response.json()["results"]]
        self.assertEqual(ride_ids, [2, 1])


class RideCostViewTests(TestCase):
    def test_returns_nulls_when_no_rides(self):
        response = self.client.get("/rides/cost")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "total_rides": 0,
                "first_ride_date": None,
                "last_ride_date": None,
                "date_range_days": None,
                "subscription_price_eur": 58.0,
                "prorated_subscription_price_eur": None,
                "cost_per_ride_eur": None,
                "day_pass_equivalent_eur": None,
                "week_pass_equivalent_eur": None,
                "money_saved_vs_day_passes_eur": None,
                "money_saved_vs_week_passes_eur": None,
            },
        )

    def test_calculates_prorated_cost_and_savings_across_date_range(self):
        # First two rides share a day (and ISO week), the third ride is nine
        # days later, in a different ISO week: 10-day range, 2 distinct ride
        # days, 2 distinct ISO weeks.
        _make_ride(
            1,
            duration=5,
            origin_station_code="001",
            destination_station_code="002",
            checkout_time=timezone.make_aware(datetime.datetime(2026, 1, 1, 12, 0, 0)),
        )
        _make_ride(
            2,
            duration=5,
            origin_station_code="001",
            destination_station_code="002",
            checkout_time=timezone.make_aware(datetime.datetime(2026, 1, 1, 18, 0, 0)),
        )
        _make_ride(
            3,
            duration=5,
            origin_station_code="001",
            destination_station_code="002",
            checkout_time=timezone.make_aware(datetime.datetime(2026, 1, 10, 12, 0, 0)),
        )

        response = self.client.get("/rides/cost")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "total_rides": 3,
                "first_ride_date": "2026-01-01",
                "last_ride_date": "2026-01-10",
                "date_range_days": 10,
                "subscription_price_eur": 58.0,
                "prorated_subscription_price_eur": 1.59,
                "cost_per_ride_eur": 0.53,
                "day_pass_equivalent_eur": 10.0,
                "week_pass_equivalent_eur": 24.0,
                "money_saved_vs_day_passes_eur": 8.41,
                "money_saved_vs_week_passes_eur": 22.41,
            },
        )

    def test_treats_single_ride_as_single_day_range(self):
        _make_ride(
            1,
            duration=5,
            origin_station_code="001",
            destination_station_code="002",
            checkout_time=timezone.make_aware(datetime.datetime(2026, 3, 1, 12, 0, 0)),
        )

        response = self.client.get("/rides/cost")

        body = response.json()
        self.assertEqual(body["date_range_days"], 1)
        self.assertEqual(body["first_ride_date"], "2026-03-01")
        self.assertEqual(body["last_ride_date"], "2026-03-01")
