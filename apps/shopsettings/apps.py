from django.apps import AppConfig


class ShopSettingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.shopsettings"
    verbose_name = "Настройки магазина"

    def ready(self):
        from django.core.cache import cache
        from django.db.models.signals import post_save

        from .models import ShopSettings

        def _clear_all(sender, **kwargs):
            cache.clear()

        post_save.connect(_clear_all, sender=ShopSettings, dispatch_uid="shopsettings_cache_clear")
