# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-26 17:22
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0006_auto_20160626_2017'),
    ]

    operations = [
        migrations.CreateModel(
            name='Claim',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('license_plates', models.CharField(blank=True, max_length=50, verbose_name='Номери автомобілів')),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='Довгота')),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='Широта')),
                ('city', models.CharField(blank=True, db_index=True, max_length=255, verbose_name='Місто')),
                ('address', models.CharField(blank=True, max_length=255, verbose_name='Адреса')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('authorized_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('status', models.CharField(choices=[('enqueued', 'Enqueued'), ('accepted', 'Accepted by police'), ('in_progress', 'In progress'), ('complete', 'Complete'), ('invalid', 'Invalid'), ('canceled', 'Canceled')], db_index=True, default='enqueued', max_length=255)),
                ('crimetypes', models.ManyToManyField(to='core.CrimeType', verbose_name='Порушення')),
                ('images', models.ManyToManyField(blank=True, to='media.MediaFileModel', verbose_name='Зображення')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='claims', to=settings.AUTH_USER_MODEL, verbose_name='Користувач')),
            ],
            options={
                'permissions': (('can_list_all_claims', 'Can list all claims'),),
                'verbose_name': 'Скарга',
                'verbose_name_plural': 'Скарги',
            },
        ),
        migrations.CreateModel(
            name='ClaimState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('enqueued', 'Enqueued'), ('accepted', 'Accepted by police'), ('in_progress', 'In progress'), ('complete', 'Complete'), ('invalid', 'Invalid'), ('canceled', 'Canceled')], max_length=255)),
                ('description', models.TextField(blank=True)),
                ('logged_at', models.DateTimeField(auto_now_add=True)),
                ('claim', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='states', to='core.Claim')),
            ],
        ),
    ]
