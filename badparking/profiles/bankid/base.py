import requests

from urllib.parse import urlencode, urljoin
from collections import namedtuple

from .exceptions import BankIdError

Token = namedtuple('Token', ['access_token', 'refresh_token', 'expires_in', 'token_type'])


class BaseBankIdClient(object):
    """
    Base BankID client class, which contains common functionality for all BankID providers.
    Constructor expects a `client_id` and `client_secret` for all providers. Some providers may introduce
    additional arguments. Optionally following keyword arguments may be provided:
        authorization_base_url: URL to be used for authorization grant step
        api_base_url: Base URL for the API requests not related to authorization step

    Public methods may raise `BankIdError` exception for specific BankID errors.
    """

    default_authorization_base_url = NotImplemented
    default_api_base_url = NotImplemented
    token_endpoint = NotImplemented

    def __init__(self, client_id, client_secret, **kwargs):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_base_url = kwargs.get('authorization_base_url', self.default_authorization_base_url)
        self.api_base_url = kwargs.get('api_base_url', self.default_api_base_url)

    def authorization_url(self, redirect_url):
        """
        Returns authorization grant step URL with `redirect_url` encoded into it to be returned to after auth.
        """
        args = (
            ('client_id', self.client_id),
            ('redirect_uri', redirect_url),
            ('response_type', 'code'),
        )
        return '{}?{}'.format(self.authorization_base_url, urlencode(args))

    def retrieve_access_token(self, code, redirect_url):
        """
        Returns `Token` instance with OAuth2 access and refresh tokens obtained by the given `code`.
        `redirect_url` MUST match the one used for `authorization_url`.
        """
        response = requests.post(urljoin(self.api_base_url, self.token_endpoint), data={
            'code': code,
            'client_id': self.client_id,
            'client_secret': self._client_secret(code),
            'redirect_uri': redirect_url,
            'grant_type': 'authorization_code'
        })
        if response.status_code == requests.codes.ok:
            data = response.json()
            return Token(data['access_token'], data['refresh_token'], data['expires_in'], data['token_type'])
        else:
            self._handle_errors(response)

    def refresh_access_token(self, token):
        """
        Refreshes the OAuth2 access token and returns a new one.
        Note: can be used only once for a new token. Refreshed token does not contain a `refresh_token` anymore.
        """
        assert token.refresh_token is not None
        response = requests.post(urljoin(self.api_base_url, self.token_endpoint), data={
            'client_id': self.client_id,
            'client_secret': self._client_secret(token.refresh_token),
            'refresh_token': token.refresh_token,
            'grant_type': 'refresh_token'
        })
        if response.status_code == requests.codes.ok:
            data = response.json()
            return Token(data['access_token'], None, data['expires_in'], data['token_type'])
        else:
            self._handle_errors(response)

    def user_info(self, token, declaration):
        """
        Calls the BankID provider to obtain the user information by given `token` and fields `declaration`.
        """
        raise NotImplementedError

    def _client_secret(self, code):
        return self.client_secret

    def _handle_errors(self, response):
        try:
            error = response.json()
            raise BankIdError(error.get('error'), error.get('error_description'))
        except ValueError:
            raise BankIdError(code=response.status_code, description='Unknown error')
