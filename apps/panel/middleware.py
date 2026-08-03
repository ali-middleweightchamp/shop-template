"""
Язык панели /panel/.

Проект использует i18n_patterns(prefix_default_language=False): для URL без
языкового префикса Django принудительно ставит язык по умолчанию и игнорирует
куку языка. Панель живёт вне префикса, поэтому язык из куки применяем сами —
уже после стандартного LocaleMiddleware.
"""
from django.conf import settings
from django.utils import translation


class PanelLocaleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._langs = {code for code, _ in settings.LANGUAGES}

    def __call__(self, request):
        if request.path.startswith("/panel/"):
            lang = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
            if lang in self._langs:
                translation.activate(lang)
                request.LANGUAGE_CODE = lang
        return self.get_response(request)
