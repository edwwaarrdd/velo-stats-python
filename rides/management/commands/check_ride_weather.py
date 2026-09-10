from django.core.management.base import BaseCommand

from rides.models import RideRecord
from tasks.tasks import check_ride_weather


class Command(BaseCommand):
    help = (
        "Dispatch a Celery task per ride to fetch and cache the weather at its "
        "origin station and checkin time from Open-Meteo."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-fetch weather for every ride, even if already checked.",
        )

    def handle(self, *args, **options):
        force = options["force"]
        rides = (
            RideRecord.objects.all()
            if force
            else RideRecord.objects.filter(weather_checked_at__isnull=True)
        )

        dispatched_count = 0
        for ride in rides:
            check_ride_weather.delay(ride.ride_id, force=force)
            dispatched_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Dispatched {dispatched_count} ride weather check task(s).")
        )
