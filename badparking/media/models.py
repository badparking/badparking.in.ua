from pathlib import Path
from uuid import uuid4
from datetime import datetime

from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill


def generate_upload_path(instance, filename):
    return 'images/{}/{}{}'.format(datetime.now().strftime('%Y/%m/%d'), uuid4().hex, Path(filename).suffix)


class MediaFileModel(models.Model):
    file = models.ImageField(upload_to=generate_upload_path)
    thumbnail = ImageSpecField(source='file',
                               processors=[ResizeToFill(100, 100)],
                               format='JPEG',
                               options={'quality': 60})
    original_filename = models.CharField(max_length=255, default='')
    created_at = models.DateTimeField(editable=False, auto_now_add=True)

    @property
    def size(self):
        return self.file.size

    @property
    def url(self):
        return self.file.url

    def __str__(self):
        return '<{} created at {}>'.format(self.file.name, self.created_at)
