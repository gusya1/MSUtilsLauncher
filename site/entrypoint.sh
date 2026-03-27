#!/bin/sh

DJANGO_MODE=${DJANGO_SERVER_TYPE:-runserver}

PROJECT_NAME=snmprogs

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

case "$DJANGO_MODE" in
    gunicorn)
        echo "Starting Gunicorn server for $PROJECT_NAME..."
        exec gunicorn ${PROJECT_NAME}.wsgi:application --timeout 120 --bind 0.0.0.0:8000 --workers 3
        ;;
    runserver)
        echo "Starting Django runserver..."
        exec python manage.py runserver 0.0.0.0:8000
        ;;
    celery)
        echo "Starting celery..."
        celery -A snmprogs worker --loglevel=info
        ;;
    *)
        echo "Unknown DJANGO_SERVER_TYPE: $DJANGO_MODE. Exiting."
        exit 1
        ;;
esac
