from django.contrib import admin
from django.utils.html import format_html
from .models import CrimeType, Claim, ClaimState


class CrimeTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "enabled")
    ordering = ('-enabled',)

    def has_delete_permission(self, request, obj=None):
        return False


class MediaInline(admin.TabularInline):
    model = Claim.images.through
    raw_id_fields = ('mediafilemodel',)
    readonly_fields = ('image',)

    def image(self, obj):
        return format_html('<a href="{}"><img src="{}" width="100" height="100" /></a>',
                           obj.mediafilemodel.file.url, obj.mediafilemodel.file.url)


class ClaimStateInline(admin.TabularInline):
    model = ClaimState
    readonly_fields = ('logged_at',)


class ClaimAdmin(admin.ModelAdmin):
    list_display = ('pk', 'created_at', 'status')
    inlines = [MediaInline, ClaimStateInline]
    exclude = ('images',)
    readonly_fields = ('created_at', 'modified_at')


admin.site.register(CrimeType, CrimeTypeAdmin)
admin.site.register(Claim, ClaimAdmin)
