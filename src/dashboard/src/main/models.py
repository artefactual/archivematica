# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

# This Django model module was auto-generated and then updated manually
# Needs some cleanups, make sure each model has its primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.

# stdlib, alphabetical by import source
import ast
import logging

# Core Django, alphabetical by import source
from django import forms
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext as _, ugettext_lazy as _l

# Third party dependencies, alphabetical by import source
from django_extensions.db.fields import UUIDField

# This project, alphabetical by import source
from contrib import utils
import main

LOGGER = logging.getLogger('archivematica.dashboard')

METADATA_STATUS_ORIGINAL = 'ORIGINAL'
METADATA_STATUS_REINGEST = 'REINGEST'
METADATA_STATUS_UPDATED = 'UPDATED'
METADATA_STATUS = (
    (METADATA_STATUS_ORIGINAL, 'original'),
    (METADATA_STATUS_REINGEST, 'parsed from reingest'),
    (METADATA_STATUS_UPDATED, 'updated'),  # Might be updated for both, on rereingest
)


# CUSTOM FIELDS

class UUIDPkField(UUIDField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 36)
        kwargs['primary_key'] = True
        kwargs['db_column'] = 'pk'
        super(UUIDPkField, self).__init__(*args, **kwargs)


class BlobTextField(models.TextField):
    """
    Text field backed by `longblob` instead of `longtext`.

    Used for storing strings that need to match unsanitized paths on disk.
    """

    def db_type(self, connection):
        return 'longblob'


# SIGNALS

@receiver(post_save, sender=User)
def create_user_agent(sender, instance, **kwargs):
    LOGGER.debug('Caught post_save signal from %s with instance %r', sender, instance)
    agent, created = Agent.objects.update_or_create(userprofile__user=instance, defaults={
        'identifiertype': 'Archivematica user pk',
        'identifiervalue': str(instance.id),
        'name': 'username="{u.username}", first_name="{u.first_name}", last_name="{u.last_name}"'.format(u=instance),
        'agenttype': 'Archivematica user',
    })
    LOGGER.debug('Agent: %s; created: %s', agent, created)
    if created:
        UserProfile.objects.update_or_create(user=instance, defaults={'agent': agent})


# MODELS

class DashboardSettingManager(models.Manager):
    """
    Table-level dictionary behaviour for DashboardSetting.

    WARNING: This class is used from at least one database migration
    (0031_dashboard_scope). The implementation of set_dict should be backward
    compatible compatible with the existing migrations using it. If it changes,
    the migrations should be updated accordingly.
    """
    use_in_migrations = True  # Serialize manager into migration

    def get_dict(self, scope):
        """
        Retrieve a dictionary given its scope. The returned dict will be empty
        if the scope cannot not be found.

            > DashboardSetting.objects.get_dict('My dictionary')
            {u'foo': u'bar'}

        """
        return {key: value for (key, value) in self.get_queryset().filter(scope=scope).values_list('name', 'value')}

    def set_dict(self, scope, items):
        """
        Store key: value pairs in a given scope. Each item in the dict will
        be mapped into a table tuple. Existing pairs will be deleted. Django
        will convert all the values into unicode strings.

            > DashboardSetting.object.set_dict('My dictionary', {'foo': 'bar'})

        """
        if not isinstance(items, dict):
            return False
        with transaction.atomic():
            self.unset_dict(scope)
            self.bulk_create([
                DashboardSetting(scope=scope, name=unicode(name), value=unicode(value)) for name, value in items.items()
            ])

    def unset_dict(self, scope):
        return self.get_queryset().filter(scope=scope).delete()


class DashboardSetting(models.Model):
    """ Settings related to the dashboard stored as key-value pairs. """
    id = models.AutoField(primary_key=True, db_column='pk')
    scope = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255, db_column='name')
    value = models.TextField(db_column='value', blank=True)
    lastmodified = models.DateTimeField(auto_now=True, db_column='lastModified')

    objects = DashboardSettingManager()

    class Meta:
        db_table = u'DashboardSettings'

    def __str__(self):
        return '[scope={}|name={}]: {}'.format(self.scope if self.scope else '<blank>', self.name, self.value)


class Access(models.Model):
    """ Information about an upload to AtoM for a SIP. """
    id = models.AutoField(primary_key=True, db_column='pk')
    sipuuid = models.CharField(max_length=36, db_column='SIPUUID', blank=True)
    # Qubit ID (slug) generated or preexisting if a new description was not created
    resource = models.TextField(db_column='resource', blank=True)
    # Before the UploadDIP micro-service is executed, a dialog shows up and ask the user
    # the target archival description when the DIP will be deposited via SWORD
    # This column is mandatory, the user won't be able to submit the form if this field is empty
    target = models.TextField(db_column='target', blank=True)
    # Human readable status of an upload (rsync progress percentage, etc)
    status = models.TextField(db_column='status', blank=True)
    # Machine readable status code of an upload
    # 10 = Rsync is working
    # 11 = Rsync finished successfully
    # 12 = Rsync failed (then see self.exitcode to get rsync exit code)
    # 13 = SWORD deposit will be executed
    # 14 = Deposit done, Qubit returned code 200 (HTTP Created)
    #      - The deposited was created synchronously
    #      - At this point self.resource should contains the created Qubit resource
    # 15 = Deposit done, Qubit returned code 201 (HTTP Accepted)
    #      - The deposited will be created asynchronously (Qubit has a job queue)
    #      - At this point self.resource should contains the created Qubit resource
    #      - ^ this resource could be under progres, ask to Qubit for the status
    statuscode = models.PositiveSmallIntegerField(db_column='statusCode', null=True, blank=True)  # Actually a unsigned tinyint
    # Rsync exit code
    exitcode = models.PositiveSmallIntegerField(db_column='exitCode', null=True, blank=True)  # Actually a unsigned tinyint
    # Timestamps
    createdtime = models.DateTimeField(db_column='createdTime', auto_now_add=True)
    updatedtime = models.DateTimeField(db_column='updatedTime', auto_now=True)

    class Meta:
        db_table = u'Accesses'

    def get_title(self):
        try:
            jobs = main.models.Job.objects.filter(sipuuid=self.sipuuid, subjobof='')
            return utils.get_directory_name_from_job(jobs)
        except:
            return _('N/A')


