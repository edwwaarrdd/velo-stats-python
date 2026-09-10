import unittest
from datetime import UTC, datetime

from weather.models import WeatherObservation, WeatherRecord

SAMPLE_HOURLY = {
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


class WeatherObservationTests(unittest.TestCase):
    def test_from_open_meteo_hourly_parses_variables_at_index(self):
        observation = WeatherObservation.from_open_meteo_hourly(SAMPLE_HOURLY, 1)

        self.assertEqual(observation.temperature_c, 6.2)
        self.assertEqual(observation.apparent_temperature_c, 3.1)
        self.assertEqual(observation.precipitation_mm, 0.5)
        self.assertEqual(observation.rain_mm, 0.5)
        self.assertEqual(observation.snowfall_cm, 0.0)
        self.assertEqual(observation.cloud_cover_percent, 90)
        self.assertEqual(observation.wind_speed_kmh, 14.4)
        self.assertEqual(observation.wind_gusts_kmh, 22.2)
        self.assertEqual(observation.wind_direction_degrees, 280)
        self.assertEqual(observation.relative_humidity_percent, 80)
        self.assertEqual(observation.weather_code, 61)
        self.assertEqual(
            observation.observed_at, datetime(2024, 1, 15, 14, 0, tzinfo=UTC)
        )


class WeatherRecordTests(unittest.TestCase):
    def test_to_observation_returns_stored_fields(self):
        record = WeatherRecord(
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
            observed_at=datetime(2024, 1, 15, 14, 0, tzinfo=UTC),
        )

        observation = record.to_observation()

        self.assertEqual(
            observation,
            WeatherObservation.from_open_meteo_hourly(SAMPLE_HOURLY, 1),
        )


if __name__ == "__main__":
    unittest.main()
