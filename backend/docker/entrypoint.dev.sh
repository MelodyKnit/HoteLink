#!/bin/sh
set -eu

poetry install --only main --no-root

if [ ! -f "/app/manage.py" ]; then
  echo "Django project is not initialized yet."
  echo "The backend dev container is ready with dependencies installed."
  echo "After manage.py and config/settings are created, this container can run the Django dev server directly."
  tail -f /dev/null
fi

python manage.py migrate --noinput || true
exec python manage.py runserver 0.0.0.0:8000
