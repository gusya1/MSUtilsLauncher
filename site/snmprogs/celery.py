import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'snmprogs.settings')

app = Celery('snmprogs')

# Используем строку конфигурации из настроек Django с префиксом CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи в файлах tasks.py каждого приложения
app.autodiscover_tasks()
