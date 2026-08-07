"""URL панели продавца (/panel/)."""
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import StaffAuthenticationForm

app_name = "panel"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="panel/login.html",
            authentication_form=StaffAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="panel:login"), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("styleguide/", views.styleguide, name="styleguide"),
    # Товары
    path("products/", views.products, name="products"),
    path("products/new/", views.product_edit, name="product_new"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("products/save-prices/", views.product_save_prices, name="product_save_prices"),
    path("products/toggle/", views.product_toggle, name="product_toggle"),
    path("products/discount/", views.product_discount, name="product_discount"),
    path("products/bulk/", views.product_bulk, name="product_bulk"),
    # Категории
    path("categories/", views.categories, name="categories"),
    path("categories/new/", views.category_edit, name="category_new"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    path("categories/reorder/", views.category_reorder, name="category_reorder"),
    path("promotions/", views.promotions, name="promotions"),
    # Баннеры
    path("banners/", views.banners, name="banners"),
    path("banners/new/", views.banner_edit, name="banner_new"),
    path("banners/<int:pk>/edit/", views.banner_edit, name="banner_edit"),
    path("banners/<int:pk>/delete/", views.banner_delete, name="banner_delete"),
    path("banners/toggle/", views.banner_toggle, name="banner_toggle"),
    path("banners/reorder/", views.banner_reorder, name="banner_reorder"),
    path("settings/", views.settings_view, name="settings"),
    # Прайс-лист
    path("price/", views.price, name="price"),
    path("price/template/", views.price_template, name="price_template"),
    path("price/export/", views.price_export, name="price_export"),
]
