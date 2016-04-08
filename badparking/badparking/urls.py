"""badparking URL Configuration
"""

from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers
from mobile_api.serializers import CrimeTypeViewSet


router = routers.DefaultRouter()
router.register(r'types', CrimeTypeViewSet)

urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^docs/', include('rest_framework_swagger.urls')),
]
