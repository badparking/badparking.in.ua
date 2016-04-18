# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-16 19:02
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0002_auto_20160404_0115'),
    ]

    operations = [
        migrations.CreateModel(
            name='Claim',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('license_plates', models.CharField(blank=True, max_length=50, verbose_name='Номери автомобілів')),
                ('longitude', models.CharField(blank=True, max_length=50, verbose_name='Довгота')),
                ('latitude', models.CharField(blank=True, max_length=50, verbose_name='Широта')),
                ('city', models.CharField(blank=True, max_length=30, verbose_name='Місто')),
                ('address', models.CharField(blank=True, max_length=150, verbose_name='Адреса')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('crimetypes', models.ManyToManyField(to='core.CrimeType', verbose_name='Порушення')),
                ('images', models.ManyToManyField(blank=True, to='media.MediaFileModel', verbose_name='Зображення')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Користувач')),
            ],
            options={
                'verbose_name': 'Скарга',
                'verbose_name_plural': 'Скарги',
            },
        ),
    ]
