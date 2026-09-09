from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from rides.models import RideRecord


def _make_ride(ride_id, distance_checked_at=None):
    return RideRecord.objects.create(
        ride_id=ride_id,
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
        distance_checked_at=distance_checked_at,
    )


class CheckRideDistancesCommandTests(TestCase):
    @patch("rides.management.commands.check_ride_distances.check_ride_distance")
    def test_dispatches_task_for_each_unchecked_ride(self, mock_task):
        _make_ride(1)
        _make_ride(2)
        _make_ride(3, distance_checked_at=timezone.now())

        call_command("check_ride_distances")

        self.assertEqual(mock_task.delay.call_count, 2)
        dispatched_ride_ids = {call.args[0] for call in mock_task.delay.call_args_list}
        self.assertEqual(dispatched_ride_ids, {1, 2})
