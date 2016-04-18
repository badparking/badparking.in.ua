from django.db import models
from datetime import datetime


class MediaFileModel(models.Model):
    file = models.ImageField('Зображення', upload_to='images/%Y/%m/%d')
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    @property
    def size(self):
        return self.file.size

    @property
    def url(self):
        return self.file.url

    def __unicode__(self):
        return self.pk

    class Meta:
        verbose_name = "Зображення"
        verbose_name_plural = "Зображення"
