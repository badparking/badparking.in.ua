import time

from hashlib import sha256
from urllib.parse import urlencode

from django.core.management.base import BaseCommand, CommandError

from mobile_api.models import Client


class Command(BaseCommand):
    help = 'Generates a secret hash using current time for a specified client'

    def add_arguments(self, parser):
        parser.add_argument('client_id', type=str)

        parser.add_argument(
            '--url',
            action='store_true',
            dest='url',
            default=False,
            help='Present output in URL-encoded format',
        )

    def handle(self, *args, **options):
        try:
            client = Client.objects.get(pk=options['client_id'])
        except Client.DoesNotExist:
            raise CommandError('Client {} does not exist'.format(options['client_id']))

        timestamp = str(int(time.time()))
        secret_hash = sha256(client.secret.encode('utf8') + timestamp.encode('utf8')).hexdigest()
        if options['url']:
            self.stdout.write(self.style.SUCCESS(urlencode({
                'client_id': client.id,
                'client_secret': secret_hash,
                'timestamp': timestamp
            })))
        else:
            self.stdout.write(self.style.SUCCESS('Secret hash: {}, timestamp: {}'.format(secret_hash, timestamp)))
