from django.apps import AppConfig
from django.conf import settings

from .bankid import OschadBankId, PrivatBankId


class ProfilesConfig(AppConfig):
    name = 'profiles'

    def ready(self):
        # Load BankID clients once on app load
        if not hasattr(self, 'oschad_bankid'):
            self.oschad_bankid = OschadBankId(**settings.BANKID_OSCHADBANK)
        if not hasattr(self, 'privat_bankid'):
            self.privat_bankid = PrivatBankId(**settings.BANKID_PRIVATBANK)
