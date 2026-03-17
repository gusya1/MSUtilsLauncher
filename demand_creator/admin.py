from django.contrib import admin

from .models import DemandCreatorSettings

@admin.register(DemandCreatorSettings)
class MoySkladSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not DemandCreatorSettings.objects.exists()
