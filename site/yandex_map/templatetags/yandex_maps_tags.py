from django import template
from django.utils.safestring import mark_safe
from django.conf import settings

register = template.Library()

@register.simple_tag()
def yandex_maps_on_load_script():
    script = (
        f'<script src="https://api-maps.yandex.ru/v3/'
        f'?apikey={settings.YANDEX_MAPS_API_KEY}&lang=ru_RU" '
        f'type="text/javascript"></script>'
    )
    return mark_safe(script)