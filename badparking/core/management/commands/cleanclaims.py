from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Claim


class Command(BaseCommand):
    help = 'Cleans up old unauthorized claims'

    def add_arguments(self, parser):
        parser.add_argument('days_old', type=int)
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Do not delete the claims',
        )

    def handle(self, *args, **options):
        qs = Claim.objects.unauthorized().filter(created_at__lte=timezone.now() - timedelta(days=options['days_old']))
        self.stdout.write('Found {} unautorized claims older than {} days for the clean up'
                          .format(qs.count(), options['days_old']))
        if not options['dry_run']:
            qs.delete()
