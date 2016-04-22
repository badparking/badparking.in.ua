from django.conf.urls import url

from .views import OschadBankOAuthLoginView, PrivatBankOAuthLoginView, OschadBankOAuthCompleteLoginView,\
    PrivatBankOAuthCompleteLoginView, DummyOAuthLoginView, DummyOAuthCompleteLoginView


urlpatterns = [
    url(r'^login/oschadbank$', OschadBankOAuthLoginView.as_view(), name='profiles>login>oschadbank'),
    url(r'^login/privatbank$', PrivatBankOAuthLoginView.as_view(), name='profiles>login>privatbank'),
    url(r'^login/dummy$', DummyOAuthLoginView.as_view(), name='profiles>login>dummy'),
    url(r'^complete/oschadbank$', OschadBankOAuthCompleteLoginView.as_view(),
        name='profiles>complete_login>oschadbank'),
    url(r'^complete/privatbank$', PrivatBankOAuthCompleteLoginView.as_view(),
        name='profiles>complete_login>privatbank'),
    url(r'^complete/dummy$', DummyOAuthCompleteLoginView.as_view(),
        name='profiles>complete_login>dummy'),
]
