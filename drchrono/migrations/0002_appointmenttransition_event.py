# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2020-02-08 04:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drchrono', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointmenttransition',
            name='event',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
