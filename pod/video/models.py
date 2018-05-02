from django.db import models
from django.db import connection
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language
from django.template.defaultfilters import slugify
from django.db.models import Sum
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.apps import apps
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.dispatch import receiver
# from django.db.models.signals import post_save
# from django.db.models.signals import pre_save
from django.db.models.signals import pre_delete
# from django.db.models.signals import post_delete

try:
    from pod.filepicker.models import CustomImageModel
except ImportError:
    pass



from datetime import datetime
from ckeditor.fields import RichTextField
from tagging.fields import TagField

import os
import time
import unicodedata

import logging
logger = logging.getLogger(__name__)

FILEPICKER = True if apps.is_installed('pod.filepicker') else False
VIDEOS_DIR = getattr(
    settings, 'VIDEOS_DIR', 'videos')
FILES_DIR = getattr(
    settings, 'FILES_DIR', 'files')
MAIN_LANG_CHOICES = getattr(
    settings, 'MAIN_LANG_CHOICES', (('fr', _('French')),))
CURSUS_CODES = getattr(
    settings, 'CURSUS_CODES', (
        ('0', _("None / All")),
        ('L', _("Bachelor’s Degree")),
        ('M', _("Master’s Degree")),
        ('D', _("Doctorate")),
        ('1', _("Other"))
    ))
DEFAULT_TYPE_ID = getattr(
    settings, 'DEFAULT_TYPE_ID', 1)

LICENCE_CHOICES = getattr(
    settings, 'LICENCE_CHOICES', (
        ('BY', _("Attribution")),
        ('BY ND', _("Attribution + Pas de Modification")),
        ('BY NC ND', _(
            "Attribution + Pas d’Utilisation Commerciale + Pas de Modification"
        )),
        ('BY NC', _("Attribution + Pas d’Utilisation Commerciale")),
        ('BY NC SA',
            _(
                "Attribution + Pas d’Utilisation Commerciale + "
                + "Partage dans les mêmes conditions"
            )),
        ('BY SA', _(
            "Attribution + Partage dans les mêmes conditions"))
    ))
FORMAT_CHOICES = getattr(
    settings, 'FORMAT_CHOICES', (
        ("video/mp4", 'video/mp4'),
        ("video/mp2t", 'video/mp2t'),
        ("video/webm", 'video/webm'),
        ("audio/mp3", "audio/mp3"),
        ("audio/wav", "audio/wav"),
        ("application/x-mpegURL", "application/x-mpegURL"),
    ))
ENCODING_CHOICES = getattr(
    settings, 'ENCODING_CHOICES', (
        ("audio", "audio"),
        ("360p", "360p"),
        ("480p", "480p"),
        ("720p", "720p"),
        ("1080p", "1080p"),
        ("playlist", "playlist")
    ))
# FUNCTIONS


def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])


def get_storage_path_video(instance, filename):
    """ Get the storage path. Instance needs to implement owner """
    fname, dot, extension = filename.rpartition('.')
    try:
        fname.index("/")
        return os.path.join(VIDEOS_DIR, instance.owner.owner.hashkey,
                            '%s/%s.%s' % (os.path.dirname(fname),
                                          slugify(os.path.basename(fname)),
                                          extension))
    except ValueError:
        return os.path.join(VIDEOS_DIR, instance.owner.owner.hashkey,
                            '%s.%s' % (slugify(fname), extension))


def get_upload_path_files(instance, filename):
    fname, dot, extension = filename.rpartition('.')
    try:
        fname.index("/")
        return os.path.join(FILES_DIR,
                            '%s/%s.%s' % (os.path.dirname(fname),
                                          slugify(os.path.basename(fname)),
                                          extension))
    except ValueError:
        return os.path.join(FILES_DIR,
                            '%s.%s' % (slugify(fname), extension))


def get_nextautoincrement(mymodel):
    cursor = connection.cursor()
    cursor.execute(
        "SELECT Auto_increment FROM information_schema.tables "
        + "WHERE table_name='%s';" %
        mymodel._meta.db_table)
    row = cursor.fetchone()
    cursor.close()
    return row[0]

# MODELS


class VideoImageModel(models.Model):
    file = models.ImageField(
        _('Image'), null=True, upload_to=get_upload_path_files,
        blank=True, max_length=255)


