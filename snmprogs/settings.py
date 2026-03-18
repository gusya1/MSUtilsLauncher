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
import logging.config


SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'cg#p$g+j9tax!#a3cup@1$8obt2_+&k3q+pmu)5%asj6yjpkag')
DEBUG = True

ALLOWED_HOSTS = ['*']

ADMINS = [('Сергей', 'serheos@gmail.com')]

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
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['mail_admins'],
        'level': 'ERROR',
    },
}
logging.config.dictConfig(LOGGING)


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}