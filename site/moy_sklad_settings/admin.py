from django.contrib import admin

from .models import MoySkladSettings, BlacklistProjectMS


class BlacklistProjectMsInline(admin.TabularInline):
    model = BlacklistProjectMS
    extra = 1


@admin.register(MoySkladSettings)
class MoySkladSettingsAdmin(admin.ModelAdmin):
    inlines = [BlacklistProjectMsInline]

    def has_add_permission(self, request):
        return not MoySkladSettings.objects.exists()
