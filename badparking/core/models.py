from uuid import uuid4

from django.db import models, transaction
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

from media.models import MediaFileModel

from .constants import CLAIM_STATUS_CHOICES, CLAIM_STATUS_ENQUEUED, CLAIM_STATUS_CANCELED, CLAIM_STATUS_RECEIVED,\
    CLAIM_STATUS_COMPLETE, CLAIM_ACTIVE_STATUSES


class CrimeType(models.Model):
    name = models.CharField(max_length=255)
    enabled = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return self.name


class ClaimQuerySet(models.QuerySet):
    def authorized(self):
        return self.filter(user__isnull=False)

    def unauthorized(self):
        return self.filter(user__isnull=True)

    def active(self):
        return self.filter(status__in=CLAIM_ACTIVE_STATUSES)

    def enqueued(self):
        return self.filter(status=CLAIM_STATUS_ENQUEUED)


class Claim(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    license_plates = models.CharField(max_length=50, db_index=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    city = models.CharField(max_length=255, db_index=True)
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(editable=False, auto_now_add=True, db_index=True)
    modified_at = models.DateTimeField(editable=False, auto_now=True)
    authorized_at = models.DateTimeField(editable=False, blank=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='claims',
                             blank=True, null=True)

    crimetypes = models.ManyToManyField(CrimeType)
    media = models.ManyToManyField(MediaFileModel, blank=True)
    media_filenames = ArrayField(models.CharField(max_length=255), default=list)
    status = models.CharField(max_length=255, choices=CLAIM_STATUS_CHOICES, default=CLAIM_STATUS_RECEIVED,
                              db_index=True)

    objects = ClaimQuerySet.as_manager()

    class Meta:
        permissions = (('can_list_all_claims', 'Can list all claims'),)
        ordering = ['-created_at']

    def __str__(self):
        return '<Claim {} - {} - {}>'.format(self.pk, self.user.pk if self.user else 'Anonymous', self.status)

    def is_cancelable(self):
        return self.status in (CLAIM_STATUS_RECEIVED, CLAIM_STATUS_COMPLETE)

    def is_received(self):
        return self.status == CLAIM_STATUS_RECEIVED

    def try_cancel(self):
        if self.is_cancelable():
            self.log_state(CLAIM_STATUS_CANCELED)

    def try_complete(self):
        if not self.is_received():
            return
        if set(self.media.values_list('original_filename', flat=True)) == set(self.media_filenames):
            self.log_state(CLAIM_STATUS_COMPLETE)

    @transaction.atomic
    def log_state(self, status, description=''):
        self.states.create(status=status, description=description)
        self.status = status
        self.save(update_fields=['status', 'modified_at'])


class ClaimState(models.Model):
    claim = models.ForeignKey(Claim, related_name='states')
    status = models.CharField(max_length=255, choices=CLAIM_STATUS_CHOICES)
    description = models.TextField(blank=True)
    logged_at = models.DateTimeField(editable=False, auto_now_add=True)

    def __str__(self):
        return '<ClaimState {} - {}>'.format(self.claim.pk, self.status)