class Channel(models.Model):
    title = models.CharField(_('Title'), max_length=100, unique=True)
    slug = models.SlugField(
        _('Slug'), unique=True, max_length=100,
        help_text=_(
            u'Used to access this instance, the "slug" is a short label '
            + 'containing only letters, numbers, underscore or dash top.'))
    description = RichTextField(_('Description'),
                                config_name='complete', blank=True)
    # add headband
    if FILEPICKER:
        headband = models.ForeignKey(CustomImageModel,
                                     blank=True, null=True,
                                     verbose_name=_('Headband'))
    else:
        headband = models.ForeignKey(VideoImageModel,
                                     blank=True, null=True,
                                     verbose_name=_('Thumbnails'))
    color = models.CharField(
        _('Background color'), max_length=10, blank=True, null=True)
    style = models.TextField(_('Extra style'), null=True, blank=True)
    owners = models.ManyToManyField(
        User, related_name='owners_channels', verbose_name=_('Owners'),
        blank=True)
    users = models.ManyToManyField(
        User, related_name='users_channels', verbose_name=_('Users'),
        blank=True)
    visible = models.BooleanField(
        verbose_name=_('Visible'),
        help_text=_(
            u'If checked, the channel appear in a list of available '
            + 'channels on the platform.'),
        default=False)

    class Meta:
        ordering = ['title']
        verbose_name = _('Channel')
        verbose_name_plural = _('Channels')

    def __str__(self):
        return "%s" % (self.title)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Channel, self).save(*args, **kwargs)


class Theme(models.Model):
    parentId = models.ForeignKey('self', null=True, blank=True)
    title = models.CharField(_('Title'), max_length=100, unique=True)
    slug = models.SlugField(
        _('Slug'), unique=True, max_length=100,
        help_text=_(
            u'Used to access this instance, the "slug" is a short label '
            + 'containing only letters, numbers, underscore or dash top.'))
    description = models.TextField(null=True, blank=True)
    if FILEPICKER:
        headband = models.ForeignKey(CustomImageModel,
                                     blank=True, null=True,
                                     verbose_name=_('Headband'))
    else:
        headband = models.ForeignKey(VideoImageModel,
                                     blank=True, null=True,
                                     verbose_name=_('Thumbnails'))

    channel = models.ForeignKey(
        'Channel', related_name='themes', verbose_name=_('Channel'))

    def __str__(self):
        return "%s: %s" % (self.channel.title, self.title)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Theme, self).save(*args, **kwargs)

    class Meta:
        ordering = ['title']
        verbose_name = _('Theme')
        verbose_name_plural = _('Themes')


class Type(models.Model):
    title = models.CharField(_('Title'), max_length=100, unique=True)
    slug = models.SlugField(
        _('Slug'), unique=True, max_length=100,
        help_text=_(
            u'Used to access this instance, the "slug" is a short label '
            + 'containing only letters, numbers, underscore or dash top.'))
    description = models.TextField(null=True, blank=True)
    if FILEPICKER:
        icon = models.ForeignKey(CustomImageModel,
                                 blank=True, null=True,
                                 verbose_name=_('Icon'))
    else:
        icon = models.ForeignKey(VideoImageModel,
                                 blank=True, null=True,
                                 verbose_name=_('Thumbnails'))

    def __str__(self):
        return "%s" % (self.title)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Type, self).save(*args, **kwargs)

    class Meta:
        ordering = ['title']
        verbose_name = _('Type')
        verbose_name_plural = _('Types')


class Discipline(models.Model):
    title = models.CharField(_('title'), max_length=100, unique=True)
    slug = models.SlugField(
        _('slug'), unique=True, max_length=100,
        help_text=_(
            u'Used to access this instance, the "slug" is a short label '
            + 'containing only letters, numbers, underscore or dash top.'))
    description = models.TextField(null=True, blank=True)
    if FILEPICKER:
        icon = models.ForeignKey(CustomImageModel,
                                 blank=True, null=True,
                                 verbose_name=_('Icon'))
    else:
        icon = models.ForeignKey(VideoImageModel,
                                 blank=True, null=True,
                                 verbose_name=_('Thumbnails'))

    def __str__(self):
        return "%s" % (self.title)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Discipline, self).save(*args, **kwargs)

    class Meta:
        ordering = ['title']
        verbose_name = _('Discipline')
        verbose_name_plural = _('Disciplines')


