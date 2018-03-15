# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-03-10 06:24
from __future__ import unicode_literals

import ckeditor.fields
import datetime
from django.db import migrations, models
import django.db.models.deletion
import pod.video.models
import tagging.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authentication', '0001_initial'),
        ('auth', '0008_alter_user_username_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True, serialize=False,
                    verbose_name='ID')),
                ('video', models.FileField(
                    max_length=255,
                    upload_to=pod.video.models.get_storage_path,
                    verbose_name='Video')),
                ('allow_downloading', models.BooleanField(
                    default=False, verbose_name='allow downloading')),
                ('is_360', models.BooleanField(
                    default=False, verbose_name='video 360')),
                ('title', models.CharField(
                    max_length=250, verbose_name='Title')),
                ('slug', models.SlugField(editable=False,
                                          help_text='Used to access this '
                                          + 'instance, the "slug" is a short '
                                          + 'label containing only letters, '
                                          + 'numbers, underscore or dash top.',
                                          max_length=255, unique=True,
                                          verbose_name='Slug')),
                ('date_added', models.DateField(
                    default=datetime.datetime.now, verbose_name='Date added')),
                ('date_evt', models.DateField(
                    blank=True, default=datetime.datetime.now, null=True,
                    verbose_name='Date of event')),
                ('description', ckeditor.fields.RichTextField(
                    blank=True, verbose_name='Description')),
                ('cursus', models.CharField(
                    choices=[('0', 'None / All'),
                             ('L', 'Bachelor’s Degree'),
                             ('M', 'Master’s Degree'),
                             ('D', 'Doctorate'), ('1', 'Other')], default='0',
                    max_length=1, verbose_name='University course')),
                ('main_lang', models.CharField(choices=[
                 ('fr', 'French')], default='fr', max_length=2,
                    verbose_name='Main language')),
                ('overview',
                    models.ImageField(blank=True, editable=False,
                                      max_length=255,
                                      null=True,
                                      upload_to=pod
                                      .video.models.get_storage_path,
                                      verbose_name='Overview')),
                ('duration', models.IntegerField(
                    blank=True, default=0, editable=False,
                    verbose_name='Duration')),
                ('infoVideo', models.TextField(
                    blank=True, editable=False, null=True)),
                ('is_draft', models.BooleanField(
                    default=True, help_text='If this box is checked, '
                    + 'the video will be visible and accessible only by you.',
                    verbose_name='Draft')),
                ('is_restricted', models.BooleanField(
                    default=False, help_text='If this box is checked, '
                    + 'the video will only be accessible '
                    + 'to authenticated users.',
                    verbose_name='Restricted access')),
                ('password', models.CharField(blank=True,
                                              help_text='Viewing this video'
                                              + 'will not be possible without '
                                              + 'this password.',
                                              max_length=50,
                                              null=True,
                                              verbose_name='password')),
                ('tags', tagging.fields.TagField(blank=True, max_length=255)),
                ('owner', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='authentication.Owner',
                    verbose_name='Owner')),
                ('restrict_access_to_groups', models.ManyToManyField(
                    blank=True, to='auth.Group', verbose_name='Goups')),
            ],
        ),
        migrations.CreateModel(
            name='ViewCount',
            fields=[
                ('id', models.AutoField(
                    auto_created=True, primary_key=True,
                    serialize=False,
                    verbose_name='ID')),
                ('date', models.DateField(auto_now=True, verbose_name='Date')),
                ('count', models.IntegerField(
                    default=0, editable=False, verbose_name='Number of view')),
                ('video', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='video.Video')),
            ],
        ),
    ]