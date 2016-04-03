from django.db import models


class CrimeType(models.Model):
    name = models.CharField("Тип порушення", max_length=255)
    enabled = models.BooleanField("Увімкнено", default=False, db_index=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Тип порушення"
        verbose_name_plural = "Типи порушень"
