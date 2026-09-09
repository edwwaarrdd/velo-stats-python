from django.core.management.base import BaseCommand

from stations.models import StationRecord
from stations.services import VeloAntwerpStationInformationService


class Command(BaseCommand):
    help = "Fetch Velo Antwerp station information and save it to the database."

    def handle(self, *args, **options):
        service = VeloAntwerpStationInformationService()
        collection = service.fetch_stations()

        created_count = 0
        updated_count = 0
        for station in collection:
            _, created = StationRecord.objects.update_or_create(
                station_id=station.station_id,
                defaults={
                    "name": station.name,
                    "short_name": station.short_name,
                    "lat": station.lat,
                    "lon": station.lon,
                    "address": station.address,
                    "post_code": station.post_code,
                    "rental_methods": station.rental_methods,
                    "capacity": station.capacity,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {len(collection)} stations "
                f"({created_count} created, {updated_count} updated)."
            )
        )
