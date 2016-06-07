from django.core.management.base import BaseCommand

from core.models import Claim
from core.constants import CLAIM_ACTIVE_STATUSES


CLAIM_BATCH_SIZE = 100


class Command(BaseCommand):
    help = 'Scans for active claims and updates their states from the police feedback'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Do not save the claims',
        )

    def handle(self, *args, **options):
        qs = Claim.objects.filter(status__in=CLAIM_ACTIVE_STATUSES)
        total = qs.count()
        self.stdout.write('Querying {} claims'.format(total))
        # Ask for feedback in batches to avoid overburdening the services
        for start in range(0, total, CLAIM_BATCH_SIZE):
            end = min(start + CLAIM_BATCH_SIZE, total)
            claims = {c.pk: c for c in qs[start:end]}
            for feedback in self._retrieve_feedback(map(lambda x: x.pk, claims)):
                claim = claims.get(feedback['id'], None)
                if claim and claim.status != feedback['status']:
                    if not options['dry_run']:
                        claim.log_state(status=feedback['status'], description=feedback.get('description', ''))
                    self.stdout.write('{} changed status to {}'.format(str(claim), feedback['status']))

    def _retrieve_feedback(self, claim_ids):
        # TODO: retrieve and process actual feedback from the police interface when there are details
        return [
            {'id': 1, 'status': 'accepted'},
            {'id': 2, 'status': 'in_progress', 'description': 'Police car #1111 was dispatched'}
        ]
