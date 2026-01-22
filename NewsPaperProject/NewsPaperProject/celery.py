import os
from celery import Celery
from celery.schedules import crontab

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewsPaperProject.settings')

app = Celery('NewsPaperProject')

# Загружаем настройки из настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи в приложениях Django
app.autodiscover_tasks()

# Настройка периодических задач
app.conf.beat_schedule = {
    'send-weekly-newsletter-every-monday-8am': {
        'task': 'news.tasks.send_weekly_newsletter',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Понедельник, 8:00
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')