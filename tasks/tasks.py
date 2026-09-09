import logging

from celery import shared_task

logger = logging.getLogger("tasks")


@shared_task
def log_test_message(message: str) -> None:
    logger.info("Test task received: %s", message)
