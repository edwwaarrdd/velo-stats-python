from django.test import TestCase

from stations.models import StationRecord


class StationListViewTests(TestCase):
    def test_returns_all_stations_with_coordinates(self):
        StationRecord.objects.create(
            station_id="041",
            name="041- Van Eyck",
            short_name="041",
            lat=51.2189,
            lon=4.4131,
            address="",
            post_code="",
        )

        response = self.client.get("/stations/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "results": [
                    {
                        "station_id": "041",
                        "name": "041- Van Eyck",
                        "lat": 51.2189,
                        "lon": 4.4131,
                    }
                ]
            },
        )

    def test_returns_empty_results_when_no_stations(self):
        response = self.client.get("/stations/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": []})
