from datetime import date

from django.db import models
from django.contrib.auth.models import AbstractUser

from .constants import PROFILE_PROVIDERS


class User(AbstractUser):
    middle_name = models.CharField(max_length=255, blank=True)
    dob = models.DateField(default=date.today)
    # This might be empty, in such case passport should be used, `User.identity` property addresses this
    inn = models.CharField(max_length=255, blank=True, db_index=True)
    passport = models.CharField(max_length=255, blank=True, db_index=True)  # <series number> format
    phone = models.CharField(max_length=255, blank=True)
    provider_type = models.CharField(max_length=255, choices=PROFILE_PROVIDERS, blank=True)

    @property
    def identity(self):
        """
        Username will generally contain the identity but not always, this way it's explicit.
        """
        return self.inn or self.passport

    def get_full_name(self):
        full_name = self.first_name
        if self.middle_name:
            full_name += ' {}'.format(self.middle_name)
        return '{} {}'.format(full_name, self.last_name)

    def __str__(self):
        return '<User: {}, {}>'.format(self.get_full_name(), self.identity)
