from django.contrib import admin

from .models import DeliveryMapPaletteSettings, PaletteItem

class PaletteItemInline(admin.TabularInline):
    model = PaletteItem
    extra = 1

@admin.register(DeliveryMapPaletteSettings)
class MoySkladSettingsAdmin(admin.ModelAdmin):
    inlines = [PaletteItemInline]

    def has_add_permission(self, request):
        return not DeliveryMapPaletteSettings.objects.exists()
