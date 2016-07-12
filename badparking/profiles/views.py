import logging

from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, HttpResponseBadRequest, Http404
from django.views.generic import View
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.apps import apps
from django.conf import settings

from mobile_api.models import Client
from .serializers import UserSerializer, InnUserSerializer
from .constants import OSCHAD_BANKID, PRIVAT_BANKID
from .bankid import BankIdError
from .jwt import jwt_from_user

logger = logging.getLogger(__name__)
oschad_bankid = apps.get_app_config('profiles').oschad_bankid
privat_bankid = apps.get_app_config('profiles').privat_bankid
User = get_user_model()


class OAuthLoginView(View):
    """
    Initiates the OAuth2 authorization flow.
    Additionally requires `client_id` and hashed `client_secret` query string params corresponding to an active
    `mobile_api.models.Client` to be present for client authentication.

    `client_secret` is a value of the secret hashed with current UTC `timestamp` in seconds as
    SHA256(secret + timestamp).

    Concrete implementations should be used instead of this.
    """
    def get(self, request):
        client_id = request.GET.get('client_id')
        client_secret = request.GET.get('client_secret')
        timestamp = request.GET.get('timestamp')
        if not client_id or not client_secret or not timestamp:
            return HttpResponseBadRequest()

        try:
            client = Client.objects.get(id=client_id, is_active=True)
            client.verify_secret(client_secret, timestamp, raise_exception=True)
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
    user_serializer = UserSerializer

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
            serializer = self._get_serializer(user, data=user_info, partial=True)
        else:
            serializer = self._get_serializer(data=user_info)
        if not serializer.is_valid():
            logger.error(serializer.errors)
            return HttpResponseBadRequest('Invalid user data', content_type='text/plain')
        user = serializer.save()
        token = jwt_from_user(user)

        response = HttpResponse('Authentication complete', content_type='text/plain')
        response['X-JWT'] = token
        return response

    def _get_serializer(self, *args, **kwargs):
        return self.user_serializer(*args, **kwargs)

    def _retrieve_user_info(self, request, code):
        """
        Returns a dict of fields required by the User model.

        The implementation retrieves an OAuth2 token using the given `code` and, which is used in order to obtain
        the user information from the provider-specific API.
        """
        raise NotImplementedError

    def _get_user(self, user_info):
        raise NotImplementedError


class BankIDUserInfoMixin:
    """
    Provides routines common to different BankID providers.
    """
    user_serializer = InnUserSerializer
    user_info_declaration = {
        'type': 'physical',
        'fields': ['firstName', 'middleName', 'lastName', 'phone', 'inn', 'email'],
    }

    def _map_user_info(self, user_info):
        """
        Maps BankID user info to internally digestible format. To be used with `_retrieve_user_info` method.
        """
        customer = user_info['customer']
        data = {
            'first_name': customer.get('firstName', ''),
            'middle_name': customer.get('middleName', ''),
            'last_name': customer.get('lastName', ''),
            'inn': customer.get('inn', '')
        }
        # These fields may be overridden by the user and we don't want them to be emptied on re-login
        if customer.get('email', None):
            data['email'] = customer['email']
        if customer.get('phone', None):
            data['phone'] = customer['phone']
        return data

    def _get_user(self, user_info):
        if 'inn' not in user_info:
            # INN is required but let validation handle it
            return None

        try:
            user = User.objects.get_by_inn(user_info['inn'], user_info.get('email', None))
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
    """
    Debug mode only view for quickly testing the auth flow manually.

    Note: this view bypasses the client check and MUST only be used in debug mode.
    """
    def get(self, request):
        if not settings.DEBUG:
            raise Http404()

        return HttpResponseRedirect(self._authorization_url(request))

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
    """Debug mode only view for quickly testing completion of the auth flow manually."""
    def get(self, request):
        if not settings.DEBUG:
            raise Http404()

        return super(DummyOAuthCompleteLoginView, self).get(request)

    def _retrieve_user_info(self, request, code):
        # This is my "Lenna", no offense ;)
        return {
            'first_name': 'Aivaras',
            'middle_name': '',
            'last_name': 'Abromavičius',
            'email': 'aivaras@abromavichius.com',
            'inn': '1112618222',
            'phone': '+380961234511',
            'provider_type': OSCHAD_BANKID
        }
