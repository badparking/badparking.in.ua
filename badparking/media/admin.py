from django.contrib import admin
from .models import MediaFileModel

class MediaFileModelAdmin(admin.ModelAdmin):
    list_display = ("pk", "created_at")

admin.site.register(MediaFileModel, MediaFileModelAdmin)
