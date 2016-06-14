import requests

from urllib.parse import urljoin

from .base import BaseBankIdClient


class OschadBankId(BaseBankIdClient):
    """
    Oschadbank-specific BankID client.
    """

    default_authorization_base_url = 'https://id.bank.gov.ua/v1/bank/oauth2/authorize'
    default_api_base_url = 'https://id.bank.gov.ua/v1/'
    token_endpoint = 'bank/oauth2/token'

    def user_info(self, token, declaration):
        headers = {
            'Authorization': 'Bearer {}'.format(token.access_token),
            'Accept': 'application/json'
        }
        response = requests.post(urljoin(self.api_base_url, 'bank/resource/client'),
                                 json=declaration,
                                 headers=headers)
        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            self._handle_errors(response)
