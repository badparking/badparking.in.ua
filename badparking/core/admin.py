from django.contrib import admin
from imagekit.admin import AdminThumbnail

from .models import CrimeType, Claim, ClaimState


class CrimeTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "enabled")
    ordering = ('-enabled',)

    def has_delete_permission(self, request, obj=None):
        return False


class MediaInline(admin.TabularInline):
    model = Claim.media.through
    raw_id_fields = ('mediafilemodel',)
    readonly_fields = ('admin_thumbnail',)
    admin_thumbnail = AdminThumbnail(image_field=lambda obj: obj.mediafilemodel.thumbnail)


class ClaimStateInline(admin.TabularInline):
    model = ClaimState
    readonly_fields = ('logged_at',)


class ClaimAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'city', 'created_at', 'status')
    inlines = [MediaInline, ClaimStateInline]
    exclude = ('media',)
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'modified_at', 'authorized_at')
    list_filter = ('status', 'crimetypes')
    search_fields = ('id', 'license_plates', 'city', 'address', 'user__email', 'user__last_name')


admin.site.register(CrimeType, CrimeTypeAdmin)
admin.site.register(Claim, ClaimAdmin)
