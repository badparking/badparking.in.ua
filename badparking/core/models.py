from uuid import uuid4

from django.db import models, transaction
from django.conf import settings
from media.models import MediaFileModel

from .constants import CLAIM_STATUS_CHOICES, CLAIM_STATUS_ENQUEUED, CLAIM_STATUS_CANCELED, CLAIM_ACTIVE_STATUSES


class CrimeType(models.Model):
    name = models.CharField("Тип порушення", max_length=255)
    enabled = models.BooleanField("Увімкнено", default=False, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип порушення"
        verbose_name_plural = "Типи порушень"


class ClaimQuerySet(models.QuerySet):
    def authorized(self):
        return self.filter(user__isnull=False)

    def unauthorized(self):
        return self.filter(user__isnull=True)

    def active(self):
        return self.filter(status__in=CLAIM_ACTIVE_STATUSES)


class Claim(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    license_plates = models.CharField("Номери автомобілів", max_length=50, db_index=True)
    longitude = models.DecimalField("Довгота", max_digits=9, decimal_places=6)
    latitude = models.DecimalField("Широта", max_digits=9, decimal_places=6)
    city = models.CharField("Місто", max_length=255, db_index=True)
    address = models.CharField("Адреса", max_length=255)
    created_at = models.DateTimeField(editable=False, auto_now_add=True, db_index=True)
    modified_at = models.DateTimeField(editable=False, auto_now=True)
    authorized_at = models.DateTimeField(editable=False, blank=True, null=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             verbose_name="Користувач",
                             related_name='claims',
                             blank=True, null=True)

    crimetypes = models.ManyToManyField(CrimeType, verbose_name="Порушення")
    images = models.ManyToManyField(MediaFileModel, blank=True, verbose_name="Зображення")
    status = models.CharField(max_length=255, choices=CLAIM_STATUS_CHOICES, default=CLAIM_STATUS_ENQUEUED,
                              db_index=True)

    objects = ClaimQuerySet.as_manager()

    class Meta:
        verbose_name = "Скарга"
        verbose_name_plural = "Скарги"
        permissions = (('can_list_all_claims', 'Can list all claims'),)
        ordering = ['-created_at']

    def __str__(self):
        return '<Claim {} - {} - {}>'.format(self.pk, self.user.pk if self.user else 'Anonymous', self.status)

    def is_cancelable(self):
        return self.status == CLAIM_STATUS_ENQUEUED

    def cancel(self):
        if self.is_cancelable():
            self.status = CLAIM_STATUS_CANCELED
            self.save(update_fields=['status', 'modified_at'])

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
