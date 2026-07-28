"""Корневые URL проекта."""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

# Русифицируем заголовки админки
admin.site.site_header = _("Управление магазином")
admin.site.site_title = _("Магазин")
admin.site.index_title = _("Панель управления")

urlpatterns = [
    # Переключение языка (POST /i18n/setlang/)
    path("i18n/", include("django.conf.urls.i18n")),
]

# Языковой префикс в URL (/ru/, /uz/). Админка живёт вне префикса.
urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("apps.catalog.urls")),
    prefix_default_language=False,
)

if settings.DEBUG:
    # В dev Django сам отдаёт media; в проде это делает nginx
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
