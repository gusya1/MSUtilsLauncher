from django.contrib import admin

from .models import PaymentInCreatorSettings

@admin.register(PaymentInCreatorSettings)
class MoySkladSettingsAdmin(admin.ModelAdmin):
    

    def has_add_permission(self, request):
        return not PaymentInCreatorSettings.objects.exists()
