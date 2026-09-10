from django.core.management.base import BaseCommand

from rides.models import RideRecord
from tasks.tasks import check_ride_distance


class Command(BaseCommand):
    help = (
        "Dispatch a Celery task per unchecked ride to calculate and cache the "
        "distance between its origin and destination stations."
    )

    def handle(self, *args, **options):
        rides = RideRecord.objects.filter(distance_checked_at__isnull=True)

        dispatched_count = 0
        for ride in rides:
            check_ride_distance.delay(ride.ride_id)
            dispatched_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Dispatched {dispatched_count} ride distance check task(s).")
        )
