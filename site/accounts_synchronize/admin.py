from django.contrib import admin

from accounts_synchronize.models import AccountsSyncronizeSettings

@admin.register(AccountsSyncronizeSettings)
class MoySkladSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not AccountsSyncronizeSettings.objects.exists()
