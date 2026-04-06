#!/bin/sh
set -eu

poetry install --only main --no-root

if [ ! -f "/app/manage.py" ]; then
  echo "Django project is not initialized yet."
  echo "The backend dev container is ready with dependencies installed."
  echo "After manage.py and config/settings are created, this container can run the Django dev server directly."
  tail -f /dev/null
fi

python manage.py check
python manage.py migrate --noinput || true

# ----- 后台迁移自动检测 -----
# 每 10 秒扫描一次，发现未应用的迁移后自动执行 migrate。
# 这样本地新增 migration 文件（通过 volume 同步）后无需手动操作。
(
  while true; do
    sleep 10
    # showmigrations --plan 中 [ ] 表示未应用
    pending=$(python manage.py showmigrations --plan 2>/dev/null | grep '\[ \]' || true)
    if [ -n "$pending" ]; then
      echo "[auto-migrate] 检测到未应用的迁移，正在执行 migrate ..."
      python manage.py migrate --noinput 2>&1 | sed 's/^/[auto-migrate] /'
      echo "[auto-migrate] 迁移完成。"
    fi
  done
) &

exec python manage.py runserver 0.0.0.0:8000
