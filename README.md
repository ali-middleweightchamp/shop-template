# Каталог-шаблон для магазина

Переиспользуемый шаблон интернет-каталога для малого бизнеса (канцтовары,
автозапчасти, стройматериалы, оптовики). Покупатель без регистрации собирает
корзину и оформляет заказ **в один клик через Telegram/WhatsApp** — продавцу
приходит готовое сообщение в обычную личку. Товарами управляют через админку,
прайс загружается файлом Excel.

Шаблон разворачивается под нового клиента за пару часов: меняешь настройки
в админке (название, логотип, цвет, Telegram, телефон) и загружаешь прайс.

## Возможности

- 🛒 Корзина на `localStorage`, заказ → deep-link в Telegram/WhatsApp с готовым текстом
- 📱 Mobile-first витрина: главная, каталог, карточка товара, поиск, контакты
- 🎨 Тема «Изумруд» (светлая/тёмная), фирменный цвет из настроек — **ничего не захардкожено**
- 🌐 Двуязычность **ru / uz** (латиница), переключатель в шапке
- ⚙️ Админка на django-jazzmin: массовое редактирование цен/наличия, импорт прайса
- 🖼️ Превью изображений (easy-thumbnails), SVG-плейсхолдеры

## Стек

Python 3.12 · Django 5 · PostgreSQL 16 · Django Templates · Tailwind CSS (CLI) ·
Alpine.js · Pillow · easy-thumbnails · openpyxl · gunicorn · whitenoise ·
Docker + docker-compose · ruff + black

## Быстрый старт (Docker)

```bash
cp .env.example .env          # заполнить SECRET_KEY, DOMAIN, OWNER_* и т.д.
docker compose up -d --build  # миграции, статика и владелец создаются автоматически
```

Открыть: витрина — `https://<DOMAIN>` , панель продавца — `https://<DOMAIN>/panel/`

Демо-данные (по желанию):
```bash
docker compose exec web python manage.py seed_demo               # канцтовары
docker compose exec web python manage.py seed_demo --preset=toys # игрушки и т.д.
```

## Деплой на VPS (Caddy + HTTPS)

Нужен сервер (2 vCPU / 2–4 GB, напр. Hetzner CX22) и домен с A-записью на его IP.

```bash
# 1. На сервере: Docker + Compose
curl -fsSL https://get.docker.com | sh

# 2. Код и настройки
git clone <repo-url> shop && cd shop
cp .env.example .env
nano .env        # DJANGO_SETTINGS_MODULE=config.settings.prod, DEBUG=False,
                 # SECRET_KEY, DOMAIN=shop.example.uz, ALLOWED_HOSTS, POSTGRES_*,
                 # DATABASE_URL, OWNER_USERNAME/PASSWORD/EMAIL

# 3. Запуск (Caddy сам выпустит HTTPS-сертификат для DOMAIN)
docker compose up -d --build
```

Готово: `https://shop.example.uz` — витрина, `/panel/` — панель продавца
(логин/пароль из `OWNER_*`).

Обновление и бэкапы:
```bash
./deploy.sh    # git pull + пересборка + миграции
./backup.sh    # дамп базы + архив медиа в backups/ (можно в cron)
```

При сдаче: покажите владельцу вход в `/panel/` и попросите сменить пароль.
Суперпользователь (`/admin/`) остаётся у вас — создаётся отдельно
(`docker compose exec web python manage.py createsuperuser`).

## Локально без Docker

Нужны Python 3.12, Node 20 и PostgreSQL (или SQLite для быстрого просмотра).

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
npm install && npm run build:css          # сборка Tailwind
export DATABASE_URL="sqlite:///$(pwd)/local.sqlite3"   # быстрый локальный вариант
python manage.py migrate
python manage.py runserver
```

Пересборка стилей на лету: `npm run watch:css`.

## Структура

```
config/settings/{base,dev,prod}.py   настройки (django-environ)
apps/catalog/        категории, товары, витрина
apps/shopsettings/   настройки магазина (брендинг, контакты, тема)
apps/importer/       импорт/экспорт прайса
templates/           шаблоны (base + catalog + admin)
static/src/          input.css, themes.css, шрифты, JS
docker/              Dockerfile, nginx.conf, entrypoint
locale/uz/           узбекский перевод интерфейса
```

## Локализация

Перевод интерфейса — стандартный i18n Django. После изменения строк:

```bash
python manage.py makemessages -l uz
python manage.py compilemessages -l uz
```

## Стиль и линт

```bash
ruff check . && black .
```

## Доступ в админку

Регистрации для покупателей нет — заказы идут через Telegram. Доступ в админку
только у продавца, суперпользователь создаётся из командной строки
(`createsuperuser`). Пароль хранится хэшированным; сменить —
`python manage.py changepassword <user>`.

---

Это шаблон: специфичное для конкретного магазина не хардкодится — всё берётся
из модели `ShopSettings`.
