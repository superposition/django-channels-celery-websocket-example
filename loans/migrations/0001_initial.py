# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-05 01:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customers', '0001_squashed_0010_auto_20170105_0123'),
    ]

    operations = [
        migrations.CreateModel(
            name='Loan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField()),
                ('reason', models.TextField(null=True)),
                ('end_date', models.DateField()),
                ('company', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='customers.Company')),
            ],
        ),
    ]
