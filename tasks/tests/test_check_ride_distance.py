from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from rides.models import RideRecord
from routing.models import Route, StationRouteRecord, TravelMode
from stations.models import StationRecord
from tasks.tasks import check_ride_distance


class CheckRideDistanceTests(TestCase):
    def setUp(self):
        self.origin_station = StationRecord.objects.create(
            station_id="001",
            name="001 - Centraal Station",
            short_name="001",
            lat=51.21782,
            lon=4.42065,
            address="Koningin Astridplein",
            post_code="2018",
        )
        self.destination_station = StationRecord.objects.create(
            station_id="021",
            name="021 - Driekoningen",
            short_name="021",
            lat=51.22,
            lon=4.41,
            address="Driekoningenstraat",
            post_code="2020",
        )
        self.ride = RideRecord.objects.create(
            ride_id=1,
            account_id=1,
            status="completed",
            duration=600,
            bike_number="B1",
            origin_station_code="001",
            origin_station="001 - Centraal Station",
            origin_slot_id="1",
            checkout_time=timezone.now(),
            destination_station_code="021",
            destination_station="021 - Driekoningen",
            destination_slot_id="2",
            checkin_time=timezone.now(),
        )

    @patch("tasks.tasks.OsrmRouteService")
    def test_marks_ride_checked_and_uses_bike_mode(self, mock_osrm_cls):
        mock_osrm = MagicMock()
        mock_osrm.get_route.return_value = Route(distance_meters=1234.0, duration_seconds=100.0)
        mock_osrm_cls.return_value = mock_osrm

        check_ride_distance.apply(args=[self.ride.ride_id])

        self.ride.refresh_from_db()
        self.assertIsNotNone(self.ride.distance_checked_at)
        mock_osrm.get_route.assert_called_once()
        self.assertEqual(mock_osrm.get_route.call_args[0][2], TravelMode.BIKE)
        self.assertEqual(StationRouteRecord.objects.count(), 1)

    @patch("tasks.tasks.OsrmRouteService")
    def test_reuses_cached_station_route_without_calling_api(self, mock_osrm_cls):
        StationRouteRecord.objects.create(
            origin_station=self.origin_station,
            destination_station=self.destination_station,
            mode=TravelMode.BIKE.value,
            distance_meters=999.0,
            duration_seconds=50.0,
        )
        mock_osrm = MagicMock()
        mock_osrm_cls.return_value = mock_osrm

        check_ride_distance.apply(args=[self.ride.ride_id])

        self.ride.refresh_from_db()
        self.assertIsNotNone(self.ride.distance_checked_at)
        mock_osrm.get_route.assert_not_called()

    @patch("tasks.tasks.OsrmRouteService")
    def test_skips_already_checked_ride(self, mock_osrm_cls):
        mock_osrm = MagicMock()
        mock_osrm_cls.return_value = mock_osrm
        self.ride.distance_checked_at = timezone.now()
        self.ride.save(update_fields=["distance_checked_at"])

        check_ride_distance.apply(args=[self.ride.ride_id])

        mock_osrm.get_route.assert_not_called()

    @patch("tasks.tasks.OsrmRouteService")
    def test_logs_and_skips_when_station_missing(self, mock_osrm_cls):
        self.ride.origin_station_code = "unknown"
        self.ride.save(update_fields=["origin_station_code"])
        mock_osrm = MagicMock()
        mock_osrm_cls.return_value = mock_osrm

        with self.assertLogs("tasks", level="ERROR"):
            check_ride_distance.apply(args=[self.ride.ride_id])

        self.ride.refresh_from_db()
        self.assertIsNone(self.ride.distance_checked_at)
        mock_osrm.get_route.assert_not_called()
