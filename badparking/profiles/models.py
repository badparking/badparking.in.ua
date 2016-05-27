from django.db import models
from django.contrib.auth.models import AbstractUser

from .constants import PROFILE_PROVIDERS


class User(AbstractUser):
    middle_name = models.CharField(max_length=255, blank=True)
    dob = models.DateField(blank=True, null=True)
    inn = models.CharField(max_length=255, blank=True, db_index=True)
    phone = models.CharField(max_length=255, blank=True)
    provider_type = models.CharField(max_length=255, choices=PROFILE_PROVIDERS, blank=True)

    def get_full_name(self):
        full_name = self.first_name
        if self.middle_name:
            full_name += ' {}'.format(self.middle_name)
        return '{} {}'.format(full_name, self.last_name)

    def is_complete(self):
        """
        Checks if user profile is complete and ready to register claims.
        """
        return bool(self.get_full_name() and self.dob and self.inn and self.phone)

    def __str__(self):
        return '<User: {}, {}>'.format(self.get_full_name(), self.inn)
