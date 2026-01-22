from django.core.management.base import BaseCommand
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util
from news.tasks import send_weekly_digest
import logging

logger = logging.getLogger(__name__)

@util.close_old_connections
def send_weekly_newsletter():
    """Задача для еженедельной рассылки"""
    logger.info("Starting weekly newsletter task...")
    try:
        count = send_weekly_digest()
        logger.info(f"Weekly newsletter sent to {count} users")
    except Exception as e:
        logger.error(f"Error sending weekly newsletter: {e}")

class Command(BaseCommand):
    help = "Starts the APScheduler for weekly newsletters"

    def handle(self, *args, **options):
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # Добавляем задачу: каждое воскресенье в 10:00
        scheduler.add_job(
            send_weekly_newsletter,
            trigger=CronTrigger(day_of_week="sun", hour=10, minute=0),
            id="weekly_newsletter",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'weekly_newsletter'.")

        # Задача для тестирования: каждую минуту (для отладки)
        scheduler.add_job(
            send_weekly_newsletter,
            trigger=CronTrigger(minute="*/1"),
            id="test_newsletter",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added test job 'test_newsletter' (runs every minute).")

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully.")