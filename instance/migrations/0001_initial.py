# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields
from django.conf import settings
import annoying.fields


class Migration(migrations.Migration):

    dependencies = [
        ('popit', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('person', models.ForeignKey(to='popit.Person', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WriteItInstance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=512, blank=True)),
                ('slug', autoslug.fields.AutoSlugField(populate_from='name', unique=True, editable=False)),
                ('owner', models.ForeignKey(related_name='writeitinstances', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('persons', models.ManyToManyField(related_name='writeit_instances', through='instance.Membership', to='popit.Person')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WriteItInstanceConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('testing_mode', models.BooleanField(default=True)),
                ('moderation_needed_in_all_messages', models.BooleanField(default=False, help_text='Every message is going to         have a moderation mail')),
                ('allow_messages_using_form', models.BooleanField(default=True, help_text='Allow the creation of new messages         using the web')),
                ('rate_limiter', models.IntegerField(default=0)),
                ('notify_owner_when_new_answer', models.BooleanField(default=False, help_text='The owner of this instance         should be notified         when a new answer comes in')),
                ('autoconfirm_api_messages', models.BooleanField(default=True, help_text='Messages pushed to the api should             be confirmed automatically')),
                ('custom_from_domain', models.CharField(max_length=512, null=True, blank=True)),
                ('email_host', models.CharField(max_length=512, null=True, blank=True)),
                ('email_host_password', models.CharField(max_length=512, null=True, blank=True)),
                ('email_host_user', models.CharField(max_length=512, null=True, blank=True)),
                ('email_port', models.IntegerField(null=True, blank=True)),
                ('email_use_tls', models.NullBooleanField()),
                ('email_use_ssl', models.NullBooleanField()),
                ('can_create_answer', models.BooleanField(default=False, help_text='Can create an answer using the WebUI')),
                ('maximum_recipients', models.PositiveIntegerField(default=5)),
                ('default_language', models.CharField(max_length=10, choices=[('ar', 'Arabic'), ('cs', 'Czech'), ('en', 'English'), ('es', 'Spanish'), ('fr', 'French'), ('hu', 'Hungarian')])),
                ('writeitinstance', annoying.fields.AutoOneToOneField(related_name='config', to='instance.WriteItInstance', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WriteitInstancePopitInstanceRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('periodicity', models.CharField(default='1W', max_length=2, choices=[('--', 'Never'), ('2D', 'Twice every Day'), ('1D', 'Daily'), ('1W', 'Weekly')])),
                ('status', models.CharField(default='nothing', max_length=20, choices=[('nothing', 'Not doing anything now'), ('error', 'Error'), ('success', 'Success'), ('waiting', 'Waiting'), ('inprogress', 'In Progress')])),
                ('status_explanation', models.TextField(default='')),
                ('updated', models.DateTimeField(auto_now_add=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('popitapiinstance', models.ForeignKey(to='popit.ApiInstance', on_delete=models.CASCADE)),
                ('writeitinstance', models.ForeignKey(to='instance.WriteItInstance', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='membership',
            name='writeitinstance',
            field=models.ForeignKey(to='instance.WriteItInstance', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
