import time

from uuid import uuid4
from hmac import compare_digest
from hashlib import sha256

from django.db import models
from django.conf import settings
from django.contrib.auth.models import Permission


class Client(models.Model):
    """
    API client.
    To be used with API client authentication, where `client_id` is `id` and `client_secret` is `secret`.
    """
    id = models.UUIDField(primary_key=True, default=uuid4)
    secret = models.CharField(max_length=255)  # TODO: generate a good default here
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return '<Client: {} - {}>'.format(self.id, self.name)

    def has_perm(self, perm):
        """
        Checks if a `Client` instance has permission specified by `perm`.
        Very basic imitation of Django's permissions model.
        """
        if not self.is_active:
            return False
        return self.permissions.filter(codename=perm).exists()

    def verify_secret(self, hashed_secret, timestamp, raise_exception=False):
        """
        Verifies that given `hash_secret` corresponds to client's `secret` hashed with the given `timestamp`, which
        in turn is within the configured threshold.

        If `raise_exception` is `True` failure to verify will raise `ValueError`, otherwise it returns a boolean.
        """
        # First, validate the timestamp with a drift threshold
        timestamp_int = int(timestamp)
        lapsed = int(time.time()) - timestamp_int
        if abs(lapsed) > settings.API_CLIENT_TIMESTAMP_THRESHOLD:
            if raise_exception:
                raise ValueError('Timestamp is expired')
            else:
                return False

        # Compute a SHA256 hash of client secret with the timestamp value and securely compare with given hash value
        verified = compare_digest(hashed_secret,
                                  sha256(self.secret.encode('utf8') + timestamp.encode('utf8')).hexdigest())
        if not verified and raise_exception:
            raise ValueError('Secret does not match')
        return verified
