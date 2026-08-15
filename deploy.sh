#!/bin/sh
# Обновление боевого сайта: подтянуть код → пересобрать → поднять → дождаться готовности.
# Запуск на сервере:  ./deploy.sh
#
# Миграции, сбор статики и владельца магазина применяет entrypoint контейнера web
# при старте (docker/entrypoint.sh). Здесь их НЕ дублируем: второй параллельный
# `migrate` ловил гонку с entrypoint и падал с «column already exists».
set -e
cd "$(dirname "$0")"

# Готов ли web: gunicorn отвечает на :8000. Он стартует ТОЛЬКО после того, как
# entrypoint закончил миграции и сбор статики (exec "$@" в самом конце), поэтому
# ответ — надёжный признак «всё применилось и сайт живой».
web_ready() {
  docker compose exec -T web python - <<'PY' 2>/dev/null
import sys, urllib.request, urllib.error
try:
    urllib.request.urlopen("http://127.0.0.1:8000/", timeout=3)
except urllib.error.HTTPError:
    pass          # ответил (пусть даже 4xx/5xx) — значит живой
except Exception:
    sys.exit(1)   # ещё не поднялся
PY
}

echo "→ Обновляю код из git..."
git pull --ff-only

echo "→ Пересобираю и поднимаю контейнеры..."
docker compose up -d --build

echo "→ Жду готовности web (entrypoint применяет миграции и статику)..."
i=0
until web_ready; do
  i=$((i + 1))
  if [ "$i" -ge 45 ]; then
    echo "⚠ web не ответил за ~90с. Логи: docker compose logs --tail=50 web"
    exit 1
  fi
  sleep 2
done

echo "✓ Готово. Сайт обновлён."
