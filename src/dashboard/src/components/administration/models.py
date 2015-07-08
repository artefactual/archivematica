from django.db import models
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


PREMIS_CHOICES = [('yes', 'Yes'), ('no', 'No'), ('premis', 'Base on PREMIS')]
EAD_ACTUATE_CHOICES = [('none', 'None'), ('onLoad', 'onLoad'), ('other', 'other'), ('onRequest', 'onRequest')]
EAD_SHOW_CHOICES = [('embed', 'Embed'), ('new', 'New'), ('none', 'None'), ('other', 'Other'), ('replace', 'Replace')]

class ArchivistsToolkitConfig(models.Model):
    id = UUIDPkField()
    host = models.CharField(max_length=50, verbose_name='Database Host')
    port = models.IntegerField(default=3306, verbose_name='Database Port')
    dbname = models.CharField(max_length=50, verbose_name='Database Name')
    dbuser = models.CharField(max_length=50, verbose_name='Database User')
    dbpass = models.CharField(max_length=50, blank=True, verbose_name='Database Password')
    atuser = models.CharField(max_length=50, verbose_name='Archivists Toolkit Username')
    premis = models.CharField(max_length=10, choices=PREMIS_CHOICES, verbose_name='Restrictions Apply', default='yes')
    ead_actuate = models.CharField(max_length=50, choices=EAD_ACTUATE_CHOICES, verbose_name='EAD DAO Actuate', default='none')
    ead_show = models.CharField(max_length=50, choices=EAD_SHOW_CHOICES, verbose_name='EAD DAO Show', default='embed')
    object_type = models.CharField(max_length=50, blank=True, verbose_name='Object type')
    use_statement = models.CharField(max_length=50, verbose_name='Use Statement')
    uri_prefix = models.CharField(max_length=50, verbose_name='URL prefix')
    access_conditions = models.CharField(max_length=50, blank=True, verbose_name='Conditions governing access')
    use_conditions = models.CharField(max_length=50, blank=True, verbose_name='Conditions governing use')

class ArchivesSpaceConfig(models.Model):
    id = UUIDPkField()
    host = models.CharField(max_length=50, verbose_name='ArchivesSpace host')
    port = models.IntegerField(default=8089, verbose_name='ArchivesSpace backend port')
    user = models.CharField(max_length=50, verbose_name='ArchivesSpace administrative user')
    passwd = models.CharField(max_length=50, blank=True, verbose_name='ArchivesSpace administrative user password')
    premis = models.CharField(max_length=10, choices=PREMIS_CHOICES, verbose_name='Restrictions Apply', default='yes')
    xlink_show = models.CharField(max_length=50, choices=EAD_SHOW_CHOICES, verbose_name='XLink Show', default='embed')
    xlink_actuate = models.CharField(max_length=50, choices=EAD_ACTUATE_CHOICES, verbose_name='XLink Actuate', default='none')
    object_type = models.CharField(max_length=50, blank=True, verbose_name='Object type')
    use_statement = models.CharField(max_length=50, verbose_name='Use statement')
    uri_prefix = models.CharField(max_length=50, verbose_name='URL prefix')
    access_conditions = models.CharField(max_length=50, blank=True, verbose_name='Conditions governing access')
    use_conditions = models.CharField(max_length=50, blank=True, verbose_name='Conditions governing use')
    repository = models.IntegerField(default=2, verbose_name='ArchivesSpace repository number')
