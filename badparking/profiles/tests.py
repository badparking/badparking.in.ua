import time

from datetime import date
from unittest.mock import patch
from urllib.parse import urlencode
from hashlib import sha256

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.conf import settings

from rest_framework_jwt.settings import api_settings

from mobile_api.models import Client

from .serializers import InnUserSerializer
from .constants import PRIVAT_BANKID, OSCHAD_BANKID
from .views import OschadBankOAuthCompleteLoginView, PrivatBankOAuthCompleteLoginView, BankIDUserInfoMixin


User = get_user_model()
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER


class UserSerializerTests(TestCase):
    fixtures = ['test-data']

    @classmethod
    def setUpTestData(cls):
        cls.deserialization_data = {
            'first_name': 'ЄВГЕН',
            'middle_name': 'МИКОЛАЙОВИЧ',
            'last_name': 'САЛО',
            'email': 'eugene.salo@email.com',
            'inn': '1112618111',
            'phone': '+380961234511',
            'provider_type': OSCHAD_BANKID
        }

    def test_serialization_success(self):
        user = User.objects.get_by_inn('1112618222')
        serializer = InnUserSerializer(user)
        self.assertEqual(dict(serializer.data), {
            'first_name': 'Aivaras',
            'middle_name': '',
            'last_name': 'Abromavičius',
            'email': 'aivaras@abromavichius.com',
            'full_name': 'Aivaras Abromavičius',
            'inn': '1112618222',
            'phone': '+380961234511',
            'is_complete': True
        })

    def test_deserialization_success(self):
        serializer = InnUserSerializer(data=self.deserialization_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertIsInstance(user, User)
        self.assertEqual(user.inn, '1112618111')
        self.assertEqual(user.external_id, '1112618111')
        self.assertTrue(user.is_complete())

    def test_deserialization_validation_failure(self):
        data = {
            'first_name': '',
            'middle_name': 'Олексійович',
            'last_name': '',
            'email': 'me@.gov.ua',
            'inn': '1111111111',
            'phone': '',
            'provider_type': OSCHAD_BANKID
        }
        serializer = InnUserSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class OAuthViewsTests(TestCase):
    fixtures = ['test-data']

    @classmethod
    def setUpTestData(cls):
        cls.api_client = Client.objects.get(id='9a6291c1-ef6d-4d81-b6dd-a1699b4b78f0')

    def _make_api_creds(self, api_client, timestamp=None):
        if timestamp is None:
            timestamp = str(int(time.time()))
        secret_hash = sha256(api_client.secret.encode('utf8') + timestamp.encode('utf8')).hexdigest()
        return {'client_id': api_client.id, 'client_secret': secret_hash, 'timestamp': timestamp}

    def _complete_bankid_flow(self, view, complete_url, extra_user_info=None, test_failure=False):
        user_info = {
            'first_name': 'ЄВГЕН',
            'middle_name': 'МИКОЛАЙОВИЧ',
            'last_name': 'САЛО',
            'email': 'eugene.salo@email.com',
            'inn': '1112618111',
            'phone': '+380961234511'
        }
        if extra_user_info:
            user_info.update(extra_user_info)

        with patch.object(view, '_retrieve_user_info', return_value=user_info) as mock_method:
            response = self.client.get(complete_url, {'code': 'testcode'})
            mock_method.assert_called_once_with(response.wsgi_request, 'testcode')
            if test_failure:
                return response

            # Check basic response info
            self.assertEqual(response.status_code, 200)
            self.assertTrue('X-JWT' in response)

            # Check user exists
            user = User.objects.get_by_inn(user_info['inn'])
            self.assertEqual(user.inn, user_info['inn'])

            # Check returned JWT token is valid and contains this user in the payload
            payload = jwt_decode_handler(response['X-JWT'])
            self.assertEqual(payload['email'], user.email)
            self.assertEqual(payload['username'], user.username)
            self.assertEqual(payload['full_name'], user.get_full_name())
            self.assertEqual(payload['is_complete'], user.is_complete())

        return user

    def test_oschadbank_full_flow(self):
        response = self.client.get(reverse('profiles>login>oschadbank'), self._make_api_creds(self.api_client))

        complete_url = reverse('profiles>complete_login>oschadbank')
        redirect_uri = urlencode({'redirect_uri': 'http://testserver{}'.format(complete_url)})
        expected_url = 'https://id.bank.gov.ua/v1/bank/oauth2/authorize?client_id={}&{}&response_type=code'\
            .format(settings.BANKID_OSCHADBANK['client_id'], redirect_uri)
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)

        user = self._complete_bankid_flow(OschadBankOAuthCompleteLoginView, complete_url,
                                          extra_user_info={'provider_type': OSCHAD_BANKID})
        self.assertEqual(user.provider_type, OSCHAD_BANKID)

    def test_privatbank_full_flow(self):
        response = self.client.get(reverse('profiles>login>privatbank'), self._make_api_creds(self.api_client))

        complete_url = reverse('profiles>complete_login>privatbank')
        redirect_uri = urlencode({'redirect_uri': 'http://testserver{}'.format(complete_url)})
        expected_url = 'https://bankid.privatbank.ua/DataAccessService/das/authorize?client_id={}&{}&response_type=code'\
            .format(settings.BANKID_PRIVATBANK['client_id'], redirect_uri)
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)

        user = self._complete_bankid_flow(PrivatBankOAuthCompleteLoginView, complete_url,
                                          extra_user_info={'provider_type': PRIVAT_BANKID})
        self.assertEqual(user.provider_type, PRIVAT_BANKID)

    def test_missing_client_params(self):
        for view_name in ('profiles>login>oschadbank', 'profiles>login>privatbank'):
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 400)
            response = self.client.get(reverse(view_name), {'client_id': 'dummy'})
            self.assertEqual(response.status_code, 400)
            response = self.client.get(reverse(view_name), {'client_secret': 'dummy'})
            self.assertEqual(response.status_code, 400)

    def test_invalid_client(self):
        for view_name in ('profiles>login>oschadbank', 'profiles>login>privatbank'):
            response = self.client.get(reverse(view_name),
                                       {'client_id': 'dummy', 'client_secret': 'dummy', 'timestamp': '12345'})
            self.assertEqual(response.status_code, 403)

    def test_invalid_client_timestamp(self):
        for view_name in ('profiles>login>oschadbank', 'profiles>login>privatbank'):
            future_timestamp = str(time.time() + settings.API_CLIENT_TIMESTAMP_THRESHOLD + 1)
            response = self.client.get(reverse(view_name), self._make_api_creds(self.api_client, future_timestamp))
            self.assertEqual(response.status_code, 403)

    def test_incoherent_client_secret(self):
        for view_name in ('profiles>login>oschadbank', 'profiles>login>privatbank'):
            # Check that using a valid hash with a different timestamp doesn't authenticate
            creds = self._make_api_creds(self.api_client)
            creds['timestamp'] = str(time.time() + 1)
            response = self.client.get(reverse(view_name), creds)
            self.assertEqual(response.status_code, 403)

    def test_missing_auth_code(self):
        for view_name in ('profiles>complete_login>oschadbank', 'profiles>complete_login>privatbank'):
            response = self.client.get(reverse(view_name))
            self.assertEqual(response.status_code, 400)

    def test_update_complete(self):
        complete_url = reverse('profiles>complete_login>oschadbank')
        extra_user_info = {
            'first_name': 'Aivaras',
            'middle_name': 'Patronymic',
            'last_name': 'Abromavičius',
            'email': 'aivaras@abromavichius.com',
            'inn': '1112618222',
            'phone': '+380961234512',
            'provider_type': OSCHAD_BANKID
        }
        user = User.objects.get_by_inn(extra_user_info['inn'])
        self.assertEqual(user.middle_name, '')
        self.assertEqual(user.provider_type, PRIVAT_BANKID)
        user = self._complete_bankid_flow(OschadBankOAuthCompleteLoginView, complete_url,
                                          extra_user_info=extra_user_info)
        self.assertEqual(user.middle_name, 'Patronymic')
        self.assertEqual(user.provider_type, OSCHAD_BANKID)

    def test_update_inactive(self):
        complete_url = reverse('profiles>complete_login>oschadbank')
        extra_user_info = {
            'first_name': 'Inactive',
            'middle_name': '',
            'last_name': 'User',
            'email': 'inactive@user.com',
            'inn': '1112618223',
            'phone': '',
            'provider_type': OSCHAD_BANKID
        }
        user = User.objects.get_by_inn(extra_user_info['inn'])
        self.assertFalse(user.is_active)
        response = self._complete_bankid_flow(OschadBankOAuthCompleteLoginView, complete_url,
                                              extra_user_info=extra_user_info, test_failure=True)
        self.assertEqual(response.status_code, 403)

    def test_validation_failure(self):
        complete_url = reverse('profiles>complete_login>oschadbank')
        extra_user_info = {
            'first_name': 'Invalid',
            'middle_name': '',
            'last_name': '',
            'email': 'invalid@.com',
            'inn': '',
            'phone': '',
            'provider_type': OSCHAD_BANKID
        }
        response = self._complete_bankid_flow(OschadBankOAuthCompleteLoginView, complete_url,
                                              extra_user_info=extra_user_info, test_failure=True)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Invalid user data')

    def test_bankid_userinfo_map(self):
        # Truncated example from BankID docs
        bankid_data = {
            'state': 'ok',
            'customer': {
                'type': 'physical',
                'inn': '1112618222',
                'birthDay': '20.01.1973',
                'clId': '46378c05eb48127552e60cffd086e6e34287ff04',
                'firstName': 'ЄВГЕН',
                'lastName': 'САЛО',
                'middleName': 'МИКОЛАЙОВИЧ',
                'phone': '+380681231212',
                'signature': 'bad3419d8f4aee6945636e8b3fe7e492798e4564',
                'documents': [
                    {
                        'type': 'passport',
                        'series': 'ШО',
                        'number': '123456',
                        'issue': 'ДНЕПРОПЕТРОВСКИМ РО УМВД',
                        'dateIssue': '11.06.1997',
                        'issueCountryIso2': 'UA',
                        'dateModification': '29.05.2014 17:52:25'
                    }
                ],
            }
        }
        expected_data = {
            'first_name': 'ЄВГЕН',
            'middle_name': 'МИКОЛАЙОВИЧ',
            'last_name': 'САЛО',
            'inn': '1112618222',
            'phone': '+380681231212'
        }
        obj = BankIDUserInfoMixin()
        self.assertEqual(obj._map_user_info(bankid_data), expected_data)

    def test_dummy_auth_only_in_debug(self):
        with self.settings(DEBUG=False):
            response = self.client.get(reverse('profiles>login>dummy'))
            self.assertEqual(response.status_code, 404)

            response = self.client.get(reverse('profiles>complete_login>dummy'))
            self.assertEqual(response.status_code, 404)
