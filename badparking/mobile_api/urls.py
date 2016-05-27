from django.conf.urls import include, url

from rest_framework import routers
from rest_framework_jwt.views import refresh_jwt_token, verify_jwt_token

from .views import CurrentUserView, CrimeTypeViewSet, ClaimListView, CurrentUserClaimViewSet


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'types', CrimeTypeViewSet)
router.register(r'claims/my', CurrentUserClaimViewSet, base_name='my-claims')


urlpatterns = [
    url(r'^token/refresh$', refresh_jwt_token),
    url(r'^token/verify$', verify_jwt_token),
    url(r'^user/me$', CurrentUserView.as_view()),
    url(r'^claims$', ClaimListView.as_view()),
    url(r'^', include(router.urls)),
]
