from django.core.management.base import BaseCommand

from rides.models import RideRecord
from rides.services import JsonFileRideService


class Command(BaseCommand):
    help = "Load customer ride history from data/rides.json into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            help="Path to the rides JSON export (defaults to data/rides.json).",
        )

    def handle(self, *args, **options):
        service = (
            JsonFileRideService(options["path"]) if options.get("path") else JsonFileRideService()
        )
        collection = service.fetch_rides()

        created_count = 0
        updated_count = 0
        for ride in collection:
            _, created = RideRecord.objects.update_or_create(
                ride_id=ride.ride_id,
                defaults={
                    "account_id": ride.account_id,
                    "status": ride.status,
                    "duration": ride.duration,
                    "bike_number": ride.bike_number,
                    "origin_station_code": ride.origin_station_code,
                    "origin_station": ride.origin_station,
                    "origin_slot_id": ride.origin_slot_id,
                    "checkout_time": ride.checkout_time,
                    "destination_station_code": ride.destination_station_code,
                    "destination_station": ride.destination_station,
                    "destination_slot_id": ride.destination_slot_id,
                    "checkin_time": ride.checkin_time,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {len(collection)} rides "
                f"({created_count} created, {updated_count} updated)."
            )
        )
