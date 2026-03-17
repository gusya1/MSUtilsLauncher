from django.contrib import admin

from .models import ProcessingCreatorSettings

@admin.register(ProcessingCreatorSettings)
class MoySkladSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not ProcessingCreatorSettings.objects.exists()