class Video(models.Model):
    video = models.FileField(
        _('Video'),  upload_to=get_storage_path_video, max_length=255)

    allow_downloading = models.BooleanField(
        _('allow downloading'), default=False)
    is_360 = models.BooleanField(_('video 360'), default=False)
    title = models.CharField(_('Title'), max_length=250)
    slug = models.SlugField(_('Slug'), unique=True, max_length=255,
                            help_text=_(
                                'Used to access this instance, the "slug" is '
                                + 'a short label containing only letters, '
                                + 'numbers, underscore or dash top.'),
                            editable=False)
    owner = models.ForeignKey(User, verbose_name=_('Owner'))
    date_added = models.DateField(_('Date added'), default=datetime.now)
    date_evt = models.DateField(
        _(u'Date of event'), default=datetime.now, blank=True, null=True)
    description = RichTextField(
        _('Description'), config_name='complete', blank=True)

    cursus = models.CharField(
        _('University course'), max_length=1,
        choices=CURSUS_CODES, default="0")
    main_lang = models.CharField(
        _('Main language'), max_length=2,
        choices=MAIN_LANG_CHOICES, default=get_language())

    duration = models.IntegerField(
        _('Duration'), default=0, editable=False, blank=True)

    is_draft = models.BooleanField(
        verbose_name=_('Draft'),
        help_text=_(
            u'If this box is checked, '
            + 'the video will be visible and accessible only by you.'),
        default=True)
    is_restricted = models.BooleanField(
        verbose_name=_(u'Restricted access'),
        help_text=_(
            u'If this box is checked, '
            + 'the video will only be accessible to authenticated users.'),
        default=False)
    restrict_access_to_groups = models.ManyToManyField(
        Group, blank=True, verbose_name=_('Goups'),
        help_text=_(u'Select one or more groups who can access to this video'))
    password = models.CharField(
        _('password'),
        help_text=_(
            u'Viewing this video will not be possible without this password.'),
        max_length=50, blank=True, null=True)
    tags = TagField(help_text=_(
        u'Separate tags with spaces, '
        + 'enclose the tags consist of several words in quotation marks.'),
        verbose_name=_('Tags'))
    if FILEPICKER:
        thumbnail = models.ForeignKey(CustomImageModel,
                                      blank=True, null=True,
                                      verbose_name=_('Thumbnails'))
    else:
        thumbnail = models.ForeignKey(VideoImageModel,
                                      blank=True, null=True,
                                      verbose_name=_('Thumbnails'))

    overview = models.ImageField(
        _('Overview'), null=True, upload_to=get_upload_path_files,
        blank=True, max_length=255, editable=False)

    type = models.ForeignKey(Type, verbose_name=_('Type'),
                             default=DEFAULT_TYPE_ID)
    discipline = models.ManyToManyField(
        Discipline, blank=True, verbose_name=_('Disciplines'))
    channel = models.ManyToManyField(
        Channel, verbose_name=_('Channels'), blank=True)
    theme = models.ManyToManyField(
        Theme, verbose_name=_('Themes'), blank=True)

    licence = models.CharField(
        _('Licence'), max_length=8,
        choices=LICENCE_CHOICES, blank=True, null=True)

    encoding_in_progress = models.BooleanField(
        _('Encoding in progress'), default=False, editable=False)

    def save(self, *args, **kwargs):
        newid = -1
        if not self.id:
            try:
                newid = get_nextautoincrement(Video)
            except Exception:
                try:
                    newid = Video.objects.latest('id').id
                    newid += 1
                except Exception:
                    newid = 1
        else:
            newid = self.id
        newid = '%04d' % newid
        self.slug = "%s-%s" % (newid, slugify(self.title))
        self.tags = remove_accents(self.tags)
        super(Video, self).save(*args, **kwargs)

    def __str__(self):
        return "%s - %s" % ('%04d' % self.id, self.title)

    def get_viewcount(self):
        count_sum = self.viewcount_set.all().aggregate(Sum('count'))
        if count_sum['count__sum'] is None:
            return 0
        return count_sum['count__sum']

    def duration_in_time(self):
        return time.strftime('%H:%M:%S', time.gmtime(self.duration))

    duration_in_time.short_description = _('Duration')
    duration_in_time.allow_tags = True

    def get_absolute_url(self):
        return reverse('video', args=[str(self.slug)])

    def delete(self):
        if self.video:
            if os.path.isfile(self.video.path):
                os.remove(self.video.path)
        if self.overview:
            if os.path.isfile(self.overview.path):
                os.remove(self.overview.path)
        super(Video, self).delete()


def remove_video_file(video):
    if video.video:
        log_file = os.path.join(
            os.path.dirname(video.video.path),
            "%04d" % video.id,
            'encoding.log')
        if os.path.isfile(log_file):
            os.remove(log_file)
    if video.overview:
        image_overview = os.path.join(
            os.path.dirname(video.overview.path), 'overview.png')
        if os.path.isfile(image_overview):
            os.remove(image_overview)
        video.overview.delete()


