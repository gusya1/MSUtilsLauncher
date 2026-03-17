from django.contrib import admin

from moy_sklad_settings.models import MoySkladSettings

@admin.register(MoySkladSettings)
class MoySkladSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not MoySkladSettings.objects.exists()
