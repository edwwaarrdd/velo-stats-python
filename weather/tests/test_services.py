import json
import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from rides.models import RideRecord
from routing.models import Coordinate
from weather.models import WeatherObservation, WeatherRecord
from weather.services import CachedRideWeatherService, OpenMeteoWeatherService

SAMPLE_PAYLOAD = {
    "hourly": {
        "time": ["2024-01-15T13:00", "2024-01-15T14:00"],
        "temperature_2m": [5.1, 6.2],
        "apparent_temperature": [2.0, 3.1],
        "precipitation": [0.0, 0.5],
        "rain": [0.0, 0.5],
        "snowfall": [0.0, 0.0],
        "cloud_cover": [80, 90],
        "wind_speed_10m": [12.3, 14.4],
        "wind_gusts_10m": [20.1, 22.2],
        "wind_direction_10m": [270, 280],
        "relative_humidity_2m": [77, 80],
        "weather_code": [3, 61],
    }
}


def _fake_response(payload):
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


class OpenMeteoWeatherServiceTests(unittest.TestCase):
    def setUp(self):
        self.location = Coordinate(lat=51.21782, lon=4.42065)
        self.at = datetime(2024, 1, 15, 14, 30, tzinfo=UTC)

    @patch("weather.services.urllib.request.urlopen")
    def test_get_weather_parses_the_nearest_hour(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(SAMPLE_PAYLOAD)
        service = OpenMeteoWeatherService()

        observation = service.get_weather(self.location, self.at)

        self.assertEqual(observation.temperature_c, 6.2)
        self.assertEqual(observation.weather_code, 61)
        self.assertEqual(observation.observed_at, datetime(2024, 1, 15, 14, 0, tzinfo=UTC))

    @patch("weather.services.urllib.request.urlopen")
    def test_get_weather_requests_the_rides_date_and_coordinates(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response(SAMPLE_PAYLOAD)
        service = OpenMeteoWeatherService(base_url="https://example.invalid", timeout=5.0)

        service.get_weather(self.location, self.at)

        called_url = mock_urlopen.call_args[0][0]
        self.assertIn("latitude=51.21782", called_url)
        self.assertIn("longitude=4.42065", called_url)
        self.assertIn("start_date=2024-01-15", called_url)
        self.assertIn("end_date=2024-01-15", called_url)
        self.assertEqual(mock_urlopen.call_args[1], {"timeout": 5.0})

    @patch("weather.services.urllib.request.urlopen")
    def test_get_weather_raises_when_open_meteo_reports_error(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response({"reason": "Invalid coordinates"})
        service = OpenMeteoWeatherService()

        with self.assertRaises(RuntimeError):
            service.get_weather(self.location, self.at)


class CachedRideWeatherServiceTests(TestCase):
    def setUp(self):
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
            checkin_time=datetime(2024, 1, 15, 14, 30, tzinfo=UTC),
        )
        self.location = Coordinate(lat=51.21782, lon=4.42065)
        self.observation = WeatherObservation.from_open_meteo_hourly(SAMPLE_PAYLOAD["hourly"], 1)
        self.inner_weather_service = MagicMock()
        self.inner_weather_service.get_weather.return_value = self.observation
        self.service = CachedRideWeatherService(self.inner_weather_service)

    def test_get_weather_fetches_and_caches_when_not_cached(self):
        observation = self.service.get_weather(self.ride, self.location)

        self.assertEqual(observation, self.observation)
        self.inner_weather_service.get_weather.assert_called_once_with(
            self.location, self.ride.checkin_time
        )
        self.assertEqual(WeatherRecord.objects.count(), 1)

    def test_get_weather_returns_cached_observation_without_refetching(self):
        WeatherRecord.objects.create(
            ride=self.ride,
            temperature_c=1.0,
            apparent_temperature_c=1.0,
            precipitation_mm=0.0,
            rain_mm=0.0,
            snowfall_cm=0.0,
            cloud_cover_percent=0,
            wind_speed_kmh=0.0,
            wind_gusts_kmh=0.0,
            wind_direction_degrees=0,
            relative_humidity_percent=0,
            weather_code=0,
            observed_at=timezone.now(),
        )

        self.service.get_weather(self.ride, self.location)

        self.inner_weather_service.get_weather.assert_not_called()
        self.assertEqual(WeatherRecord.objects.count(), 1)

    def test_get_weather_refetches_and_overwrites_when_forced(self):
        WeatherRecord.objects.create(
            ride=self.ride,
            temperature_c=1.0,
            apparent_temperature_c=1.0,
            precipitation_mm=0.0,
            rain_mm=0.0,
            snowfall_cm=0.0,
            cloud_cover_percent=0,
            wind_speed_kmh=0.0,
            wind_gusts_kmh=0.0,
            wind_direction_degrees=0,
            relative_humidity_percent=0,
            weather_code=0,
            observed_at=timezone.now(),
        )

        observation = self.service.get_weather(self.ride, self.location, force=True)

        self.assertEqual(observation, self.observation)
        self.inner_weather_service.get_weather.assert_called_once()
        self.assertEqual(WeatherRecord.objects.count(), 1)
        self.assertEqual(WeatherRecord.objects.get().temperature_c, self.observation.temperature_c)


if __name__ == "__main__":
    unittest.main()
