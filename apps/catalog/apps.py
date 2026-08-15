from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalog"
    verbose_name = "Каталог"

    def ready(self):
        # Сбрасываем кэш мега-меню «Каталог» при любом изменении категорий
        # (панель или Django-admin), чтобы меню не отставало.
        from django.core.cache import cache
        from django.db.models.signals import post_delete, post_save

        from .models import Category

        def _clear_menu(sender, **kwargs):
            cache.delete("catalog_menu_v1")

        post_save.connect(_clear_menu, sender=Category, dispatch_uid="catmenu_save")
        post_delete.connect(_clear_menu, sender=Category, dispatch_uid="catmenu_del")
