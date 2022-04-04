# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('report', jsonfield.fields.JSONField(default=dict)),
                ('processed', models.BooleanField(default=False)),
                ('date', models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
    ]
