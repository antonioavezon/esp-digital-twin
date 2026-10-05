"""Preferencias de presentación guardadas en cookies. No tocan el motor físico."""

LANG_COOKIE = "esp_lang"
THEME_COOKIE = "esp_theme"
LANGS = ("es", "en")
THEMES = ("dark", "light")


def language_of(request) -> str:
    value = request.COOKIES.get(LANG_COOKIE, "es")
    return value if value in LANGS else "es"


def theme_of(request) -> str:
    value = request.COOKIES.get(THEME_COOKIE, "dark")
    return value if value in THEMES else "dark"
