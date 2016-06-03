from django.core.management.base import BaseCommand

from mobile_api.models import Client


class Command(BaseCommand):
    help = 'List all available API clients'

    def handle(self, *args, **options):
        clients_str = '\n'.join(map(str, Client.objects.all()))
        self.stdout.write(clients_str)