class DublinCore(models.Model):
    """ DublinCore metadata associated with a SIP or Transfer. """
    id = models.AutoField(primary_key=True, db_column='pk')
    metadataappliestotype = models.ForeignKey('MetadataAppliesToType', db_column='metadataAppliesToType')
    metadataappliestoidentifier = models.CharField(max_length=36, blank=True, null=True, default=None, db_column='metadataAppliesToidentifier')  # Foreign key to SIPs or Transfers
    title = models.TextField(db_column='title', blank=True)
    is_part_of = models.TextField(db_column='isPartOf', verbose_name=_l('Part of AIC'), help_text=_l('Optional: leave blank if unsure'), blank=True)
    creator = models.TextField(db_column='creator', blank=True)
    subject = models.TextField(db_column='subject', blank=True)
    description = models.TextField(db_column='description', blank=True)
    publisher = models.TextField(db_column='publisher', blank=True)
    contributor = models.TextField(db_column='contributor', blank=True)
    date = models.TextField(help_text=_l('Use ISO 8601 (YYYY-MM-DD or YYYY-MM-DD/YYYY-MM-DD)'), db_column='date', blank=True)
    type = models.TextField(db_column='type', blank=True)
    format = models.TextField(db_column='format', blank=True)
    identifier = models.TextField(db_column='identifier', blank=True)
    source = models.TextField(db_column='source', blank=True)
    relation = models.TextField(db_column='relation', blank=True)
    language = models.TextField(help_text=_l('Use ISO 639'), db_column='language', blank=True)
    coverage = models.TextField(db_column='coverage', blank=True)
    rights = models.TextField(db_column='rights', blank=True)
    status = models.CharField(db_column='status', max_length=8, choices=METADATA_STATUS, default=METADATA_STATUS_ORIGINAL)

    class Meta:
        db_table = u'Dublincore'

    def __unicode__(self):
        if self.title:
            return u'%s' % self.title
        else:
            return _('Untitled')


class MetadataAppliesToType(models.Model):
    """
    What type of unit (SIP, DIP, Transfer etc) the metadata link is.

    TODO replace this with choices fields.
    """
    id = UUIDPkField()
    description = models.CharField(max_length=50, db_column='description')
    replaces = models.CharField(max_length=36, db_column='replaces', null=True, blank=True)
    lastmodified = models.DateTimeField(db_column='lastModified', auto_now=True)

    class Meta:
        db_table = u'MetadataAppliesToTypes'

    def __unicode__(self):
        return unicode(self.description)


class Event(models.Model):
    """ PREMIS Events associated with Files. """
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    event_id = UUIDField(auto=False, null=True, unique=True, db_column='eventIdentifierUUID')
    file_uuid = models.ForeignKey('File', db_column='fileUUID', to_field='uuid', null=True, blank=True)
    event_type = models.TextField(db_column='eventType', blank=True)
    event_datetime = models.DateTimeField(db_column='eventDateTime', auto_now=True)
    event_detail = models.TextField(db_column='eventDetail', blank=True)
    event_outcome = models.TextField(db_column='eventOutcome', blank=True)
    event_outcome_detail = models.TextField(db_column='eventOutcomeDetailNote', blank=True)  # TODO convert this to a BinaryField with Django >= 1.6
    agents = models.ManyToManyField('Agent')

    class Meta:
        db_table = u'Events'

    def __unicode__(self):
        return _('%(type)s event on %(file_uuid)s (%(detail)s)') % {
            'type': self.even_type,
            'file_uuid': self.file_uuid,
            'detail': self.event_detail
        }


class Derivation(models.Model):
    """
    Link between original and normalized files.

    Eg original to preservation copy, or original to access copy.
    """
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    source_file = models.ForeignKey('File', db_column='sourceFileUUID', to_field='uuid', related_name='derived_file_set')
    derived_file = models.ForeignKey('File', db_column='derivedFileUUID', to_field='uuid', related_name='original_file_set')
    event = models.ForeignKey('Event', db_column='relatedEventUUID', to_field='event_id', null=True, blank=True)

    class Meta:
        db_table = u'Derivations'

    def __unicode__(self):
        return _('%(derived)s derived from %(src)s in %(event)s') % {
            'derived': self.derived_file,
            'src': self.source_file,
            'event': self.event
        }


class UnitHiddenManager(models.Manager):
    def is_hidden(self, uuid):
        """ Return True if the unit (SIP, Transfer) with uuid is hidden. """
        try:
            return self.get_queryset().get(uuid=uuid).hidden
        except:
            return False


class SIP(models.Model):
    """ Information on SIP units. """
    uuid = models.CharField(max_length=36, primary_key=True, db_column='sipUUID')
    createdtime = models.DateTimeField(db_column='createdTime', auto_now_add=True)
    # If currentpath is null, this SIP is understood to not have been started yet.
    currentpath = models.TextField(db_column='currentPath', null=True, blank=True)
    hidden = models.BooleanField(default=False)
    aip_filename = models.TextField(db_column='aipFilename', null=True, blank=True)
    SIP_TYPE_CHOICES = (
        ('SIP', _l('SIP')),
        ('AIC', _l('AIC')),
        ('AIP-REIN', _l('Reingested AIP')),
        ('AIC-REIN', _l('Reingested AIC')),
    )
    sip_type = models.CharField(max_length=8, choices=SIP_TYPE_CHOICES, db_column='sipType', default='SIP')
    identifiers = models.ManyToManyField('Identifier')
    diruuids = models.BooleanField(db_column='dirUUIDs', default=False)

    # Deprecated
    magiclink = models.ForeignKey('MicroServiceChainLink', db_column='magicLink', null=True, blank=True)
    magiclinkexitmessage = models.CharField(max_length=50, db_column='magicLinkExitMessage', null=True, blank=True)

    objects = UnitHiddenManager()

    class Meta:
        db_table = u'SIPs'

    def __unicode__(self):
        return _('SIP: {path}') % {'path': self.currentpath}


class TransferManager(models.Manager):
    def is_hidden(self, uuid):
        try:
            return Transfer.objects.get(uuid__exact=uuid).hidden is True
        except:
            return False


