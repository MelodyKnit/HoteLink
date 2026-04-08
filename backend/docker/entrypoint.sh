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

# 自动创建超级管理员（仅在环境变量存在且用户不存在时）
if [ "${CONTAINER_ROLE:-web}" = "web" ] && [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
  python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='${DJANGO_SUPERUSER_USERNAME}').exists():
    User.objects.create_superuser('${DJANGO_SUPERUSER_USERNAME}', '${DJANGO_SUPERUSER_EMAIL:-admin@hotelink.local}', '${DJANGO_SUPERUSER_PASSWORD:-admin123}')
    print('Superuser created.')
else:
    print('Superuser already exists.')
" 2>/dev/null || true
fi

if [ "$#" -eq 0 ]; then
  set -- gunicorn "${DJANGO_WSGI_MODULE:-config.wsgi:application}" \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-120}"
fi

exec "$@"
