from rest_framework import exceptions

from .models import Client


class ClientAuthMixin:
    def _get_client(self, request):
        client_id = request.GET.get('client_id')
        client_secret = request.GET.get('client_secret')
        timestamp = request.GET.get('timestamp')
        if not client_id or not client_secret or not timestamp:
            raise exceptions.NotAuthenticated()

        try:
            client = Client.objects.get(id=client_id, is_active=True)
            client.verify_secret(client_secret, timestamp, raise_exception=True)
        except (Client.DoesNotExist, ValueError):
            raise exceptions.AuthenticationFailed()

        return client


class UserObjectMixin:
    def get_object(self):
        user = self.request.user
        self.check_object_permissions(self.request, user)

        return user


class ClaimCreateMixin:
    def perform_create(self, serializer):
        # Currently DRF doesn't seem to pass lists of files into the validated data, hence this explicit way
        image_files = []
        if self.request.FILES:
            image_files = self.request.FILES.getlist('images')
        serializer.save(image_files=image_files)
