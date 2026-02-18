# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        ('instance', '0004_add_email_real_name_to_config'),
        ('popolo_sources', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstanceMembership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('person', models.ForeignKey(to='popolo.Person', on_delete=models.CASCADE)),
                ('writeitinstance', models.ForeignKey(to='instance.WriteItInstance', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='writeitinstance',
            name='popolo_persons',
            field=models.ManyToManyField(related_name='writeit_instances', through='instance.InstanceMembership', to='popolo.Person'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='writeitinstancepopitinstancerecord',
            name='popolo_source',
            field=models.ForeignKey(blank=True, to='popolo_sources.PopoloSource', null=True, on_delete=models.SET_NULL),
            preserve_default=True,
        ),
    ]
