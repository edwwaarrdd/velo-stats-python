from django.core.management.base import BaseCommand

from tasks.tasks import log_test_message


class Command(BaseCommand):
    help = "Dispatch a test Celery task that logs a message from the worker."

    def add_arguments(self, parser):
        parser.add_argument(
            "--message",
            default="Hello from dispatch_test_task",
            help="Message the worker should write to the log.",
        )

    def handle(self, *args, **options):
        result = log_test_message.delay(options["message"])
        self.stdout.write(
            self.style.SUCCESS(f"Dispatched task {result.id} to the queue.")
        )
