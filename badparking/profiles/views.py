import logging

from datetime import datetime

from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.generic import View
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.apps import apps

from rest_framework_jwt.settings import api_settings

from mobile_api.models import Client
from .serializers import UserSerializer
from .constants import OSCHAD_BANKID, PRIVAT_BANKID
from .bankid import BankIdError

logger = logging.getLogger(__name__)
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
oschad_bankid = apps.get_app_config('profiles').oschad_bankid
privat_bankid = apps.get_app_config('profiles').privat_bankid
User = get_user_model()


class OAuthLoginView(View):
    """
    Initiates the OAuth2 authorization flow.
    Additionally requires `client_id` and `client_secrect` query string params corresponding to an active
    `mobile_api.models.Client` to be present for client authentication.

    Concrete implementations should be used instead of this.
    """
    def get(self, request):
        client_id = request.GET.get('client_id')
        client_secret = request.GET.get('client_secret')
        if not client_id or not client_secret:
            return HttpResponseBadRequest()

        try:
            Client.objects.get(id=client_id, secret=client_secret, is_active=True)
        except (Client.DoesNotExist, ValueError):
            return HttpResponseForbidden()

        return HttpResponseRedirect(self._authorization_url(request))

    def _authorization_url(self, request):
        """
        Fully formed OAuth2 authorization flow URL, which will be used to redirect the user and then back again.
        """
        raise NotImplementedError


class OAuthCompleteLoginView(View):
    """
    Completes the OAuth2 flow by accepting the `code` in query string and using it to exchange for an access token,
    which is then to be used for provider's user information API.

    If everything goes right it creates or updates a user based on provider's user information and writes a
    JWT token tied with this user to the response.

    Concrete implementations should be used instead of this.
    """
    def get(self, request):
        code = request.GET.get('code')
        if not code:
            return HttpResponseBadRequest()

        user_info = self._retrieve_user_info(request, code)
        if not user_info:
            return HttpResponseBadRequest()
        user = self._get_user(user_info)
        if user:
            if not user.is_active:
                return HttpResponseForbidden()
            serializer = UserSerializer(user, data=user_info)
        else:
            serializer = UserSerializer(data=user_info)
        if not serializer.is_valid():
            return HttpResponseBadRequest('Invalid user data', content_type='text/plain')
        user = serializer.save()

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        return HttpResponse(token, content_type='text/plain')

    def _retrieve_user_info(self, request, code):
        """
        Returns a dict of fields required by the User model.

        The implementation retrieves an OAuth2 token using the given `code` and, which is used in order to obtain
        the user information from the provider-specific API.
        """
        raise NotImplementedError

    def _get_user(self, user_info):
        raise NotImplementedError


class BankIDUserInfoMixin(object):
    """
    Provides routines common to different BankID providers.
    """
    user_info_declaration = {
        'type': 'physical',
        'fields': ['firstName', 'middleName', 'lastName', 'phone', 'inn', 'birthDay', 'email'],
        'documents': [
            {
                'type': 'passport',
                'fields': ['series', 'number']
            }
        ]
    }

    def _map_user_info(self, user_info):
        """
        Maps BankID user info to internally digestible format. To be used with `_retrieve_user_info` method.
        """
        customer = user_info['customer']
        try:
            passport = list(filter(lambda x: x['type'] == 'passport', customer['documents']))[0]
        except (IndexError, KeyError):
            # Failing softly here, let validation do it's job later
            passport = None

        return {
            'first_name': customer['firstName'],
            'middle_name': customer.get('middleName', ''),
            'last_name': customer['lastName'],
            'email': customer.get('email', ''),
            'inn': customer.get('inn', ''),
            # Birthday is required but due to some glitches with BankID atm this is temporarily worked around
            'dob': datetime.strptime(customer['birthDay'], '%d.%m.%Y').date() if 'birthDay' in customer else datetime.today().date(),
            'passport': '{} {}'.format(passport['series'], passport['number']) if passport else ''
        }

    def _get_user(self, user_info):
        try:
            user = User.objects.get(passport=user_info['passport'])
        except User.DoesNotExist:
            user = None
        return user

    def _retrieve_user_info(self, request, code):
        try:
            user_info = self._bankid_user_info(request, code)
        except BankIdError:
            logger.exception('Retrieving BankID info for code "%s" failed', code)
            return None
        return self._map_user_info(user_info)


class OschadBankOAuthLoginView(OAuthLoginView):
    def _authorization_url(self, request):
        redirect_url = request.build_absolute_uri(reverse('profiles>complete_login>oschadbank'))
        return oschad_bankid.authorization_url(redirect_url)


class PrivatBankOAuthLoginView(OAuthLoginView):
    def _authorization_url(self, request):
        redirect_url = request.build_absolute_uri(reverse('profiles>complete_login>privatbank'))
        return privat_bankid.authorization_url(redirect_url)


class DummyOAuthLoginView(OAuthLoginView):
    """Temporary view for testing purposes only (should be replaced with proper unit tests later on)"""
    def _authorization_url(self, request):
        return '{}?code=dummy'.format(request.build_absolute_uri(reverse('profiles>complete_login>dummy')))


class OschadBankOAuthCompleteLoginView(BankIDUserInfoMixin, OAuthCompleteLoginView):
    def _bankid_user_info(self, request, code):
        redirect_url = request.build_absolute_uri(reverse('profiles>complete_login>oschadbank'))
        token = oschad_bankid.retrieve_access_token(code, redirect_url)
        user_info = oschad_bankid.user_info(token, self.user_info_declaration)
        user_info['provider_type'] = OSCHAD_BANKID
        return user_info


class PrivatBankOAuthCompleteLoginView(BankIDUserInfoMixin, OAuthCompleteLoginView):
    def _bankid_user_info(self, request, code):
        redirect_url = request.build_absolute_uri(reverse('profiles>complete_login>privatbank'))
        token = privat_bankid.retrieve_access_token(code, redirect_url)
        user_info = privat_bankid.user_info(token, self.user_info_declaration)
        user_info['provider_type'] = PRIVAT_BANKID
        return user_info


class DummyOAuthCompleteLoginView(BankIDUserInfoMixin, OAuthCompleteLoginView):
    """Temporary view for testing purposes only (should be replaced with proper unit tests later on)"""
    def _retrieve_user_info(self, code):
        # This is my "Lenna", no offense ;)
        return {
            'first_name': 'Aivaras',
            'middle_name': '',
            'last_name': 'Abromavičius',
            'email': 'aivaras@abromavichius.com',
            'inn': '1112618222',
            'dob': datetime.strptime('21.01.1976', '%d.%m.%Y').date(),
            'passport': 'AA 123456',
            'provider_type': ''
        }
