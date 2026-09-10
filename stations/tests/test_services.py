import json
import unittest
from unittest.mock import MagicMock, patch

from stations.services import VeloAntwerpStationInformationService

SAMPLE_PAYLOAD = {
    "last_updated": 1788939141,
    "ttl": 60,
    "version": "2.0",
    "data": {
        "stations": [
            {
                "station_id": "001",
                "name": "001- Centraal Station - Astrid",
                "short_name": "001",
                "lat": 51.21782,
                "lon": 4.42065,
                "address": "Koningin Astridplein",
                "post_code": "2018",
                "rental_methods": ["KEY"],
                "capacity": 33,
            },
            {
                "station_id": "002",
                "name": "002- Centraal Station - Astrid 2",
                "short_name": "002",
                "lat": 51.21756,
                "lon": 4.42073,
                "address": "Koningin Astridplein  tov st1",
                "post_code": "2018",
                "rental_methods": ["KEY"],
                "capacity": 36,
            },
        ]
    },
}


def _fake_response(payload):
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


class VeloAntwerpStationInformationServiceTests(unittest.TestCase):
    @patch("stations.services.urllib.request.urlopen")
    def test_fetch_stations_parses_payload_into_collection(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(SAMPLE_PAYLOAD)
        service = VeloAntwerpStationInformationService()

        collection = service.fetch_stations()

        self.assertEqual(len(collection), 2)
        station = collection.get("001")
        self.assertEqual(station.name, "001- Centraal Station - Astrid")
        self.assertEqual(station.capacity, 33)

    @patch("stations.services.urllib.request.urlopen")
    def test_fetch_stations_requests_configured_url_and_timeout(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(SAMPLE_PAYLOAD)
        service = VeloAntwerpStationInformationService(
            url="https://example.invalid/stations.json", timeout=5.0
        )

        service.fetch_stations()

        mock_urlopen.assert_called_once_with("https://example.invalid/stations.json", timeout=5.0)

    @patch("stations.services.urllib.request.urlopen")
    def test_fetch_stations_returns_empty_collection_for_no_stations(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response({"data": {"stations": []}})
        service = VeloAntwerpStationInformationService()

        collection = service.fetch_stations()

        self.assertEqual(len(collection), 0)


if __name__ == "__main__":
    unittest.main()
