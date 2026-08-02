from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.home, name="home"),
    path("catalog/", views.catalog, name="catalog"),
    path("search/", views.search, name="search"),
    path("contacts/", views.contacts, name="contacts"),
    path("cart/", views.cart, name="cart"),
    path("favorites/", views.favorites, name="favorites"),
    path("order/create/", views.order_create, name="order_create"),
    path("order/<str:code>/", views.order_detail, name="order"),
    path("catalog/<slug:slug>/", views.category, name="category"),
    path("product/<slug:slug>/", views.product_detail, name="product"),
]