@receiver(pre_delete, sender=Video,
          dispatch_uid='pre_delete-video_files_removal')
def video_files_removal(sender, instance, using, **kwargs):

    remove_video_file(instance)

    previous_encoding_video = EncodingVideo.objects.filter(
        video=instance)
    if len(previous_encoding_video) > 0:
        for encoding in previous_encoding_video:
            encoding.delete()

    previous_encoding_audio = EncodingAudio.objects.filter(
        video=instance)
    if len(previous_encoding_audio) > 0:
        for encoding in previous_encoding_audio:
            encoding.delete()

    previous_encoding_playlist = PlaylistVideo.objects.filter(
        video=instance)
    if len(previous_encoding_playlist) > 0:
        for encoding in previous_encoding_playlist:
            encoding.delete()


class ViewCount(models.Model):
    video = models.ForeignKey(Video, verbose_name=_('Video'),
                              editable=False)
    date = models.DateField(
        _(u'Date'), default=datetime.now)
    count = models.IntegerField(
        _('Number of view'), default=0, editable=False)


class VideoRendition(models.Model):
    resolution = models.CharField(
        _('resolution'),
        max_length=250,
        unique=True,
        help_text="Please use the only format x. i.e.: "
        + "<em>640x360</em> or <em>1280x720</em> or <em>1920x1080</em>.")
    video_bitrate = models.CharField(
        _('bitrate video'),
        max_length=250,
        help_text="Please use the only format k. i.e.: "
        + "<em>300k</em> or <em>600k</em> or <em>1000k</em>.")
    audio_bitrate = models.CharField(
        _('bitrate audio'),
        max_length=250,
        help_text="Please use the only format k. i.e.: "
        + "<em>300k</em> or <em>600k</em> or <em>1000k</em>.")
    encode_mp4 = models.BooleanField(_('Make a MP4 version'), default=False)

    @property
    def height(self):
        return int(self.resolution.split("x")[1])

    @property
    def width(self):
        return int(self.resolution.split("x")[0])

    def __str__(self):
        return "VideoRendition num %s with resolution %s" % (
            '%04d' % self.id, self.resolution)

    def clean(self):
        if self.resolution and 'x' not in self.resolution:
            raise ValidationError(
                VideoRendition._meta.get_field('resolution').help_text)
        else:
            res = self.resolution.replace('x', '')
            if not res.isdigit():
                raise ValidationError(
                    VideoRendition._meta.get_field('resolution').help_text)
        if self.video_bitrate and 'k' not in self.video_bitrate:
            msg = "Error in %s : " % _('bitrate video')
            raise ValidationError(
                msg + VideoRendition._meta.get_field(
                    'video_bitrate').help_text)
        else:
            vb = self.video_bitrate.replace('k', '')
            if not vb.isdigit():
                msg = "Error in %s : " % _('bitrate video')
                raise ValidationError(
                    msg + VideoRendition._meta.get_field(
                        'video_bitrate').help_text)
        if self.audio_bitrate and 'k' not in self.audio_bitrate:
            msg = "Error in %s : " % _('bitrate audio')
            raise ValidationError(
                msg + VideoRendition._meta.get_field(
                    'audio_bitrate').help_text)
        else:
            vb = self.audio_bitrate.replace('k', '')
            if not vb.isdigit():
                msg = "Error in %s : " % _('bitrate audio')
                raise ValidationError(
                    msg + VideoRendition._meta.get_field(
                        'audio_bitrate').help_text)


class EncodingVideo(models.Model):
    name = models.CharField(
        _('Name'),
        max_length=10,
        choices=ENCODING_CHOICES,
        default="360p",
        help_text="Please use the only format in encoding choices :"
        + " %s" % ' '.join(str(key) for key, value in ENCODING_CHOICES)
    )
    video = models.ForeignKey(Video, verbose_name=_('Video'))
    rendition = models.ForeignKey(
        VideoRendition, verbose_name=_('rendition'))
    encoding_format = models.CharField(
        _('Format'),
        max_length=22,
        choices=FORMAT_CHOICES,
        default="video/mp4",
        help_text="Please use the only format in format choices :"
        + " %s" % ' '.join(str(key) for key, value in FORMAT_CHOICES))
    source_file = models.FileField(
        _('encoding source file'),
        upload_to=get_storage_path_video,
        max_length=255)

    def clean(self):
        if self.name:
            if self.name not in dict(ENCODING_CHOICES):
                raise ValidationError(
                    EncodingVideo._meta.get_field('name').help_text
                )
        if self.encoding_format:
            if self.encoding_format not in dict(FORMAT_CHOICES):
                raise ValidationError(
                    EncodingVideo._meta.get_field('encoding_format').help_text
                )

    def __str__(self):
        return "EncodingVideo num : %s with resolution %s for video %s in %s"\
            % ('%04d' % self.id,
               self.name,
               self.video.id,
               self.encoding_format)

    @property
    def owner(self):
        return self.video.owner

    @property
    def height(self):
        return int(self.rendition.resolution.split("x")[1])

    @property
    def width(self):
        return int(self.rendition.resolution.split("x")[0])

    def delete(self):
        if self.source_file:
            if os.path.isfile(self.source_file.path):
                os.remove(self.source_file.path)
        super(EncodingVideo, self).delete()


