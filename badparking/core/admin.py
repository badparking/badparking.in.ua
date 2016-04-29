from django.contrib import admin
from .models import CrimeType, Claim


class CrimeTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "enabled")
    ordering = ('-enabled',)

    def has_delete_permission(self, request, obj=None):
        return False


class ClaimAdmin(admin.ModelAdmin):
    list_display = ("pk", "created_at")


admin.site.register(CrimeType, CrimeTypeAdmin)
admin.site.register(Claim, ClaimAdmin)
