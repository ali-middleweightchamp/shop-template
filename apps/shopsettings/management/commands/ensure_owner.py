"""
Создаёт или обновляет владельца магазина из переменных окружения.

Владелец — это учётка **сотрудника** (is_staff) в группе «Продавцы», а НЕ
суперпользователь. Он заходит в панель /panel/ и не может сломать систему.
Суперпользователь (полный доступ, /admin/) остаётся у разработчика —
создаётся отдельно через createsuperuser и владельцу не передаётся.

Идемпотентно: безопасно запускать при каждом деплое. Пароль хранится в .env
сервера, а не в коде. Публичной регистрации в системе нет.

Переменные:
    OWNER_USERNAME    — логин владельца (обязателен, иначе команда пропускается)
    OWNER_PASSWORD    — пароль (если задан — всегда переустанавливается)
    OWNER_EMAIL       — email (необязателен)
    OWNER_SUPERUSER   — "true", чтобы дать полный доступ (по умолчанию нет)
"""
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

SELLER_GROUP = "Продавцы"


class Command(BaseCommand):
    help = "Создаёт/обновляет владельца-сотрудника из OWNER_USERNAME/OWNER_PASSWORD/OWNER_EMAIL"

    def handle(self, *args, **options):
        User = get_user_model()

        username = (os.environ.get("OWNER_USERNAME") or "").strip()
        password = (os.environ.get("OWNER_PASSWORD") or "").strip()
        email = (os.environ.get("OWNER_EMAIL") or "").strip()

        if not username:
            self.stdout.write(
                self.style.WARNING(
                    "OWNER_USERNAME не задан — создание владельца пропущено. "
                    "Задайте переменные в .env или используйте createsuperuser."
                )
            )
            return

        user, created = User.objects.get_or_create(
            username=username, defaults={"email": email}
        )

        # Владелец — сотрудник с доступом в панель. Суперюзером делаем только
        # если явно попросили через OWNER_SUPERUSER=true.
        make_super = (os.environ.get("OWNER_SUPERUSER") or "").strip().lower() in ("1", "true", "yes")
        user.is_staff = True
        user.is_superuser = make_super
        user.is_active = True
        if email:
            user.email = email

        if password:
            # Пароль хранится только в хешированном виде; из .env лишь задаётся
            user.set_password(password)
        elif created:
            # Первое создание без пароля — ставим неюзабельный, чтобы не было пустого пароля.
            # Владелец задаёт пароль позже (OWNER_PASSWORD или через changepassword).
            user.set_unusable_password()
            self.stdout.write(
                self.style.WARNING(
                    "OWNER_PASSWORD не задан — владелец создан без пароля. "
                    f"Задайте пароль: manage.py changepassword {username}"
                )
            )

        user.save()

        # Кладём владельца в группу «Продавцы» (права на разделы задаются группе)
        group, _ = Group.objects.get_or_create(name=SELLER_GROUP)
        user.groups.add(group)

        action = "создан" if created else "обновлён"
        role = "суперпользователь" if make_super else "сотрудник, группа «Продавцы»"
        self.stdout.write(self.style.SUCCESS(f"Владелец «{username}» {action} ({role})."))
