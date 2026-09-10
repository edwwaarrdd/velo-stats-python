import unittest

from stations.models import Station, StationCollection

STATION_DATA = {
    "station_id": "001",
    "name": "001- Centraal Station - Astrid",
    "short_name": "001",
    "lat": 51.21782,
    "lon": 4.42065,
    "address": "Koningin Astridplein",
    "post_code": "2018",
    "rental_methods": ["KEY"],
    "capacity": 33,
}


class StationFromDictTests(unittest.TestCase):
    def test_builds_station_from_full_data(self):
        station = Station.from_dict(STATION_DATA)

        self.assertEqual(station.station_id, "001")
        self.assertEqual(station.name, "001- Centraal Station - Astrid")
        self.assertEqual(station.lat, 51.21782)
        self.assertEqual(station.lon, 4.42065)
        self.assertEqual(station.rental_methods, ["KEY"])
        self.assertEqual(station.capacity, 33)

    def test_defaults_missing_optional_fields(self):
        data = dict(STATION_DATA)
        del data["rental_methods"]
        del data["capacity"]

        station = Station.from_dict(data)

        self.assertEqual(station.rental_methods, [])
        self.assertEqual(station.capacity, 0)


class StationCollectionTests(unittest.TestCase):
    def setUp(self):
        self.station_one = Station.from_dict(STATION_DATA)
        other_data = dict(STATION_DATA, station_id="002", short_name="002")
        self.station_two = Station.from_dict(other_data)
        self.collection = StationCollection([self.station_one, self.station_two])

    def test_len(self):
        self.assertEqual(len(self.collection), 2)

    def test_iteration_yields_all_stations(self):
        self.assertEqual(
            {station.station_id for station in self.collection},
            {"001", "002"},
        )

    def test_contains(self):
        self.assertIn("001", self.collection)
        self.assertNotIn("999", self.collection)

    def test_get_returns_station_by_id(self):
        self.assertEqual(self.collection.get("001"), self.station_one)

    def test_get_returns_none_for_unknown_id(self):
        self.assertIsNone(self.collection.get("999"))

    def test_all_returns_list_of_stations(self):
        self.assertEqual(sorted(s.station_id for s in self.collection.all()), ["001", "002"])

    def test_deduplicates_by_station_id(self):
        collection = StationCollection([self.station_one, self.station_one])
        self.assertEqual(len(collection), 1)

    def test_empty_collection(self):
        self.assertEqual(len(StationCollection()), 0)


if __name__ == "__main__":
    unittest.main()
