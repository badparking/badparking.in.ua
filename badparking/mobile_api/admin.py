from django.contrib import admin

from .models import Client


class ClientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'is_active')

admin.site.register(Client, ClientAdmin)
