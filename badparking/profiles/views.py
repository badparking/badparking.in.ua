from urllib.parse import urlencode
from datetime import datetime

from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.conf import settings
from django.views.generic import View
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model

from rest_framework_jwt.settings import api_settings

from mobile_api.models import Client
from .serializers import UserSerializer

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
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
            return HttpResponseForbidden()

        try:
            Client.objects.get(id=client_id, secret=client_secret, is_active=True)
        except Client.DoesNotExist:
            return HttpResponseForbidden()

        return HttpResponseRedirect(self._authorization_url)

    @property
    def _authorization_url(self):
        """
        Fully formed OAuth2 authorization flow URL, which will be used to redirect the user and then back again.
        """
        raise NotImplemented


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

        user_info = self._retrieve_user_info(code)
        user = self._get_user(user_info)
        if user:
            if not user.is_active:
                return HttpResponseForbidden()
            serializer = UserSerializer(user, data=user_info)
        else:
            serializer = UserSerializer(data=user_info)
        # TODO: show some useful error message instead of exception throwing
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        return HttpResponse(token, content_type='text/plain')

    def _retrieve_user_info(self, code):
        """
        Returns a dict of fields required by the User model.

        The implementation retrieves an OAuth2 token using the given `code` and, which is used in order to obtain
        the user information from the provider-specific API.
        """
        raise NotImplemented

    def _get_user(self, user_info):
        raise NotImplemented


class BankIDUserInfoMixin(object):
    """
    Provides routines common to different BankID providers.
    """
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
            'email': customer['email'],
            'inn': customer.get('inn', ''),
            'dob': datetime.strptime(customer['birthDay'], '%d.%m.%Y').date(),
            'passport': '{} {}'.format(passport['series'], passport['number']) if passport else ''
        }

    def _get_user(self, user_info):
        try:
            user = User.objects.get(passport=user_info['passport'])
        except User.DoesNotExist:
            user = None
        return user


class OschadBankOAuthLoginView(OAuthLoginView):
    @property
    def _authorization_url(self):
        args = {
            'client_id': settings.BANKID_OSCHADBANK['client_id'],
            'redirect_uri': reverse('profiles>complete_login>oschadbank')
        }
        return 'https://bankid.oschadbank.ua/v1/bank/oauth2/authorize?{}'.format(urlencode(args))


class PrivatBankOAuthLoginView(OAuthLoginView):
    @property
    def _authorization_url(self):
        args = {
            'client_id': settings.BANKID_PRIVATBANK['client_id'],
            'redirect_uri': reverse('profiles>complete_login>privatbank')
        }
        return 'https://bankid.privatbank.ua/DataAccessService/das/authorize?{}'.format(urlencode(args))


class DummyOAuthLoginView(OAuthLoginView):
    """Temporary view for testing purposes only (should be replaced with proper unit tests later on)"""
    @property
    def _authorization_url(self):
        return '{}?code=dummy'.format(reverse('profiles>complete_login>dummy'))


class OschadBankOAuthCompleteLoginView(BankIDUserInfoMixin, OAuthCompleteLoginView):
    def _retrieve_user_info(self, code):
        # TODO: integration point with Oschad BankID user info API
        raise NotImplemented


class PrivatBankOAuthCompleteLoginView(BankIDUserInfoMixin, OAuthCompleteLoginView):
    def _retrieve_user_info(self, code):
        # TODO: integration point with Privat BankID user info API
        raise NotImplemented


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
            'provider': ''
        }
