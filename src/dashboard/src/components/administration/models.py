from django.db import models
from django.utils.translation import ugettext_lazy as _

from main.models import UUIDPkField


class ReplacementDict(models.Model):
    id = UUIDPkField()
    dictname = models.CharField(max_length=50)
    position = models.IntegerField(default=1)
    parameter = models.CharField(max_length=50)
    displayname = models.CharField(max_length=50)
    displayvalue = models.CharField(max_length=50)
    hidden = models.IntegerField()

    class Meta:
        db_table = u'ReplacementDict'


PREMIS_CHOICES = [
    ('yes', _('Yes')),
    ('no', _('No')),
    ('premis', _('Base on PREMIS'))
]

EAD_ACTUATE_CHOICES = [
    ('none', _('None')),
    ('onLoad', _('onLoad')),
    ('other', _('other')),
    ('onRequest', _('onRequest'))
]

EAD_SHOW_CHOICES = [
    ('embed', _('Embed')),
    ('new', _('New')),
    ('none', _('None')),
    ('other', _('Other')),
    ('replace', _('Replace'))
]


class ArchivistsToolkitConfig(models.Model):
    id = UUIDPkField()
    host = models.CharField(max_length=50, verbose_name=_('Database Host'))
    port = models.IntegerField(default=3306, verbose_name=_('Database Port'))
    dbname = models.CharField(max_length=50, verbose_name=_('Database Name'))
    dbuser = models.CharField(max_length=50, verbose_name=_('Database User'))
    dbpass = models.CharField(max_length=50, blank=True, verbose_name=_('Database Password'))
    atuser = models.CharField(max_length=50, verbose_name=_('Archivists Toolkit Username'))
    premis = models.CharField(max_length=10, choices=PREMIS_CHOICES, verbose_name=_('Restrictions Apply'), default='yes')
    ead_actuate = models.CharField(max_length=50, choices=EAD_ACTUATE_CHOICES, verbose_name=_('EAD DAO Actuate'), default='none')
    ead_show = models.CharField(max_length=50, choices=EAD_SHOW_CHOICES, verbose_name=_('EAD DAO Show'), default='embed')
    object_type = models.CharField(max_length=50, blank=True, verbose_name=_('Object type'))
    use_statement = models.CharField(max_length=50, verbose_name=_('Use Statement'))
    uri_prefix = models.CharField(max_length=50, verbose_name=_('URL prefix'))
    access_conditions = models.CharField(max_length=50, blank=True, verbose_name=_('Conditions governing access'))
    use_conditions = models.CharField(max_length=50, blank=True, verbose_name=_('Conditions governing use'))


class ArchivesSpaceConfig(models.Model):
    id = UUIDPkField()
    host = models.CharField(max_length=50, verbose_name=_('ArchivesSpace host'), help_text=_('Do not include http:// or www. Example: aspace.test.org '))
    port = models.IntegerField(default=8089, verbose_name=_('ArchivesSpace backend port'), help_text=_('Example: 8089'))
    user = models.CharField(max_length=50, verbose_name=_('ArchivesSpace administrative user'), help_text=_('Example: admin'))
    passwd = models.CharField(max_length=50, blank=True, verbose_name=_('ArchivesSpace administrative user password'), help_text=_('Password for user set above. Re-enter this password every time changes are made.'))
    premis = models.CharField(max_length=10, choices=PREMIS_CHOICES, verbose_name=_('Restrictions Apply'), default='yes')
    xlink_show = models.CharField(max_length=50, choices=EAD_SHOW_CHOICES, verbose_name=_('XLink Show'), default='embed')
    xlink_actuate = models.CharField(max_length=50, choices=EAD_ACTUATE_CHOICES, verbose_name=_('XLink Actuate'), default='none')
    object_type = models.CharField(max_length=50, blank=True, verbose_name=_('Object type'), help_text=_('Optional, must come from ArchivesSpace controlled list. Example: sound_recording'))
    use_statement = models.CharField(max_length=50, verbose_name=_('Use statement'), help_text=_('Optional, but if present should come from ArchivesSpace controlled list. Example: image-master'), blank=True)
    uri_prefix = models.CharField(max_length=50, verbose_name=_('URL prefix'), help_text=_('URL of DIP object server as you wish to appear in ArchivesSpace record. Example: http://example.com'))
    access_conditions = models.CharField(max_length=50, blank=True, verbose_name=_('Conditions governing access'), help_text=_('Populates Conditions governing access note'))
    use_conditions = models.CharField(max_length=50, blank=True, verbose_name=_('Conditions governing use'), help_text=_('Populates Conditions governing use note'))
    repository = models.IntegerField(default=2, verbose_name=_('ArchivesSpace repository number'), help_text=_('Default for single repository installation is 2'))
    inherit_notes = models.BooleanField(default=False, verbose_name=_('Inherit digital object notes from the parent component'))
