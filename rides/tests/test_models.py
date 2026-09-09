import unittest
from datetime import datetime

from django.utils import timezone

from rides.models import Ride, RideCollection

RIDE_DATA = {
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
}


class RideFromDictTests(unittest.TestCase):
    def test_builds_ride_from_full_data(self):
        ride = Ride.from_dict(RIDE_DATA)

        self.assertEqual(ride.ride_id, 73147208)
        self.assertEqual(ride.account_id, 123)
        self.assertEqual(ride.status, "Completed")
        self.assertEqual(ride.duration, 8)
        self.assertEqual(ride.bike_number, "5097")
        self.assertEqual(ride.origin_station_code, "021")
        self.assertEqual(ride.destination_station, "041- Van Eyck")
        self.assertEqual(
            ride.checkout_time,
            timezone.make_aware(datetime(2026, 9, 6, 8, 57, 2)),
        )
        self.assertEqual(
            ride.checkin_time,
            timezone.make_aware(datetime(2026, 9, 6, 9, 5, 30)),
        )


class RideCollectionTests(unittest.TestCase):
    def setUp(self):
        self.ride_one = Ride.from_dict(RIDE_DATA)
        other_data = dict(RIDE_DATA, id=49023660)
        self.ride_two = Ride.from_dict(other_data)
        self.collection = RideCollection([self.ride_one, self.ride_two])

    def test_len(self):
        self.assertEqual(len(self.collection), 2)

    def test_iteration_yields_all_rides(self):
        self.assertEqual(
            {ride.ride_id for ride in self.collection},
            {73147208, 49023660},
        )

    def test_contains(self):
        self.assertIn(73147208, self.collection)
        self.assertNotIn(1, self.collection)

    def test_get_returns_ride_by_id(self):
        self.assertEqual(self.collection.get(73147208), self.ride_one)

    def test_get_returns_none_for_unknown_id(self):
        self.assertIsNone(self.collection.get(1))

    def test_all_returns_list_of_rides(self):
        self.assertEqual(
            sorted(r.ride_id for r in self.collection.all()),
            [49023660, 73147208],
        )

    def test_deduplicates_by_ride_id(self):
        collection = RideCollection([self.ride_one, self.ride_one])
        self.assertEqual(len(collection), 1)

    def test_empty_collection(self):
        self.assertEqual(len(RideCollection()), 0)


if __name__ == "__main__":
    unittest.main()
