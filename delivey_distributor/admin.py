from django.contrib import admin

from .models import DeliveryRoutingSettings, Courier, Location

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass

class PaletteItemInline(admin.TabularInline):
    model = Courier
    extra = 1

@admin.register(DeliveryRoutingSettings)
class MoySkladSettingsAdmin(admin.ModelAdmin):
    inlines = [PaletteItemInline]

    def has_add_permission(self, request):
        return not DeliveryRoutingSettings.objects.exists()
