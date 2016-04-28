from uuid import uuid4

from django.db import models


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

    def __str__(self):
        return '<Client: {} - {}>'.format(self.id, self.name)
