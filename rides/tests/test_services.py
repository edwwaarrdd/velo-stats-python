import json
import tempfile
import unittest
from pathlib import Path

from rides.services import JsonFileRideService

SAMPLE_PAYLOAD = {
    "success": True,
    "status": 200,
    "data": {
        "CustomerRides": [
            {
                "id": 73147208,
                "accountId": 123,
                "status": "Completed",
                "duration": 8,
                "bikeNumber": "5097",
                "originStationCode": "021",
                "originStation": "021- Driekoningen",
                "originSlotId": "15",
                "checkoutTime": "2026-09-06 08:57:02",
                "destinationStationCode": "041",
                "destinationStation": "041- Van Eyck",
                "destinationSlotId": "23",
                "checkinTime": "2026-09-06 09:05:30",
            },
            {
                "id": 49023660,
                "accountId": 123,
                "status": "Completed",
                "duration": 6,
                "bikeNumber": "2281",
                "originStationCode": "076",
                "originStation": "076- Prekersplein",
                "originSlotId": "4",
                "checkoutTime": "2026-09-03 12:03:31",
                "destinationStationCode": "041",
                "destinationStation": "041- Van Eyck",
                "destinationSlotId": "26",
                "checkinTime": "2026-09-03 12:09:01",
            },
        ]
    },
    "error": None,
}


class JsonFileRideServiceTests(unittest.TestCase):
    def _write_payload(self, payload):
        tmp_dir = tempfile.mkdtemp()
        path = Path(tmp_dir) / "rides.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_fetch_rides_parses_payload_into_collection(self):
        path = self._write_payload(SAMPLE_PAYLOAD)
        service = JsonFileRideService(path)

        collection = service.fetch_rides()

        self.assertEqual(len(collection), 2)
        ride = collection.get(73147208)
        self.assertEqual(ride.origin_station, "021- Driekoningen")
        self.assertEqual(ride.duration, 8)

    def test_fetch_rides_returns_empty_collection_for_no_rides(self):
        path = self._write_payload({"data": {"CustomerRides": []}})
        service = JsonFileRideService(path)

        collection = service.fetch_rides()

        self.assertEqual(len(collection), 0)


if __name__ == "__main__":
    unittest.main()
