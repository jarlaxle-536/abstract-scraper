from celery import Celery
import datetime
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'abstract_scraper.settings')

app = Celery('abstract_scraper')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.loader.override_backends['django-db'] = 'django_celery_results.backends.database:DatabaseBackend'

app.autodiscover_tasks()

app.conf.update(
    CELERYBEAT_SCHEDULE = {
        'update_proxies': {
            'task': 'abstract_scraper.applications.proxies.tasks.update_proxies',
            'schedule': datetime.timedelta(minutes=5)
        },
    }
)
