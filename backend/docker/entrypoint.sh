#!/bin/sh
set -eu

if [ ! -f "/app/manage.py" ]; then
  echo "Error: /app/manage.py not found."
  echo "Initialize the Django project structure before using the production backend container."
  exit 1
fi

if [ "${CONTAINER_ROLE:-web}" = "web" ] && [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  python manage.py migrate --noinput
fi

if [ "${CONTAINER_ROLE:-web}" = "web" ] && [ "${RUN_COLLECTSTATIC:-1}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

if [ "$#" -eq 0 ]; then
  set -- gunicorn "${DJANGO_WSGI_MODULE:-config.wsgi:application}" \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-120}"
fi

exec "$@"
