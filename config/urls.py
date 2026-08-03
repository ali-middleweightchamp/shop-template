"""Корневые URL проекта."""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

from apps.catalog import views as catalog_views
from apps.catalog.sitemaps import CategorySitemap, ProductSitemap, StaticSitemap

# Русифицируем заголовки админки
admin.site.site_header = _("Управление магазином")
admin.site.site_title = _("Магазин")
admin.site.index_title = _("Панель управления")

# Django-админка /admin/ — служебный вход ТОЛЬКО для суперпользователя (нас).
# Продавцы (staff) сюда не заходят — у них своя панель /panel/.
admin.site.has_permission = lambda request: request.user.is_active and request.user.is_superuser

sitemaps = {
    "static": StaticSitemap,
    "products": ProductSitemap,
    "categories": CategorySitemap,
}

# Вне языкового префикса: SEO-служебные и переключение языка
urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", catalog_views.robots_txt, name="robots"),
    # Кастомная панель продавца (вне языкового префикса)
    path("panel/", include("apps.panel.urls")),
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
