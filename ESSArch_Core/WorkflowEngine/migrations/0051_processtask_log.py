# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-01 09:59
from __future__ import unicode_literals

from django.db import migrations
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('WorkflowEngine', '0050_auto_20161124_1116'),
    ]

    operations = [
        migrations.AddField(
            model_name='processtask',
            name='log',
            field=picklefield.fields.PickledObjectField(default=None, editable=False, null=True),
        ),
    ]