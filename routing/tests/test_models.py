import unittest

from routing.models import Route, StationRouteRecord, TravelMode


class TravelModeTests(unittest.TestCase):
    def test_values_match_osrm_profile_names(self):
        self.assertEqual(TravelMode.FOOT.value, "foot")
        self.assertEqual(TravelMode.BIKE.value, "bike")


class RouteTests(unittest.TestCase):
    def test_from_osrm_route_parses_distance_and_duration(self):
        route = Route.from_osrm_route({"distance": 1234.5, "duration": 678.9})

        self.assertEqual(route.distance_meters, 1234.5)
        self.assertEqual(route.duration_seconds, 678.9)


class StationRouteRecordTests(unittest.TestCase):
    def test_to_route_returns_distance_and_duration(self):
        record = StationRouteRecord(
            mode=TravelMode.BIKE.value,
            distance_meters=987.6,
            duration_seconds=123.4,
        )

        route = record.to_route()

        self.assertEqual(route, Route(distance_meters=987.6, duration_seconds=123.4))


if __name__ == "__main__":
    unittest.main()
