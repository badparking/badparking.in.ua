from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager

from .constants import PROFILE_PROVIDERS, FACEBOOK, OSCHAD_BANKID, PRIVAT_BANKID


class UserManager(DjangoUserManager):
    use_in_migrations = True

    def get_by_facebook_id(self, external_id, email=None):
        return self.get_queryset().get(
            self._get_filters(external_id, [FACEBOOK], email))

    def get_by_inn(self, inn, email=None):
        return self.get_queryset().get(
            self._get_filters(inn, [OSCHAD_BANKID, PRIVAT_BANKID], email))

    def _get_filters(self, external_id, providers, email):
        filters = models.Q(external_id=external_id) & models.Q(provider_type__in=providers)
        if email:
            filters |= models.Q(email=email)
        return filters


class User(AbstractUser):
    middle_name = models.CharField(max_length=255, blank=True)
    inn = models.CharField(max_length=255, blank=True, db_index=True)
    phone = models.CharField(max_length=255, blank=True)
    provider_type = models.CharField(max_length=255, choices=PROFILE_PROVIDERS, blank=True, db_index=True)
    external_id = models.CharField(max_length=255, blank=True, db_index=True)

    objects = UserManager()

    def get_full_name(self):
        full_name = self.first_name
        if self.middle_name:
            full_name += ' {}'.format(self.middle_name)
        return '{} {}'.format(full_name, self.last_name)

    def is_complete(self):
        """
        Checks if user profile is complete and ready to register claims.
        """
        return bool(self.get_full_name() and self.phone)

    def __str__(self):
        return '<User: {}, {}>'.format(self.get_full_name(), self.email)
