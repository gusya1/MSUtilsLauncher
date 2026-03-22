from django.contrib import admin

from .models import Location, YandexGeocoderSettings

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass

@admin.register(YandexGeocoderSettings)
class SettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not YandexGeocoderSettings.objects.exists()
