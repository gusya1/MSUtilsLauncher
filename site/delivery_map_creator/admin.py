from django.contrib import admin

from delivery_map_creator.models import DeliveryMapGeneratorSettings

@admin.register(DeliveryMapGeneratorSettings)
class MoySkladSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not DeliveryMapGeneratorSettings.objects.exists()
