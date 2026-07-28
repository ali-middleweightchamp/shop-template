from django.shortcuts import render


def home(request):
    """Главная. На этапе каркаса — простая страница-заглушка.
    На этапе 4 здесь появится витрина (категории, популярные товары)."""
    return render(request, "home.html")
