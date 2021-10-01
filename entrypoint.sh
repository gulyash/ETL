#!/bin/bash
set -e
echo $1

if [ "$1" = 'nostatic' ]; then
    gunicorn config.wsgi -b 0.0.0.0:8000
elif [ "$1" = 'standalone' ]; then
    python manage.py collectstatic --noinput
    python manage.py runserver 0.0.0.0:8000
fi
