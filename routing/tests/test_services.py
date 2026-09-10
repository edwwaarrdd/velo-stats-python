import json
import unittest
from unittest.mock import MagicMock, patch

from django.test import TestCase

from routing.models import Coordinate, Route, StationRouteRecord, TravelMode
from routing.services import CachedStationRouteService, OsrmRouteService
from stations.models import StationRecord

SAMPLE_PAYLOAD = {
    "code": "Ok",
    "routes": [
        {
            "distance": 5432.1,
            "duration": 987.6,
        }
    ],
}


def _fake_response(payload):
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


class OsrmRouteServiceTests(unittest.TestCase):
    def setUp(self):
        self.origin = Coordinate(lat=51.21782, lon=4.42065)
        self.destination = Coordinate(lat=51.22, lon=4.41)

    @patch("routing.services.urllib.request.urlopen")
    def test_get_route_parses_payload_into_route(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(SAMPLE_PAYLOAD)
        service = OsrmRouteService()

        route = service.get_route(self.origin, self.destination, TravelMode.FOOT)

        self.assertEqual(route.distance_meters, 5432.1)
        self.assertEqual(route.duration_seconds, 987.6)

    @patch("routing.services.urllib.request.urlopen")
    def test_get_route_requests_foot_profile_with_lon_lat_ordering(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(SAMPLE_PAYLOAD)
        service = OsrmRouteService(base_url="https://example.invalid", timeout=5.0)

        service.get_route(self.origin, self.destination, TravelMode.FOOT)

        mock_urlopen.assert_called_once_with(
            "https://example.invalid/routed-foot/route/v1/foot/"
            "4.42065,51.21782;4.41,51.22?overview=false",
            timeout=5.0,
        )

    @patch("routing.services.urllib.request.urlopen")
    def test_get_route_requests_bike_profile(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(SAMPLE_PAYLOAD)
        service = OsrmRouteService(base_url="https://example.invalid")

        service.get_route(self.origin, self.destination, TravelMode.BIKE)

        called_url = mock_urlopen.call_args[0][0]
        self.assertIn("/routed-bike/route/v1/bike/", called_url)

    @patch("routing.services.urllib.request.urlopen")
    def test_get_route_uses_a_separate_instance_per_travel_mode(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(SAMPLE_PAYLOAD)
        service = OsrmRouteService(base_url="https://example.invalid")

        service.get_route(self.origin, self.destination, TravelMode.BIKE)
        bike_url = mock_urlopen.call_args[0][0]

        service.get_route(self.origin, self.destination, TravelMode.FOOT)
        foot_url = mock_urlopen.call_args[0][0]

        self.assertIn("/routed-bike/", bike_url)
        self.assertIn("/routed-foot/", foot_url)

    @patch("routing.services.urllib.request.urlopen")
    def test_get_route_raises_when_osrm_reports_error(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(
            {"code": "NoRoute", "message": "Impossible route between points"}
        )
        service = OsrmRouteService()

        with self.assertRaises(RuntimeError):
            service.get_route(self.origin, self.destination, TravelMode.FOOT)


class CachedStationRouteServiceTests(TestCase):
    def setUp(self):
        self.origin_station_record = StationRecord.objects.create(
            station_id="001",
            name="001- Centraal Station",
            short_name="001",
            lat=51.21782,
            lon=4.42065,
            address="Koningin Astridplein",
            post_code="2018",
        )
        self.destination_station_record = StationRecord.objects.create(
            station_id="021",
            name="021- Driekoningen",
            short_name="021",
            lat=51.22,
            lon=4.41,
            address="Driekoningenstraat",
            post_code="2020",
        )
        self.origin = self.origin_station_record.to_station()
        self.destination = self.destination_station_record.to_station()
        self.inner_route_service = MagicMock()
        self.inner_route_service.get_route.return_value = Route(
            distance_meters=5432.1, duration_seconds=987.6
        )
        self.service = CachedStationRouteService(self.inner_route_service)

    def test_get_route_calculates_and_caches_when_not_cached(self):
        route = self.service.get_route(self.origin, self.destination, TravelMode.FOOT)

        self.assertEqual(route, Route(distance_meters=5432.1, duration_seconds=987.6))
        self.inner_route_service.get_route.assert_called_once_with(
            Coordinate(lat=self.origin.lat, lon=self.origin.lon),
            Coordinate(lat=self.destination.lat, lon=self.destination.lon),
            TravelMode.FOOT,
        )
        self.assertEqual(StationRouteRecord.objects.count(), 1)

    def test_get_route_returns_cached_route_without_recalculating(self):
        StationRouteRecord.objects.create(
            origin_station=self.origin_station_record,
            destination_station=self.destination_station_record,
            mode=TravelMode.FOOT.value,
            distance_meters=1111.0,
            duration_seconds=222.0,
        )

        route = self.service.get_route(self.origin, self.destination, TravelMode.FOOT)

        self.assertEqual(route, Route(distance_meters=1111.0, duration_seconds=222.0))
        self.inner_route_service.get_route.assert_not_called()
        self.assertEqual(StationRouteRecord.objects.count(), 1)

    def test_get_route_caches_separately_per_travel_mode(self):
        self.service.get_route(self.origin, self.destination, TravelMode.FOOT)
        self.service.get_route(self.origin, self.destination, TravelMode.BIKE)

        self.assertEqual(self.inner_route_service.get_route.call_count, 2)
        self.assertEqual(StationRouteRecord.objects.count(), 2)


if __name__ == "__main__":
    unittest.main()
