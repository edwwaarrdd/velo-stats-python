from django.test import TestCase
from django.utils import timezone

from rides.models import RideRecord
from routing.models import StationRouteRecord, TravelMode
from stations.models import StationRecord


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


def _make_ride(ride_id, duration, origin_station_code, destination_station_code):
    return RideRecord.objects.create(
        ride_id=ride_id,
        account_id=1,
        status="completed",
        duration=duration,
        bike_number="B1",
        origin_station_code=origin_station_code,
        origin_station="Origin",
        origin_slot_id="1",
        checkout_time=timezone.now(),
        destination_station_code=destination_station_code,
        destination_station="Destination",
        destination_slot_id="2",
        checkin_time=timezone.now(),
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
