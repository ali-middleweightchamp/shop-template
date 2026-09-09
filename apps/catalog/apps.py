from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalog"
    verbose_name = "Каталог"

    def ready(self):
        from django.core.cache import cache
        from django.db.models.signals import post_delete, post_save

        from .models import Banner, Category, Product

        def _clear_menu(sender, **kwargs):
            cache.delete("catalog_menu_v1")

        def _clear_all(sender, **kwargs):
            cache.clear()

        post_save.connect(_clear_menu, sender=Category, dispatch_uid="catmenu_save")
        post_delete.connect(_clear_menu, sender=Category, dispatch_uid="catmenu_del")

        # Сбрасываем весь кеш страниц при изменении товаров, категорий, баннеров
        for model, uid in [
            (Product, "cache_product"),
            (Category, "cache_category"),
            (Banner, "cache_banner"),
        ]:
            post_save.connect(_clear_all, sender=model, dispatch_uid=f"{uid}_save")
            post_delete.connect(_clear_all, sender=model, dispatch_uid=f"{uid}_del")
