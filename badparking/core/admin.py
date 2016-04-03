from django.contrib import admin
from .models import CrimeType


class CrimeTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "enabled")
    ordering = ('-enabled',)

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(CrimeType, CrimeTypeAdmin)
