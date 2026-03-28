"""
Дебажная конфигурация сайта. Для запуска скопировать с именем settings.py.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
# этот хак позволяет дозаполнять нужные настройки
from .common_settings import * # noqa: F403

import os


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'cg#p$g+j9tax!#a3cup@1$8obt2_+&k3q+pmu)5%asj6yjpkag')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

CSRF_COOKIE_SECURE = True  # если используешь HTTPS
CSRF_TRUSTED_ORIGINS = ['https://snmprogs.sobakanamyase.ru']

ALLOWED_HOSTS = ['*']

ADMINS = [('Сергей', 'serheos@gmail.com')]

LOG_LEVEL = os.environ.get('DJANGO_LOG_LEVEL', 'INFO')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters':{
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'delivery_distributor': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'moysklad_sync': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['mail_admins'],
        'level': 'ERROR',
    },
}

YANDEX_MAPS_API_KEY = os.environ.get('YANDEX_MAPS_API_KEY', None)

OSRM_URL = os.environ.get('OSRM_URL', 'http://osrm:5000')