class Transfer(models.Model):
    """ Information on Transfer units. """
    uuid = models.CharField(max_length=36, primary_key=True, db_column='transferUUID')
    currentlocation = models.TextField(db_column='currentLocation')
    type = models.CharField(max_length=50, db_column='type')
    accessionid = models.TextField(db_column='accessionID')
    sourceofacquisition = models.TextField(db_column='sourceOfAcquisition', blank=True)
    typeoftransfer = models.TextField(db_column='typeOfTransfer', blank=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    hidden = models.BooleanField(default=False)
    transfermetadatasetrow = models.ForeignKey('TransferMetadataSet', db_column='transferMetadataSetRowUUID', to_field='id', null=True, blank=True)
    diruuids = models.BooleanField(db_column='dirUUIDs', default=False)

    # Deprecated
    magiclink = models.ForeignKey('MicroServiceChainLink', db_column='magicLink', null=True, blank=True)
    magiclinkexitmessage = models.CharField(max_length=50, db_column='magicLinkExitMessage', null=True, blank=True)

    objects = UnitHiddenManager()

    class Meta:
        db_table = u'Transfers'


class SIPArrange(models.Model):
    """ Information about arranged files: original and arranged location, current status. """
    original_path = models.CharField(max_length=255, null=True, blank=True, default=None, unique=True)
    arrange_path = models.CharField(max_length=255)
    file_uuid = UUIDField(auto=False, null=True, blank=True, default=None)
    transfer_uuid = UUIDField(auto=False, null=True, blank=True, default=None)
    sip = models.ForeignKey(SIP, to_field='uuid', null=True, blank=True, default=None)
    level_of_description = models.CharField(max_length=2014)
    sip_created = models.BooleanField(default=False)
    aip_created = models.BooleanField(default=False)

    class Meta:
        verbose_name = _l("Arranged SIPs")

    def __unicode__(self):
        return _('%(original)s -> %(arrange)s') % {
            'original': self.original_path,
            'arrange': self.arrange_path
        }


class SIPArrangeAccessMapping(models.Model):
    """ Maps directories within SIPArrange to descriptive objects in a remote archival management system. """
    ARCHIVESSPACE = "archivesspace"
    ARCHIVISTS_TOOLKIT = "atk"
    ATOM = "atom"
    SYSTEMS = (
        (ARCHIVESSPACE, "ArchivesSpace"),
        (ARCHIVISTS_TOOLKIT, "Archivist's Toolkit"),
        (ATOM, "AtoM"),
    )

    arrange_path = models.CharField(max_length=255)
    system = models.CharField(choices=SYSTEMS, default=ATOM, max_length=255)
    identifier = models.CharField(max_length=255)

    def __str__(self):
        return 'arrange_path={s.arrange_path}, system={s.system}, identifier={s.identifier}'.format(s=self)


class Identifier(models.Model):
    """Identifiers used by File, Directory SIP models. Used for Handle System
    handles/PIDs and maybe for other types of identifier in the future.
    """
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    type = models.TextField(verbose_name=_l('Identifier Type'),
                            null=True, blank=False)
    value = models.TextField(
        verbose_name=_l('Identifier Value'),
        help_text=_l('Used for premis:objectIdentifierType and'
                     ' premis:objectIdentifierValue in the METS file.'),
        null=True, blank=False)

    def __str__(self):
        return (u'Identifier {i.identifiervalue} of type'
                ' {i.identifiertype}'.format(i=self))

    class Meta:
        db_table = u'Identifiers'


class File(models.Model):
    """ Information about Files in units (Transfers, SIPs). """
    uuid = models.CharField(max_length=36, primary_key=True, db_column='fileUUID')
    sip = models.ForeignKey(SIP, db_column='sipUUID', to_field='uuid', null=True, blank=True)
    transfer = models.ForeignKey(Transfer, db_column='transferUUID', to_field='uuid', null=True, blank=True)

    # both actually `longblob` in the database
    originallocation = BlobTextField(db_column='originalLocation')
    currentlocation = BlobTextField(db_column='currentLocation', null=True)
    filegrpuse = models.CharField(max_length=50, db_column='fileGrpUse', default='Original')
    filegrpuuid = models.CharField(max_length=36, db_column='fileGrpUUID', blank=True)
    checksum = models.CharField(max_length=128, db_column='checksum', blank=True)
    checksumtype = models.CharField(max_length=36, db_column='checksumType', blank=True)
    size = models.BigIntegerField(db_column='fileSize', null=True, blank=True)
    label = models.TextField(blank=True)
    modificationtime = models.DateTimeField(db_column='modificationTime', auto_now_add=True)
    enteredsystem = models.DateTimeField(db_column='enteredSystem', auto_now_add=True)
    removedtime = models.DateTimeField(db_column='removedTime', null=True, default=None)

    # This should hold any handles generated for the file.
    # Its format is expected to be "<NAMING_AUTHORITY>/<HANDLE>" i.e,.
    # "<NAMING_AUTHORITY>/<UUID>", e.g.,
    # "12345/6e6ea3f0-93ce-4798-bb75-a88e2d0d6f09". Note that neither the
    # resolver URL for constructing PURLs nor the qualifier (for constructing
    # qualified PURLs) should be included in this value. If needed, these
    # values can be constructed using the DashboardSettings rows with scope
    # 'handle'.
    identifiers = models.ManyToManyField('Identifier')

    class Meta:
        db_table = u'Files'

    def __unicode__(self):
        return _('File %(uuid)s: %(originallocation)s now at %(currentlocation)s') % {
            'uuid': self.uuid,
            'originallocation': self.originallocation,
            'currentlocation': self.currentlocation
        }


class Directory(models.Model):
    """Information about Directories in units (Transfers, SIPs).
    Note: Directory instances are only created if the user explicitly
    configures Archivematica to assign UUIDs to directories.
    """
    uuid = models.CharField(max_length=36, primary_key=True,
                            db_column='directoryUUID')
    sip = models.ForeignKey(SIP, db_column='sipUUID', to_field='uuid',
                            null=True, blank=True)
    transfer = models.ForeignKey(Transfer, db_column='transferUUID',
                                 to_field='uuid', null=True, blank=True)
    originallocation = BlobTextField(db_column='originalLocation')
    currentlocation = BlobTextField(db_column='currentLocation', null=True)
    enteredsystem = models.DateTimeField(db_column='enteredSystem',
                                         auto_now_add=True)
    identifiers = models.ManyToManyField('Identifier')

    class Meta:
        db_table = u'Directories'

    def __unicode__(self):
        return _('Directory %(uuid)s: %(originallocation)s now at %(currentlocation)s') % {
            'uuid': self.uuid,
            'originallocation': self.originallocation,
            'currentlocation': self.currentlocation
        }

    @classmethod
    def create_many(cls, dir_paths_uuids, unit_mdl, unit_type='transfer'):
        """Create ``Directory`` models to encode the relationship between each
        directory path/UUID pair in ``dir_paths_uuids`` and the ``Transfer`` model
        that the directories are a part of.
        """
        unit_type = {'transfer': 'transfer'}.get(unit_type, 'sip')
        return cls.objects.bulk_create([
            cls(**{'uuid': dir_uuid,
                   unit_type: unit_mdl,
                   'originallocation': dir_path,
                   'currentlocation': dir_path})
            for dir_path, dir_uuid in dir_paths_uuids])


class FileFormatVersion(models.Model):
    """
    Link between a File and the FormatVersion it is identified as.

    TODO? Replace this with a foreign key from File to FormatVersion.
    """
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    file_uuid = models.ForeignKey('File', db_column='fileUUID', to_field='uuid')
    format_version = models.ForeignKey('fpr.FormatVersion', db_column='fileID', to_field='uuid')

    class Meta:
        db_table = u'FilesIdentifiedIDs'

    def __unicode__(self):
        return u'%(file)s is %(format)s' % {
            'file': self.file_uuid,
            'format': self.format_version
        }


class Job(models.Model):
    jobuuid = UUIDField(db_column='jobUUID', primary_key=True)
    jobtype = models.CharField(max_length=250, db_column='jobType', blank=True)
    createdtime = models.DateTimeField(db_column='createdTime')
    createdtimedec = models.DecimalField(db_column='createdTimeDec', max_digits=26, decimal_places=10, default=0.0)
    directory = models.TextField(blank=True)
    sipuuid = models.CharField(max_length=36, db_column='SIPUUID')  # Foreign key to SIPs or Transfers
    unittype = models.CharField(max_length=50, db_column='unitType', blank=True)
    STATUS_UNKNOWN = 0
    STATUS_AWAITING_DECISION = 1
    STATUS_COMPLETED_SUCCESSFULLY = 2
    STATUS_EXECUTING_COMMANDS = 3
    STATUS_FAILED = 4
    STATUS = (
        (STATUS_UNKNOWN, _l('Unknown')),
        (STATUS_AWAITING_DECISION, _l('Awaiting decision')),
        (STATUS_COMPLETED_SUCCESSFULLY, _l('Completed successfully')),
        (STATUS_EXECUTING_COMMANDS, _l('Executing command(s)')),
        (STATUS_FAILED, _l('Failed'))
    )
    currentstep = models.IntegerField(db_column='currentStep', choices=STATUS, default=0, blank=False)
    microservicegroup = models.CharField(max_length=50, db_column='microserviceGroup', blank=True)
    hidden = models.BooleanField(default=False)
    microservicechainlink = models.ForeignKey('MicroServiceChainLink', db_column='MicroServiceChainLinksPK', null=True, blank=True)
    subjobof = models.CharField(max_length=36, db_column='subJobOf', blank=True)

    class Meta:
        db_table = u'Jobs'


class Task(models.Model):
    taskuuid = models.CharField(max_length=36, primary_key=True, db_column='taskUUID')
    job = models.ForeignKey('Job', db_column='jobuuid', to_field='jobuuid')
    createdtime = models.DateTimeField(db_column='createdTime')
    fileuuid = models.CharField(max_length=36, db_column='fileUUID', null=True, blank=True)
    # Actually a `longblob` in the database, since filenames may contain
    # arbitrary non-unicode characters - other blob and binary fields
    # have these types for the same reason.
    # Note that Django doesn't have a specific blob type, hence the use of
    # the char field types instead.
    filename = models.TextField(db_column='fileName', blank=True)
    execution = models.CharField(max_length=250, db_column='exec', blank=True)
    # actually a `varbinary(1000)` in the database
    arguments = models.CharField(max_length=1000, blank=True)
    starttime = models.DateTimeField(db_column='startTime', null=True, default=None)
    endtime = models.DateTimeField(db_column='endTime', null=True, default=None)
    client = models.CharField(max_length=50, blank=True)
    # stdout and stderror actually `longblobs` in the database
    stdout = models.TextField(db_column='stdOut', blank=True)
    stderror = models.TextField(db_column='stdError', blank=True)
    exitcode = models.BigIntegerField(db_column='exitCode', null=True, blank=True)

    class Meta:
        db_table = u'Tasks'


class Agent(models.Model):
    """ PREMIS Agents created for the system.  """
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    identifiertype = models.TextField(verbose_name=_l('Agent Identifier Type'), null=True, db_column='agentIdentifierType')
    identifiervalue = models.TextField(verbose_name=_l('Agent Identifier Value'), help_text=_l('Used for premis:agentIdentifierValue and premis:linkingAgentIdentifierValue in the METS file.'), null=True, blank=False, db_column='agentIdentifierValue')
    name = models.TextField(verbose_name=_l('Agent Name'), help_text=_l('Used for premis:agentName in the METS file.'), null=True, blank=False, db_column='agentName')
    agenttype = models.TextField(verbose_name=_l('Agent Type'), help_text=_l('Used for premis:agentType in the METS file.'), db_column='agentType', default='organization')

    def __str__(self):
        return u'{a.agenttype}; {a.identifiertype}: {a.identifiervalue}; {a.name}'.format(a=self)

    class Meta:
        db_table = u'Agents'


class UserProfile(models.Model):
    """ Extension of the User model for additional information. """
    user = models.OneToOneField(User)
    agent = models.OneToOneField(Agent)

    class Meta:
        db_table = u'main_userprofile'


class Report(models.Model):
    """ Reports of failures to display. """
    id = models.AutoField(primary_key=True, db_column='pk')
    unittype = models.CharField(max_length=50, db_column='unitType')
    unitname = models.CharField(max_length=50, db_column='unitName')
    unitidentifier = models.CharField(max_length=36, db_column='unitIdentifier')  # Foreign key to SIP or Transfer
    content = models.TextField(db_column='content')
    created = models.DateTimeField(db_column='created', auto_now_add=True)

    class Meta:
        db_table = u'Reports'


class RightsStatement(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    metadataappliestotype = models.ForeignKey(MetadataAppliesToType, to_field='id', db_column='metadataAppliesToType')
    metadataappliestoidentifier = models.CharField(max_length=36, blank=True, db_column='metadataAppliesToidentifier')
    rightsstatementidentifiertype = models.TextField(db_column='rightsStatementIdentifierType', blank=True, verbose_name=_l('Type'))
    rightsstatementidentifiervalue = models.TextField(db_column='rightsStatementIdentifierValue', blank=True, verbose_name=_l('Value'))
    rightsholder = models.IntegerField(db_column='fkAgent', default=0, verbose_name=_l('Rights holder'))
    RIGHTS_BASIS_CHOICES = (
        ('Copyright', _l('Copyright')),
        ('Statute', _l('Statute')),
        ('License', _l('License')),
        ('Donor', _l('Donor')),
        ('Policy', _l('Policy')),
        ('Other', _l('Other')),
    )
    rightsbasis = models.CharField(db_column='rightsBasis', choices=RIGHTS_BASIS_CHOICES, max_length=64, verbose_name=_l('Basis'), default='Copyright')
    status = models.CharField(db_column='status', max_length=8, choices=METADATA_STATUS, default=METADATA_STATUS_ORIGINAL)

    class Meta:
        db_table = u'RightsStatement'
        verbose_name = _l('Rights Statement')

    def __unicode__(self):
        return _('%(basis)s for %(unit)s (%(id)s)') % {
            'basis': self.rightsbasis,
            'unit': self.metadataappliestoidentifier,
            'id': self.id
        }


class RightsStatementCopyright(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    PREMIS_COPYRIGHT_STATUSES = (
        ('copyrighted', _l('copyrighted')),
        ('public domain', _l('public domain')),
        ('unknown', _l('unknown')),
    )
    copyrightstatus = models.TextField(db_column='copyrightStatus', blank=False, verbose_name=_l('Copyright status'), choices=PREMIS_COPYRIGHT_STATUSES, default='unknown')
    copyrightjurisdiction = models.TextField(db_column='copyrightJurisdiction', verbose_name=_l('Copyright jurisdiction'))
    copyrightstatusdeterminationdate = models.TextField(db_column='copyrightStatusDeterminationDate', blank=True, null=True, verbose_name=_l('Copyright determination date'), help_text=_l('Use ISO 8061 (YYYY-MM-DD)'))
    copyrightapplicablestartdate = models.TextField(db_column='copyrightApplicableStartDate', blank=True, null=True, verbose_name=_l('Copyright start date'), help_text=_l('Use ISO 8061 (YYYY-MM-DD)'))
    copyrightapplicableenddate = models.TextField(db_column='copyrightApplicableEndDate', blank=True, null=True, verbose_name=_l('Copyright end date'), help_text=_l('Use ISO 8061 (YYYY-MM-DD)'))
    copyrightenddateopen = models.BooleanField(default=False, db_column='copyrightApplicableEndDateOpen', verbose_name=_l('Open End Date'), help_text=_l('Indicate end date is open'))

    class Meta:
        db_table = u'RightsStatementCopyright'
        verbose_name = _l('Rights: Copyright')


class RightsStatementCopyrightDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightscopyright = models.ForeignKey(RightsStatementCopyright, db_column='fkRightsStatementCopyrightInformation')
    copyrightdocumentationidentifiertype = models.TextField(db_column='copyrightDocumentationIdentifierType', verbose_name=_l('Copyright document identification type'))
    copyrightdocumentationidentifiervalue = models.TextField(db_column='copyrightDocumentationIdentifierValue', verbose_name=_l('Copyright document identification value'))
    copyrightdocumentationidentifierrole = models.TextField(db_column='copyrightDocumentationIdentifierRole', null=True, blank=True, verbose_name=_l('Copyright document identification role'))

    class Meta:
        db_table = u'RightsStatementCopyrightDocumentationIdentifier'
        verbose_name = _l('Rights: Copyright: Docs ID')


class RightsStatementCopyrightNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightscopyright = models.ForeignKey(RightsStatementCopyright, db_column='fkRightsStatementCopyrightInformation')
    copyrightnote = models.TextField(db_column='copyrightNote', verbose_name=_l('Copyright note'))

    class Meta:
        db_table = u'RightsStatementCopyrightNote'
        verbose_name = _l('Rights: Copyright: Note')


class RightsStatementLicense(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    licenseterms = models.TextField(db_column='licenseTerms', blank=True, null=True, verbose_name=_l('License terms'))
    licenseapplicablestartdate = models.TextField(db_column='licenseApplicableStartDate', blank=True, null=True, verbose_name=_l('License start date'), help_text=_l('Use ISO 8061 (YYYY-MM-DD)'))
    licenseapplicableenddate = models.TextField(db_column='licenseApplicableEndDate', blank=True, null=True, verbose_name=_l('License end date'), help_text=_l('Use ISO 8061 (YYYY-MM-DD)'))
    licenseenddateopen = models.BooleanField(default=False, db_column='licenseApplicableEndDateOpen', verbose_name=_l('Open End Date'), help_text=_l('Indicate end date is open'))

    class Meta:
        db_table = u'RightsStatementLicense'
        verbose_name = _l('Rights: License')


class RightsStatementLicenseDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementlicense = models.ForeignKey(RightsStatementLicense, db_column='fkRightsStatementLicense')
    licensedocumentationidentifiertype = models.TextField(db_column='licenseDocumentationIdentifierType', verbose_name=_l('License documentation identification type'))
    licensedocumentationidentifiervalue = models.TextField(db_column='licenseDocumentationIdentifierValue', verbose_name=_l('License documentation identification value'))
    licensedocumentationidentifierrole = models.TextField(db_column='licenseDocumentationIdentifierRole', blank=True, null=True, verbose_name=_l('License document identification role'))

    class Meta:
        db_table = u'RightsStatementLicenseDocumentationIdentifier'
        verbose_name = _l('Rights: License: Docs ID')


class RightsStatementLicenseNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementlicense = models.ForeignKey(RightsStatementLicense, db_column='fkRightsStatementLicense')
    licensenote = models.TextField(db_column='licenseNote', verbose_name=_l('License note'))

    class Meta:
        db_table = u'RightsStatementLicenseNote'
        verbose_name = _l('Rights: License: Note')


class RightsStatementRightsGranted(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    act = models.TextField(db_column='act')
    startdate = models.TextField(db_column='startDate', verbose_name=_l('Start'), help_text=_l('Use ISO 8061 (YYYY-MM-DD)'), blank=True, null=True)
    enddate = models.TextField(db_column='endDate', verbose_name=_l('End'), help_text=_l('Use ISO 8061 (YYYY-MM-DD)'), blank=True, null=True)
    enddateopen = models.BooleanField(default=False, db_column='endDateOpen', verbose_name=_l('Open End Date'), help_text=_l('Indicate end date is open'))

    class Meta:
        db_table = u'RightsStatementRightsGranted'
        verbose_name = _l('Rights: Granted')


class RightsStatementRightsGrantedNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsgranted = models.ForeignKey(RightsStatementRightsGranted, related_name='notes', db_column='fkRightsStatementRightsGranted')
    rightsgrantednote = models.TextField(db_column='rightsGrantedNote', verbose_name=_l('Rights note'))

    class Meta:
        db_table = u'RightsStatementRightsGrantedNote'
        verbose_name = _l('Rights: Granted: Note')


class RightsStatementRightsGrantedRestriction(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsgranted = models.ForeignKey(RightsStatementRightsGranted, related_name='restrictions', db_column='fkRightsStatementRightsGranted')
    restriction = models.TextField(db_column='restriction')

    class Meta:
        db_table = u'RightsStatementRightsGrantedRestriction'
        verbose_name = _l('Rights: Granted: Restriction')


class RightsStatementStatuteInformation(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    statutejurisdiction = models.TextField(db_column='statuteJurisdiction', verbose_name=_l('Statute jurisdiction'))
    statutecitation = models.TextField(db_column='statuteCitation', verbose_name=_l('Statute citation'))
    statutedeterminationdate = models.TextField(db_column='statuteInformationDeterminationDate', verbose_name=_l('Statute determination date'), help_text=_l('Use ISO 8061 (YYYY-MM-DD)'), blank=True, null=True)
    statuteapplicablestartdate = models.TextField(db_column='statuteApplicableStartDate', blank=True, null=True, verbose_name=_l('Statute start date'), help_text=_l('Use ISO 8061 (YYYY-MM-DD)'))
    statuteapplicableenddate = models.TextField(db_column='statuteApplicableEndDate', blank=True, null=True, verbose_name=_l('Statute end date'), help_text=_l('Use ISO 8061 (YYYY-MM-DD)'))
    statuteenddateopen = models.BooleanField(default=False, db_column='statuteApplicableEndDateOpen', verbose_name=_l('Open End Date'), help_text=_l('Indicate end date is open'))

    class Meta:
        db_table = u'RightsStatementStatuteInformation'
        verbose_name = _l('Rights: Statute')


class RightsStatementStatuteInformationNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatementstatute = models.ForeignKey(RightsStatementStatuteInformation, db_column='fkRightsStatementStatuteInformation')
    statutenote = models.TextField(db_column='statuteNote', verbose_name=_l('Statute note'))

    class Meta:
        db_table = u'RightsStatementStatuteInformationNote'
        verbose_name = _l('Rights: Statute: Note')


class RightsStatementStatuteDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementstatute = models.ForeignKey(RightsStatementStatuteInformation, db_column='fkRightsStatementStatuteInformation')
    statutedocumentationidentifiertype = models.TextField(db_column='statuteDocumentationIdentifierType', verbose_name=_l('Statute document identification type'))
    statutedocumentationidentifiervalue = models.TextField(db_column='statuteDocumentationIdentifierValue', verbose_name=_l('Statute document identification value'))
    statutedocumentationidentifierrole = models.TextField(db_column='statuteDocumentationIdentifierRole', blank=True, null=True, verbose_name=_l('Statute document identification role'))

    class Meta:
        db_table = u'RightsStatementStatuteDocumentationIdentifier'
        verbose_name = _l('Rights: Statute: Docs ID')


class RightsStatementOtherRightsInformation(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    otherrightsbasis = models.TextField(db_column='otherRightsBasis', verbose_name=_l('Other rights basis'), default='Other')
    otherrightsapplicablestartdate = models.TextField(db_column='otherRightsApplicableStartDate', blank=True, null=True, verbose_name=_l('Other rights start date'), help_text=_l('Use ISO 8061 (YYYY-MM-DD)'))
    otherrightsapplicableenddate = models.TextField(db_column='otherRightsApplicableEndDate', blank=True, null=True, verbose_name=_l('Other rights end date'), help_text=_l('Use ISO 8061 (YYYY-MM-DD)'))
    otherrightsenddateopen = models.BooleanField(default=False, db_column='otherRightsApplicableEndDateOpen', verbose_name=_l('Open End Date'), help_text=_l('Indicate end date is open'))

    class Meta:
        db_table = u'RightsStatementOtherRightsInformation'
        verbose_name = _l('Rights: Other')


class RightsStatementOtherRightsDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementotherrights = models.ForeignKey(RightsStatementOtherRightsInformation, db_column='fkRightsStatementOtherRightsInformation')
    otherrightsdocumentationidentifiertype = models.TextField(db_column='otherRightsDocumentationIdentifierType', verbose_name=_l('Other rights document identification type'))
    otherrightsdocumentationidentifiervalue = models.TextField(db_column='otherRightsDocumentationIdentifierValue', verbose_name=_l('Other right document identification value'))
    otherrightsdocumentationidentifierrole = models.TextField(db_column='otherRightsDocumentationIdentifierRole', blank=True, null=True, verbose_name=_l('Other rights document identification role'))

    class Meta:
        db_table = u'RightsStatementOtherRightsDocumentationIdentifier'
        verbose_name = _l('Rights: Other: Docs ID')


class RightsStatementOtherRightsInformationNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatementotherrights = models.ForeignKey(RightsStatementOtherRightsInformation, db_column='fkRightsStatementOtherRightsInformation')
    otherrightsnote = models.TextField(db_column='otherRightsNote', verbose_name=_l('Other rights note'))

    class Meta:
        db_table = u'RightsStatementOtherRightsNote'
        verbose_name = _l('Rights: Other: Note')


class RightsStatementLinkingAgentIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    linkingagentidentifiertype = models.TextField(db_column='linkingAgentIdentifierType', verbose_name=_l('Linking Agent'), blank=True)
    linkingagentidentifiervalue = models.TextField(db_column='linkingAgentIdentifierValue', verbose_name=_l('Linking Agent Value'), blank=True)

    class Meta:
        db_table = u'RightsStatementLinkingAgentIdentifier'
        verbose_name = _l('Rights: Agent')


# MCP data interoperability

class MicroServiceChain(models.Model):
    id = UUIDPkField()
    startinglink = models.ForeignKey('MicroServiceChainLink', db_column='startingLink')
    description = models.TextField(db_column='description')
    replaces = models.ForeignKey('self', related_name='replaced_by', db_column='replaces', null=True, blank=True)
    lastmodified = models.DateTimeField(db_column='lastModified', auto_now=True)

    class Meta:
        db_table = u'MicroServiceChains'

    def __unicode__(self):
        return _('MicroServiceChain ID: %(uuid)s; %(desc)s') % {
            'uuid': self.id,
            'desc': self.description
        }


class MicroServiceChainLink(models.Model):
    id = UUIDPkField()
    currenttask = models.ForeignKey('TaskConfig', db_column='currentTask')
    defaultnextchainlink = models.ForeignKey('self', db_column='defaultNextChainLink', null=True, blank=True)
    microservicegroup = models.CharField(max_length=50, db_column='microserviceGroup')
    reloadfilelist = models.BooleanField(default=True, db_column='reloadFileList')
    defaultexitmessage = models.CharField(max_length=36, db_column='defaultExitMessage', default='Failed')
    replaces = models.ForeignKey('self', related_name='replaced_by', db_column='replaces', null=True, blank=True)
    lastmodified = models.DateTimeField(db_column='lastModified', auto_now=True)

    class Meta:
        db_table = u'MicroServiceChainLinks'

    def __unicode__(self):
        return _('MicroServiceChainLink ID: %(id)s') % {'id': self.id}


class MicroServiceChainLinkExitCode(models.Model):
    id = UUIDPkField()
    microservicechainlink = models.ForeignKey('MicroServiceChainLink', related_name='exit_codes', db_column='microServiceChainLink')
    exitcode = models.IntegerField(db_column='exitCode', default=0)
    nextmicroservicechainlink = models.ForeignKey('MicroServiceChainLink', related_name='parent_exit_codes+', db_column='nextMicroServiceChainLink', null=True, blank=True)
    exitmessage = models.CharField(max_length=50, db_column='exitMessage', default='Completed successfully')
    replaces = models.ForeignKey('self', related_name='replaced_by', null=True, blank=True, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified', auto_now=True)

    class Meta:
        db_table = u'MicroServiceChainLinksExitCodes'


class MicroServiceChainChoice(models.Model):
    id = UUIDPkField()
    choiceavailableatlink = models.ForeignKey('MicroServiceChainLink', db_column='choiceAvailableAtLink')
    chainavailable = models.ForeignKey('MicroServiceChain', db_column='chainAvailable')
    replaces = models.ForeignKey('self', related_name='replaced_by', null=True, blank=True, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified', auto_now=True)

    class Meta:
        db_table = u'MicroServiceChainChoice'

    def __unicode__(self):
        return _('MicroServiceChainChoice ID: %(uuid)s (%(chain)s at %(choice)s)') % {
            'uuid': self.id,
            'chain': self.chainavailable,
            'choice': self.choiceavailableatlink
        }


class MicroServiceChoiceReplacementDic(models.Model):
    id = UUIDPkField()
    choiceavailableatlink = models.ForeignKey('MicroServiceChainLink', db_column='choiceAvailableAtLink')
    description = models.TextField(db_column='description', verbose_name=_l('Description'))
    replacementdic = models.TextField(db_column='replacementDic', verbose_name=_l('Configuration'))
    replaces = models.ForeignKey('self', related_name='replaced_by', null=True, blank=True, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified', auto_now=True)

    def clean(self):
        error = None
        try:
            config = ast.literal_eval(self.replacementdic)
        except (ValueError, SyntaxError):
            error = _('Invalid syntax.')
        if error is None and not isinstance(config, dict):
            error = _('Invalid syntax.')
        if error is not None:
            raise forms.ValidationError(error)

    class Meta:
        db_table = u'MicroServiceChoiceReplacementDic'


class TaskType(models.Model):
    id = UUIDPkField()
    description = models.TextField(blank=True)
    replaces = models.ForeignKey('self', related_name='replaced_by', null=True, blank=True, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified', auto_now=True)

    class Meta:
        db_table = 'TaskTypes'

    def __unicode__(self):
        return _('TaskType ID: %(id), desc: %(desc)') % {
            'id': self.id,
            'desc': self.description
        }


class TaskConfig(models.Model):
    id = UUIDPkField()
    tasktype = models.ForeignKey('TaskType', db_column='taskType')
    tasktypepkreference = models.CharField(max_length=36, db_column='taskTypePKReference', null=True, blank=True, default=None)  # Foreign key to table depending on TaskType
    description = models.TextField(db_column='description')
    replaces = models.ForeignKey('self', related_name='replaced_by', null=True, blank=True, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified', auto_now=True)

    class Meta:
        db_table = u'TasksConfigs'

    def __unicode__(self):
        return _('TaskType ID: %(id), desc: %(desc)') % {
            'id': self.id,
            'desc': self.description
        }


class StandardTaskConfig(models.Model):
    id = UUIDPkField()
    execute = models.CharField(max_length=250, null=True, db_column='execute')
    arguments = models.TextField(null=True, db_column='arguments')
    filter_subdir = models.CharField(max_length=50, db_column='filterSubDir', null=True, blank=True)
    filter_file_start = models.CharField(max_length=50, db_column='filterFileStart', null=True, blank=True)
    filter_file_end = models.CharField(max_length=50, db_column='filterFileEnd', null=True, blank=True)
    requires_output_lock = models.BooleanField(db_column='requiresOutputLock', default=False)
    stdout_file = models.CharField(max_length=250, db_column='standardOutputFile', null=True, blank=True)
    stderr_file = models.CharField(max_length=250, db_column='standardErrorFile', null=True, blank=True)
    replaces = models.ForeignKey('self', related_name='replaced_by', null=True, blank=True, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified', auto_now=True)

    class Meta:
        db_table = u'StandardTasksConfigs'


class TaskConfigAssignMagicLink(models.Model):
    id = UUIDPkField()
    execute = models.ForeignKey('MicroServiceChainLink', null=True, db_column='execute', blank=True)
    replaces = models.ForeignKey('self', related_name='replaced_by', null=True, blank=True, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified', auto_now=True)

    class Meta(object):
        db_table = u'TasksConfigsAssignMagicLink'


class TaskConfigSetUnitVariable(models.Model):
    id = UUIDPkField()
    variable = models.TextField(blank=True)
    variablevalue = models.TextField(null=True, blank=True, db_column='variableValue')
    microservicechainlink = models.ForeignKey('MicroServiceChainLink', null=True, db_column='microServiceChainLink')
    createdtime = models.DateTimeField(db_column='createdTime', auto_now_add=True)
    updatedtime = models.DateTimeField(db_column='updatedTime', auto_now=True, null=True)

    class Meta(object):
        db_table = u'TasksConfigsSetUnitVariable'


class TaskConfigUnitVariableLinkPull(models.Model):
    id = UUIDPkField()
    variable = models.TextField(blank=True)
    variablevalue = models.TextField(null=True, blank=True, db_column='variableValue')
    defaultmicroservicechainlink = models.ForeignKey('MicroServiceChainLink', null=True, db_column='defaultMicroServiceChainLink')
    createdtime = models.DateTimeField(db_column='createdTime', auto_now_add=True)
    updatedtime = models.DateTimeField(db_column='updatedTime', auto_now=True, null=True)

    class Meta(object):
        db_table = u'TasksConfigsUnitVariableLinkPull'


class JobFailMessage(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    message = models.CharField(max_length=1000, null=True, blank=True, db_column='Message')
    lastmodified = models.DateTimeField(db_column='lastModified', auto_now=True)
    microservicechainlink = models.ForeignKey('MicroServiceChainLink', null=True, db_column='microServiceChainLinksPK')

    class Meta:
        db_table = u'JobFailMessages'


class UnitVariable(models.Model):
    id = UUIDPkField()
    unittype = models.CharField(max_length=50, null=True, blank=True, db_column='unitType')
    unituuid = models.CharField(max_length=36, null=True, help_text=_l('Semantically a foreign key to SIP or Transfer'), db_column='unitUUID')
    variable = models.TextField(null=True, db_column='variable')
    variablevalue = models.TextField(null=True, db_column='variableValue')
    microservicechainlink = models.ForeignKey('MicroServiceChainLink', null=True, blank=True, help_text=_l('UUID of the MicroServiceChainLink if used in task type linkTaskManagerUnitVariableLinkPull'), db_column='microServiceChainLink')
    createdtime = models.DateTimeField(db_column='createdTime', auto_now_add=True)
    updatedtime = models.DateTimeField(db_column='updatedTime', auto_now=True)

    class Meta:
        db_table = u'UnitVariables'


# END MCP data interoperability

class AtkDIPObjectResourcePairing(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    dipuuid = models.CharField(max_length=50, db_column='dipUUID')
    fileuuid = models.CharField(max_length=50, db_column='fileUUID')
    resourceid = models.IntegerField(db_column='resourceId')
    resourcecomponentid = models.IntegerField(db_column='resourceComponentId')

    class Meta:
        db_table = u'AtkDIPObjectResourcePairing'


class ArchivesSpaceDIPObjectResourcePairing(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    # TODO these should be foreign keys?
    dipuuid = models.CharField(max_length=50, db_column='dipUUID')
    fileuuid = models.CharField(max_length=50, db_column='fileUUID')
    # This field holds URL fragments, for instance:
    # /repositories/2/archival_objects/1
    resourceid = models.CharField(max_length=150, db_column='resourceId')

    def __str__(self):
        return 'ArchivesSpace Pairing<dipuuid: {s.dipuuid}, resourceid: {s.resourceid}>'.format(s=self)

    class Meta:
        db_table = u'ArchivesSpaceDIPObjectResourcePairing'
        # Table name length is fine, but if the verbose name is too
        # long it can result in confusing errors when trying to
        # set up permissions: https://code.djangoproject.com/ticket/18866
        verbose_name = _l('ASDIPObjectResourcePairing')


class ArchivesSpaceDigitalObject(models.Model):
    """
    Represents a digital object to be created in ArchivesSpace at the time an AIP is stored by Archivematica.
    """
    sip = models.ForeignKey('SIP', to_field='uuid', null=True)
    resourceid = models.CharField(max_length=150)
    label = models.CharField(max_length=255, blank=True)
    title = models.TextField(blank=True)
    started = models.BooleanField(default=False, help_text=_l('Whether or not a SIP has been started using files in this digital object.'))
    remoteid = models.CharField(max_length=150, blank=True, help_text=_l('ID in the remote ArchivesSpace system, after digital object has been created.'))


class TransferMetadataSet(models.Model):
    id = UUIDPkField()
    createdtime = models.DateTimeField(db_column='createdTime', auto_now_add=True)
    createdbyuserid = models.IntegerField(db_column='createdByUserID')

    class Meta:
        db_table = u'TransferMetadataSets'


class TransferMetadataField(models.Model):
    id = UUIDPkField()
    createdtime = models.DateTimeField(db_column='createdTime', auto_now_add=True, null=True)
    fieldlabel = models.CharField(max_length=50, blank=True, db_column='fieldLabel')
    fieldname = models.CharField(max_length=50, db_column='fieldName')
    fieldtype = models.CharField(max_length=50, db_column='fieldType')
    optiontaxonomy = models.ForeignKey('Taxonomy', db_column='optionTaxonomyUUID', to_field='id', null=True)
    sortorder = models.IntegerField(default=0, db_column='sortOrder')

    class Meta:
        db_table = u'TransferMetadataFields'

    def __unicode__(self):
        return self.fieldlabel


class TransferMetadataFieldValue(models.Model):
    id = UUIDPkField()
    createdtime = models.DateTimeField(db_column='createdTime', auto_now_add=True)
    set = models.ForeignKey('TransferMetadataSet', db_column='setUUID', to_field='id')
    field = models.ForeignKey('TransferMetadataField', db_column='fieldUUID', to_field='id')
    fieldvalue = models.TextField(blank=True, db_column='fieldValue')

    class Meta:
        db_table = u'TransferMetadataFieldValues'


# Taxonomies and their field definitions are in separate tables
# to leave room for future expansion. The possible taxonomy terms are
# designed to be editable, and forms to do so exist. (Forms for editing and
# defining new fields are present in the code but currently disabled.)
class Taxonomy(models.Model):
    id = UUIDPkField()
    createdtime = models.DateTimeField(db_column='createdTime', auto_now_add=True, null=True)
    name = models.CharField(max_length=255, blank=True, db_column='name')
    type = models.CharField(max_length=50, default='open')

    class Meta:
        db_table = u'Taxonomies'

    def __unicode__(self):
        return self.name


class TaxonomyTerm(models.Model):
    id = UUIDPkField()
    createdtime = models.DateTimeField(db_column='createdTime', auto_now_add=True, null=True)
    taxonomy = models.ForeignKey('Taxonomy', db_column='taxonomyUUID', to_field='id')
    term = models.CharField(max_length=255, db_column='term')

    class Meta:
        db_table = u'TaxonomyTerms'

    def __unicode__(self):
        return self.term


class WatchedDirectory(models.Model):
    id = UUIDPkField()
    watched_directory_path = models.TextField(null=True, blank=True, db_column='watchedDirectoryPath')
    chain = models.ForeignKey('MicroServiceChain', null=True, db_column='chain')
    only_act_on_directories = models.BooleanField(default=True, db_column='onlyActOnDirectories')
    expected_type = models.ForeignKey('WatchedDirectoryExpectedType', null=True, db_column='expectedType')
    replaces = models.ForeignKey('WatchedDirectory', null=True, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified', auto_now=True)

    class Meta(object):
        db_table = u"WatchedDirectories"


class WatchedDirectoryExpectedType(models.Model):
    id = UUIDPkField()
    description = models.TextField(null=True)
    replaces = models.ForeignKey('WatchedDirectoryExpectedType', null=True, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified', auto_now=True)

    class Meta(object):
        db_table = u"WatchedDirectoriesExpectedTypes"


class FPCommandOutput(models.Model):
    file = models.ForeignKey('File', db_column='fileUUID', to_field='uuid')
    content = models.TextField(null=True)
    rule = models.ForeignKey('fpr.FPRule', db_column='ruleUUID', to_field='uuid')

    # Table name is main_fpcommandoutput

    def __unicode__(self):
        return u'<file: {file}; rule: {rule}; content: {content}'.format(file=self.file, rule=self.rule, content=self.content[:20])


class FileID(models.Model):
    """
    This table duplicates file ID values from FPR formats. It predates the current FPR tables.

    This table may be removed in the future.
    """
    id = models.AutoField(primary_key=True, db_column='pk')
    file = models.ForeignKey('File', null=True, db_column='fileUUID', blank=True)
    format_name = models.TextField(db_column='formatName', blank=True)
    format_version = models.TextField(db_column='formatVersion', blank=True)
    format_registry_name = models.TextField(db_column='formatRegistryName', blank=True)
    format_registry_key = models.TextField(db_column='formatRegistryKey', blank=True)

    class Meta:
        db_table = 'FilesIDs'


class LevelOfDescription(models.Model):
    id = UUIDPkField()
    name = models.CharField(max_length='1024')  # seems long, but AtoM allows this much
    # sortorder should be unique, but is not defined so here to enable swapping
    sortorder = models.IntegerField(default=0, db_column='sortOrder')

    def __unicode__(self):
        return _('%(sortorder)s: %(name)s') % {
            'sortorder': self.sortorder,
            'name': self.name
        }
