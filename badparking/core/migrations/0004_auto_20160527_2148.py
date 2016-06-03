# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-27 18:48
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_claim'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='claim',
            options={'permissions': (('can_list_all_claims', 'Can list all claims'),), 'verbose_name': 'Скарга', 'verbose_name_plural': 'Скарги'},
        ),
        migrations.AddField(
            model_name='claim',
            name='status',
            field=models.CharField(choices=[('enqueued', 'Enqueued'), ('accepted', 'Accepted by police'), ('in_progress', 'In progress'), ('complete', 'Complete'), ('invalid', 'Invalid'), ('canceled', 'Canceled')], db_index=True, default='enqueued', max_length=255),
        ),
        migrations.AlterField(
            model_name='claim',
            name='city',
            field=models.CharField(blank=True, db_index=True, max_length=255, verbose_name='Місто'),
        ),
        migrations.AlterField(
            model_name='claim',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='claims', to=settings.AUTH_USER_MODEL, verbose_name='Користувач'),
        ),
    ]