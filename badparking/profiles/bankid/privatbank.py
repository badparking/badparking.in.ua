import requests

from hashlib import sha1
from base64 import b64decode
from urllib.parse import urljoin
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from .base import BaseBankIdClient
from .exceptions import BankIdError


class PrivatBankId(BaseBankIdClient):
    """
    PrivatBank-specific BankID client.
    Note: in addition to usual arguments its constructor also requires `private_key_path`, which points to
    an absolute path of the private key as approved by the provider.
    """

    default_authorization_base_url = 'https://bankid.privatbank.ua/DataAccessService/das/authorize'
    default_api_base_url = 'https://bankid.privatbank.ua/'
    token_endpoint = 'DataAccessService/oauth/token'

    def __init__(self, client_id, client_secret, private_key_path, **kwargs):
        super(PrivatBankId, self).__init__(client_id, client_secret, **kwargs)
        with open(private_key_path, 'rb') as key_file:
            self.private_key = serialization.load_pem_private_key(key_file.read(), password=None,
                                                                  backend=default_backend())

    def user_info(self, token, declaration):
        headers = {
            'Authorization': 'Bearer {}, Id {}'.format(token.access_token, self.client_id),
            'Accept': 'application/json'
        }
        response = requests.post(urljoin(self.api_base_url, 'ResourceService/checked/data'),
                                 json=declaration, headers=headers)
        if response.status_code == requests.codes.ok:
            data = response.json()
            if data['state'] == 'err':
                raise BankIdError(data.get('code'), data.get('desc'))
            elif data['state'] == 'ok':
                customer = data['customer']
                if 'signature' in customer:
                    data['customer'] = self._decrypt(customer)
                return data
            else:
                raise BankIdError(code=None, description='Unknown response state "{}"'.format(data['state']))
        else:
            self._handle_errors(response)

    def _client_secret(self, code):
        return sha1(self.client_id.encode('utf8') + self.client_secret.encode('utf8') + code.encode('utf8')).hexdigest()

    def _decrypt(self, user_info):
        def recursive_decrypt(value):
            if isinstance(value, list):
                return [recursive_decrypt(v) for v in value]
            elif isinstance(value, dict):
                return {k: (recursive_decrypt(v) if k not in ('type', 'signature') else v) for k, v in value.items()}
            elif isinstance(value, str):
                return self.private_key.decrypt(b64decode(value), padding.PKCS1v15()).decode('utf8')
            else:
                raise BankIdError(code=None, description='Unexpected value for decryption')

        return recursive_decrypt(user_info)
