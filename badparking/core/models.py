from django.db import models
from django.contrib.auth.models import User
from media.models import MediaFileModel


class CrimeType(models.Model):
    name = models.CharField("Тип порушення", max_length=255)
    enabled = models.BooleanField("Увімкнено", default=False, db_index=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Тип порушення"
        verbose_name_plural = "Типи порушень"


class Claim(models.Model):
    license_plates = models.CharField("Номери автомобілів", max_length=50, blank=True)
    longitude = models.CharField("Довгота", max_length=50, blank=True)
    latitude = models.CharField("Широта", max_length=50, blank=True)
    city = models.CharField("Місто", max_length=30, blank=True)
    address = models.CharField("Адреса", max_length=150, blank=True)
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    user = models.ForeignKey(User, verbose_name="Користувач")
    crimetypes = models.ManyToManyField(CrimeType, verbose_name="Порушення")
    images = models.ManyToManyField(MediaFileModel, blank=True, verbose_name="Зображення")

    def __unicode__(self):
        return self.pk

    class Meta:
        verbose_name = "Скарга"
        verbose_name_plural = "Скарги"
