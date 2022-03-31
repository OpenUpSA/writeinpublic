# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mailreporter', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='report',
            old_name='processed',
            new_name='resolved',
        ),
    ]
