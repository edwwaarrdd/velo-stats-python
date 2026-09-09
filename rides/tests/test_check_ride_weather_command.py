from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from rides.models import RideRecord


def _make_ride(ride_id, weather_checked_at=None):
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
        weather_checked_at=weather_checked_at,
    )


class CheckRideWeatherCommandTests(TestCase):
    @patch("rides.management.commands.check_ride_weather.check_ride_weather")
    def test_dispatches_task_for_each_unchecked_ride(self, mock_task):
        _make_ride(1)
        _make_ride(2)
        _make_ride(3, weather_checked_at=timezone.now())

        call_command("check_ride_weather")

        self.assertEqual(mock_task.delay.call_count, 2)
        dispatched_ride_ids = {call.args[0] for call in mock_task.delay.call_args_list}
        self.assertEqual(dispatched_ride_ids, {1, 2})
        for call in mock_task.delay.call_args_list:
            self.assertEqual(call.kwargs, {"force": False})

    @patch("rides.management.commands.check_ride_weather.check_ride_weather")
    def test_force_dispatches_for_all_rides(self, mock_task):
        _make_ride(1)
        _make_ride(2, weather_checked_at=timezone.now())

        call_command("check_ride_weather", "--force")

        self.assertEqual(mock_task.delay.call_count, 2)
        dispatched_ride_ids = {call.args[0] for call in mock_task.delay.call_args_list}
        self.assertEqual(dispatched_ride_ids, {1, 2})
        for call in mock_task.delay.call_args_list:
            self.assertEqual(call.kwargs, {"force": True})