class EncodingAudio(models.Model):
    name = models.CharField(
        _('Name'), max_length=10, choices=ENCODING_CHOICES, default="audio",
        help_text="Please use the only format in encoding choices :"
        + " %s" % ' '.join(str(key) for key, value in ENCODING_CHOICES))
    video = models.ForeignKey(Video, verbose_name=_('Video'))
    encoding_format = models.CharField(
        _('Format'), max_length=22, choices=FORMAT_CHOICES,
        default="audio/mp3",
        help_text="Please use the only format in format choices :"
        + " %s" % ' '.join(str(key) for key, value in FORMAT_CHOICES))
    source_file = models.FileField(
        _('encoding source file'),
        upload_to=get_storage_path_video,
        max_length=255)

    def clean(self):
        if self.name:
            if self.name not in dict(ENCODING_CHOICES):
                raise ValidationError(
                    EncodingAudio._meta.get_field('name').help_text
                )
        if self.encoding_format:
            if self.encoding_format not in dict(FORMAT_CHOICES):
                raise ValidationError(
                    EncodingAudio._meta.get_field('encoding_format').help_text
                )

    def __str__(self):
        return "EncodingAudio num : %s for video %s in %s" % (
            '%04d' % self.id,
            self.video.id,
            self.encoding_format)

    @property
    def owner(self):
        return self.video.owner

    def delete(self):
        if self.source_file:
            if os.path.isfile(self.source_file.path):
                os.remove(self.source_file.path)
        super(EncodingAudio, self).delete()


class PlaylistVideo(models.Model):
    name = models.CharField(
        _('Name'), max_length=10, choices=ENCODING_CHOICES, default="360p",
        help_text="Please use the only format in encoding choices :"
        + " %s" % ' '.join(str(key) for key, value in ENCODING_CHOICES))
    video = models.ForeignKey(Video, verbose_name=_('Video'))
    encoding_format = models.CharField(
        _('Format'), max_length=22, choices=FORMAT_CHOICES,
        default="application/x-mpegURL",
        help_text="Please use the only format in format choices :"
        + " %s" % ' '.join(str(key) for key, value in FORMAT_CHOICES))
    source_file = models.FileField(
        _('encoding source file'),
        upload_to=get_storage_path_video,
        max_length=255)

    def clean(self):
        if self.name:
            if self.name not in dict(ENCODING_CHOICES):
                raise ValidationError(
                    PlaylistVideo._meta.get_field('name').help_text
                )
        if self.encoding_format:
            if self.encoding_format not in dict(FORMAT_CHOICES):
                raise ValidationError(
                    PlaylistVideo._meta.get_field('encoding_format').help_text
                )

    def __str__(self):
        return "Playlist num : %s for video %s in %s" % (
            '%04d' % self.id,
            self.video.id,
            self.encoding_format)

    @property
    def owner(self):
        return self.video.owner

    def delete(self):
        if self.source_file:
            if os.path.isfile(self.source_file.path):
                os.remove(self.source_file.path)
        super(PlaylistVideo, self).delete()


class EncodingLog(models.Model):
    video = models.OneToOneField(Video, verbose_name=_('Video'),
                                 editable=False, on_delete=models.CASCADE)
    log = models.TextField(null=True, blank=True, editable=False)

    def __str__(self):
        return "Log for encoding video %s" % (self.video.id)


class EncodingStep(models.Model):
    video = models.OneToOneField(Video, verbose_name=_('Video'),
                                 editable=False, on_delete=models.CASCADE)
    num_step = models.IntegerField(default=0, editable=False)
    desc_step = models.CharField(null=True,
                                 max_length=255, blank=True, editable=False)

    def __str__(self):
        return "Step for encoding video %s" % (self.video.id)
