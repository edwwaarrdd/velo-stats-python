from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from rides.models import RideRecord
from routing.models import Coordinate
from stations.models import StationRecord
from tasks.tasks import check_ride_weather
from weather.models import WeatherObservation, WeatherRecord


class CheckRideWeatherTests(TestCase):
    def setUp(self):
        self.origin_station = StationRecord.objects.create(
            station_id="001",
            name="001 - Centraal Station",
            short_name="001",
            lat=51.21782,
            lon=4.42065,
            address="Koningin Astridplein",
            post_code="2018",
        )
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
            checkin_time=timezone.now(),
        )
        self.observation = WeatherObservation(
            temperature_c=6.2,
            apparent_temperature_c=3.1,
            precipitation_mm=0.5,
            rain_mm=0.5,
            snowfall_cm=0.0,
            cloud_cover_percent=90,
            wind_speed_kmh=14.4,
            wind_gusts_kmh=22.2,
            wind_direction_degrees=280,
            relative_humidity_percent=80,
            weather_code=61,
            observed_at=timezone.now(),
        )

    @patch("tasks.tasks.OpenMeteoWeatherService")
    def test_marks_ride_checked_and_uses_origin_coordinates(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service.get_weather.return_value = self.observation
        mock_service_cls.return_value = mock_service

        check_ride_weather.apply(args=[self.ride.ride_id])

        self.ride.refresh_from_db()
        self.assertIsNotNone(self.ride.weather_checked_at)
        mock_service.get_weather.assert_called_once_with(
            Coordinate(lat=51.21782, lon=4.42065), self.ride.checkin_time
        )
        self.assertEqual(WeatherRecord.objects.count(), 1)

    @patch("tasks.tasks.OpenMeteoWeatherService")
    def test_reuses_cached_weather_without_calling_api(self, mock_service_cls):
        WeatherRecord.objects.create(
            ride=self.ride,
            temperature_c=self.observation.temperature_c,
            apparent_temperature_c=self.observation.apparent_temperature_c,
            precipitation_mm=self.observation.precipitation_mm,
            rain_mm=self.observation.rain_mm,
            snowfall_cm=self.observation.snowfall_cm,
            cloud_cover_percent=self.observation.cloud_cover_percent,
            wind_speed_kmh=self.observation.wind_speed_kmh,
            wind_gusts_kmh=self.observation.wind_gusts_kmh,
            wind_direction_degrees=self.observation.wind_direction_degrees,
            relative_humidity_percent=self.observation.relative_humidity_percent,
            weather_code=self.observation.weather_code,
            observed_at=self.observation.observed_at,
        )
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service

        check_ride_weather.apply(args=[self.ride.ride_id])

        self.ride.refresh_from_db()
        self.assertIsNotNone(self.ride.weather_checked_at)
        mock_service.get_weather.assert_not_called()

    @patch("tasks.tasks.OpenMeteoWeatherService")
    def test_skips_already_checked_ride(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        self.ride.weather_checked_at = timezone.now()
        self.ride.save(update_fields=["weather_checked_at"])

        check_ride_weather.apply(args=[self.ride.ride_id])

        mock_service.get_weather.assert_not_called()

    @patch("tasks.tasks.OpenMeteoWeatherService")
    def test_force_refetches_already_checked_ride(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service.get_weather.return_value = self.observation
        mock_service_cls.return_value = mock_service
        self.ride.weather_checked_at = timezone.now()
        self.ride.save(update_fields=["weather_checked_at"])

        check_ride_weather.apply(args=[self.ride.ride_id], kwargs={"force": True})

        mock_service.get_weather.assert_called_once()

    @patch("tasks.tasks.OpenMeteoWeatherService")
    def test_logs_and_skips_when_origin_station_missing(self, mock_service_cls):
        self.ride.origin_station_code = "unknown"
        self.ride.save(update_fields=["origin_station_code"])
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service

        with self.assertLogs("tasks", level="ERROR"):
            check_ride_weather.apply(args=[self.ride.ride_id])

        self.ride.refresh_from_db()
        self.assertIsNone(self.ride.weather_checked_at)
        mock_service.get_weather.assert_not_called()
