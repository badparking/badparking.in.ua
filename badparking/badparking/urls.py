"""badparking URL Configuration
"""

from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from mobile_api import urls as mobile_api_urls
from profiles import urls as profile_urls


urlpatterns = [
    url(r'^api/v1/', include(mobile_api_urls, namespace='v1')),
    url(r'^profiles/', include(profile_urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^docs/', include('rest_framework_swagger.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
