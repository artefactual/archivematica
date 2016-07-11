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
# Feel free to rename the models, but don't rename db_table values or field
# names.

# stdlib, alphabetical by import source
import ast

# Core Django, alphabetical by import source
from django.db import models
from django import forms

# Third party dependencies, alphabetical by import source
from django_extensions.db.fields import UUIDField

# This project, alphabetical by import source
from contrib import utils
import main


METADATA_STATUS_ORIGINAL = 'ORIGINAL'
METADATA_STATUS_REINGEST = 'REINGEST'
METADATA_STATUS_UPDATED = 'UPDATED'
METADATA_STATUS = (
    (METADATA_STATUS_ORIGINAL, 'original'),
    (METADATA_STATUS_REINGEST, 'parsed from reingest'),
    (METADATA_STATUS_UPDATED, 'updated'),  # Might be updated for both, on
                                           # rereingest
)


# CUSTOM FIELDS


class UUIDPkField(UUIDField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 36)
        kwargs['primary_key'] = True
        kwargs['db_column'] = 'pk'
        super(UUIDPkField, self).__init__(*args, **kwargs)


# MODELS

class DashboardSetting(models.Model):
    """Settings related to the dashboard stored as key-value pairs.

    """

    id = models.AutoField(primary_key=True, db_column='pk')
    name = models.CharField(max_length=255, db_column='name')
    value = models.TextField(db_column='value', blank=True)
    lastmodified = models.DateTimeField(
        auto_now=True, db_column='lastModified')

    class Meta:
        db_table = u'DashboardSettings'


class Access(models.Model):
    """Information about an upload to AtoM for a SIP.

    """

    id = models.AutoField(primary_key=True, db_column='pk')
    sipuuid = models.CharField(max_length=36, db_column='SIPUUID', blank=True)

    # Qubit ID (i.e., slug), generated or preexisting, if a new description was
    # not created.
    resource = models.TextField(db_column='resource', blank=True)

    # The `target` (archival description) is mandatory in order for a DIP to be
    # uploaded via Sword (before the UploadDIP micro-service is executed).
    target = models.TextField(db_column='target', blank=True)

    # Human-readable status of an upload (rsync progress percentage, etc)
    status = models.TextField(db_column='status', blank=True)

    # Machine-readable status code of an upload
    # 10 = Rsync is working
    # 11 = Rsync finished successfully
    # 12 = Rsync failed (then see self.exitcode to get rsync exit code)
    # 13 = SWORD deposit will be executed
    # 14 = Deposit done, Qubit returned code 200 (HTTP Created)
    #      - The deposited was created synchronously
    #      - At this point self.resource should contain the created Qubit
    #        resource
    # 15 = Deposit done, Qubit returned code 201 (HTTP Accepted)
    #      - The deposited will be created asynchronously (Qubit has a job
    #        queue)
    #      - At this point self.resource should contain the created Qubit
    #        resource
    #      - ^ this resource could be in progress, ask Qubit for the status.
    # (Actually an unsigned tinyint)
    statuscode = models.PositiveSmallIntegerField(
        db_column='statusCode', null=True, blank=True)

    # Rsync exit code. (Actually an unsigned tinyint.)
    exitcode = models.PositiveSmallIntegerField(
        db_column='exitCode', null=True, blank=True)

    # Timestamps
    createdtime = models.DateTimeField(
        db_column='createdTime', auto_now_add=True)
    updatedtime = models.DateTimeField(db_column='updatedTime', auto_now=True)

    class Meta:
        db_table = u'Accesses'

    def get_title(self):
        try:
            jobs = main.models.Job.objects.filter(
                sipuuid=self.sipuuid, subjobof='')
            return utils.get_directory_name_from_job(jobs)
        except:
            return 'N/A'


class DublinCore(models.Model):
    """DublinCore metadata associated with a SIP or Transfer.

    """

    id = models.AutoField(primary_key=True, db_column='pk')

    # Type of entity, i.e., SIP or Transfer, that this metadata applies to.
    metadataappliestotype = models.ForeignKey(
        'MetadataAppliesToType', db_column='metadataAppliesToType')

    # Soft foreign key to SIPs or Transfers
    metadataappliestoidentifier = models.CharField(
        max_length=36, blank=True, null=True, default=None,
        db_column='metadataAppliesToidentifier')

    title = models.TextField(db_column='title', blank=True)
    is_part_of = models.TextField(
        db_column='isPartOf',
        verbose_name='Part of AIC',
        help_text='Optional: leave blank if unsure', blank=True)
    creator = models.TextField(db_column='creator', blank=True)
    subject = models.TextField(db_column='subject', blank=True)
    description = models.TextField(db_column='description', blank=True)
    publisher = models.TextField(db_column='publisher', blank=True)
    contributor = models.TextField(db_column='contributor', blank=True)

    # This help text confuses jrwdunham.
    date = models.TextField(
        help_text='Use ISO 8601 (YYYY-MM-DD or YYYY-MM-DD/YYYY-MM-DD)',
        db_column='date', blank=True)

    type = models.TextField(db_column='type', blank=True)
    format = models.TextField(db_column='format', blank=True)
    identifier = models.TextField(db_column='identifier', blank=True)
    source = models.TextField(db_column='source', blank=True)
    relation = models.TextField(db_column='relation', blank=True)
    language = models.TextField(help_text='Use ISO 639', db_column='language',
                                blank=True)
    coverage = models.TextField(db_column='coverage', blank=True)
    rights = models.TextField(db_column='rights', blank=True)
    status = models.CharField(
        db_column='status', max_length=8, choices=METADATA_STATUS,
        default=METADATA_STATUS_ORIGINAL)

    class Meta:
        db_table = u'Dublincore'

    def __unicode__(self):
        if self.title:
            return u'%s' % self.title
        else:
            return u'Untitled'


class MetadataAppliesToType(models.Model):
    """The type of unit (SIP, DIP, Transfer, etc.) that a piece of metadata
    applies to. `RightsStatement` and `DublinCore` instances reference these
    models.

    TODO replace this with choices fields.

    Note: 'SIP', 'Transfer' and 'File' seem to be the standard (only possible?)
    unit types.

    """

    id = UUIDPkField()
    description = models.CharField(max_length=50, db_column='description')
    replaces = models.CharField(
        max_length=36, db_column='replaces', null=True, blank=True)
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta:
        db_table = u'MetadataAppliesToTypes'

    def __unicode__(self):
        return unicode(self.description)


class Event(models.Model):
    """PREMIS Events associated with Files.

    There are many possible events for any given file within a unit. Events are
    related to Files via UUID pks. Example events: 'fixity check',
    'validation'.

    Question: are events transitory or do they persist once a unit no longer
    exists?

    """

    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    event_id = UUIDField(auto=False, null=True, unique=True,
                         db_column='eventIdentifierUUID')
    file_uuid = models.ForeignKey(
        'File', db_column='fileUUID', to_field='uuid', null=True, blank=True)
    event_type = models.TextField(db_column='eventType', blank=True)
    event_datetime = models.DateTimeField(
        db_column='eventDateTime', auto_now=True)
    event_detail = models.TextField(db_column='eventDetail', blank=True)
    event_outcome = models.TextField(db_column='eventOutcome', blank=True)
    # TODO convert this to a BinaryField with Django >= 1.6
    event_outcome_detail = models.TextField(
        db_column='eventOutcomeDetailNote', blank=True)

    # For historical reasons, this can be either a foreign key to the
    # Agent table or to the auth_user table. As a result, we can't track
    # it as a foreign key within Django.
    # See 57495899bb094dcf791b5f6d859cb596ecc5c37e for more information.
    linking_agent = models.IntegerField(
        db_column='linkingAgentIdentifier', null=True)

    class Meta:
        db_table = u'Events'

    def __unicode__(self):
        return u"{event_type} event on {file} ({event_detail})".format(
            event_type=self.event_type,
            file=self.file_uuid,
            event_detail=self.event_detail)


class Derivation(models.Model):
    """A derivation represents the link between an original file and its
    normalized counterpart via a specified event.

    E.g., the link between the original and a preservation copy, or between the
    original and an access copy.

    """

    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    source_file = models.ForeignKey(
        'File', db_column='sourceFileUUID', to_field='uuid',
        related_name='derived_file_set')
    derived_file = models.ForeignKey(
        'File', db_column='derivedFileUUID', to_field='uuid',
        related_name='original_file_set')
    event = models.ForeignKey(
        'Event', db_column='relatedEventUUID', to_field='event_id', null=True,
        blank=True)

    class Meta:
        db_table = u'Derivations'

    def __unicode__(self):
        return u'{derived} derived from {src} in {event}'.format(
            src=self.source_file,
            derived=self.derived_file,
            event=self.event)


class UnitHiddenManager(models.Manager):
    """Manager to endow all Unit models with `is_hidden` (boolean) attributes.

    """

    def is_hidden(self, uuid):
        """Return True if the unit (SIP, Transfer) with uuid is hidden.

        """

        try:
            return self.get_queryset().get(uuid=uuid).hidden
        except:
            return False


class SIP(models.Model):
    """Information on SIP units.

    Note: an AIC is an Archival Information Collection, i.e., a collection of
    AIPs. Question: can AICs contain AICs?

    """

    uuid = models.CharField(
        max_length=36, primary_key=True, db_column='sipUUID')
    createdtime = models.DateTimeField(
        db_column='createdTime', auto_now_add=True)
    # If currentpath is null, this SIP is understood to not have been started
    # yet.
    currentpath = models.TextField(
        db_column='currentPath', null=True, blank=True)
    hidden = models.BooleanField(default=False)
    aip_filename = models.TextField(
        db_column='aipFilename', null=True, blank=True)
    SIP_TYPE_CHOICES = (
        ('SIP', 'SIP'),
        ('AIC', 'AIC'),
        ('AIP-REIN', 'Reingested AIP'),
        ('AIC-REIN', 'Reingested AIC'),
    )
    sip_type = models.CharField(
        max_length=8, choices=SIP_TYPE_CHOICES, db_column='sipType',
        default='SIP')

    # Deprecated
    # Question: what did they used to do?
    magiclink = models.ForeignKey(
        'MicroServiceChainLink', db_column='magicLink', null=True, blank=True)
    magiclinkexitmessage = models.CharField(
        max_length=50, db_column='magicLinkExitMessage', null=True, blank=True)

    objects = UnitHiddenManager()

    class Meta:
        db_table = u'SIPs'

    def __unicode__(self):
        return u'SIP: {path}'.format(path=self.currentpath)


# TODO: it seems class is not being used and could be deleted. Requesting
# third-party verification.
class TransferManager(models.Manager):
    def is_hidden(self, uuid):
        try:
            return Transfer.objects.get(uuid__exact=uuid).hidden is True
        except:
            return False


class Transfer(models.Model):
    """Information on Transfer units.

    """

    uuid = models.CharField(
        max_length=36, primary_key=True, db_column='transferUUID')
    currentlocation = models.TextField(db_column='currentLocation')
    type = models.CharField(max_length=50, db_column='type')

    # 'to accession' is to record the addition of (a new item) to a library,
    # museum, or other collection
    accessionid = models.TextField(db_column='accessionID')

    sourceofacquisition = models.TextField(
        db_column='sourceOfAcquisition', blank=True)
    typeoftransfer = models.TextField(db_column='typeOfTransfer', blank=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    hidden = models.BooleanField(default=False)
    transfermetadatasetrow = models.ForeignKey(
        'TransferMetadataSet', db_column='transferMetadataSetRowUUID',
        to_field='id', null=True, blank=True)

    # Deprecated
    magiclink = models.ForeignKey(
        'MicroServiceChainLink', db_column='magicLink', null=True, blank=True)
    magiclinkexitmessage = models.CharField(
        max_length=50, db_column='magicLinkExitMessage', null=True, blank=True)

    objects = UnitHiddenManager()

    class Meta:
        db_table = u'Transfers'


class SIPArrange(models.Model):
    """Information about arranged files: original and arranged location,
    current status.

    Question: What is the point of arranging files? (Assuming it means altering
    their position in a directory structure.)

    Question: How does this model get mapped to the `main_siparrange` table? Is
    this Django magick?

    """

    original_path = models.CharField(
        max_length=255, null=True, blank=True, default=None, unique=True)
    arrange_path = models.CharField(max_length=255)
    file_uuid = UUIDField(auto=False, null=True, blank=True, default=None)
    transfer_uuid = UUIDField(auto=False, null=True, blank=True, default=None)
    sip = models.ForeignKey(
        SIP, to_field='uuid', null=True, blank=True, default=None)
    level_of_description = models.CharField(max_length=2014)
    sip_created = models.BooleanField(default=False)
    aip_created = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Arranged SIPs"

    def __unicode__(self):
        return u'{original} -> {arrange}'.format(
            original=self.original_path,
            arrange=self.arrange_path)


class SIPArrangeAccessMapping(models.Model):
    """Maps directories within SIPArrange to descriptive objects in a remote
    archival management system.

    Note: it appears that this model corresponds to no table in the database
    and is simply created and held in memory, e.g., via `get_or_create` in
    components/access/views.py

    """

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


class File(models.Model):
    """Information about Files in units (Transfers, SIPs).

    """

    uuid = models.CharField(
        max_length=36, primary_key=True, db_column='fileUUID')
    sip = models.ForeignKey(
        SIP, db_column='sipUUID', to_field='uuid', null=True, blank=True)
    transfer = models.ForeignKey(
        Transfer, db_column='transferUUID', to_field='uuid', null=True,
        blank=True)

    # both actually `longblob` in the database
    originallocation = models.TextField(db_column='originalLocation')
    currentlocation = models.TextField(db_column='currentLocation', null=True)

    # In `archivematicaCommon/lib/databaseFunctions.py`, this is described as a
    # category used to group the file with others of the same kind.
    filegrpuse = models.CharField(
        max_length=50, db_column='fileGrpUse', default='Original')

    filegrpuuid = models.CharField(
        max_length=36L, db_column='fileGrpUUID', blank=True)
    checksum = models.CharField(
        max_length=100, db_column='checksum', blank=True)
    checksumtype = models.CharField(
        max_length=36, db_column='checksumType', blank=True)
    size = models.BigIntegerField(db_column='fileSize', null=True, blank=True)
    label = models.TextField(blank=True)
    enteredsystem = models.DateTimeField(
        db_column='enteredSystem', auto_now_add=True)
    removedtime = models.DateTimeField(
        db_column='removedTime', null=True, default=None)

    class Meta:
        db_table = u'Files'

    def __unicode__(self):
        return u'{uuid}: {originallocation} now at {currentlocation}'.format(
            uuid=self.uuid,
            originallocation=self.originallocation,
            currentlocation=self.currentlocation)


class FileFormatVersion(models.Model):
    """Link between a File and the FormatVersion (table `fpr_formatversion`) it
    is identified as.

    TODO? Replace this with a foreign key from File to FormatVersion.

    Example SQL::

        SELECT fv.pronom_id, fv.description
        FROM FilesIdentifiedIDs
        INNER JOIN fpr_formatversion AS fv
        ON fileID=fv.uuid;

    """

    id = models.AutoField(
        primary_key=True, db_column='pk', editable=False)
    file_uuid = models.ForeignKey(
        'File', db_column='fileUUID', to_field='uuid')
    format_version = models.ForeignKey(
        'fpr.FormatVersion', db_column='fileID', to_field='uuid')

    class Meta:
        db_table = u'FilesIdentifiedIDs'

    def __unicode__(self):
        return u'{file} is {format}'.format(file=self.file_uuid,
                                            format=self.format_version)


class Job(models.Model):
    """The jobs that make up a micro-service chain link, e.g., "Determine which
    files to identify" in micro-service "Identify file format".

    """

    jobuuid = UUIDField(db_column='jobUUID', primary_key=True)
    jobtype = models.CharField(max_length=250, db_column='jobType', blank=True)
    createdtime = models.DateTimeField(db_column='createdTime')
    createdtimedec = models.DecimalField(
        db_column='createdTimeDec', max_digits=26, decimal_places=10,
        default=0.0)
    directory = models.TextField(blank=True)

    # Foreign key to SIPs or Transfers
    sipuuid = models.CharField(max_length=36, db_column='SIPUUID')

    # Observed values: 'unitTransfer', 'unitSIP'
    unittype = models.CharField(
        max_length=50, db_column='unitType', blank=True)

    # Example values: 'Completed successfully', 'Failed', 'Awaiting decision'
    currentstep = models.CharField(
        max_length=50, db_column='currentStep', blank=True)

    # Example values: 'Normalize', 'Scan for viruses'
    microservicegroup = models.CharField(
        max_length=50, db_column='microserviceGroup', blank=True)

    hidden = models.BooleanField(default=False)
    microservicechainlink = models.ForeignKey(
        'MicroServiceChainLink', db_column='MicroServiceChainLinksPK',
        null=True, blank=True)
    subjobof = models.CharField(
        max_length=36, db_column='subJobOf', blank=True)

    class Meta:
        db_table = u'Jobs'


class Task(models.Model):
    """Represents a task, i.e., the execution of a specific program (Python or
    shell script), possibly against a specific file. Each job can have multiple
    tasks.

    """

    taskuuid = models.CharField(
        max_length=36, primary_key=True, db_column='taskUUID')
    job = models.ForeignKey('Job', db_column='jobuuid', to_field='jobuuid')
    createdtime = models.DateTimeField(db_column='createdTime')
    fileuuid = models.CharField(
        max_length=36, db_column='fileUUID', null=True, blank=True)

    # `filename` is actually stored as a `longblob` in the database, since
    # filenames may contain arbitrary non-unicode characters. Other blob and
    # binary fields have these types for the same reason. Note that Django
    # doesn't have a specific blob type, hence the use of the char field types
    # instead.
    filename = models.TextField(db_column='fileName', blank=True)

    # Name for the executable that performs the task. These strings are mapped
    # to specific Python or shell scripts in
    # MCPClient/lib/archivematicaClientModules
    execution = models.CharField(max_length=250, db_column='exec', blank=True)

    # `arguments` is actually a `varbinary(1000)` in the database.
    arguments = models.CharField(max_length=1000, blank=True)

    starttime = models.DateTimeField(
        db_column='startTime', null=True, default=None)
    endtime = models.DateTimeField(
        db_column='endTime', null=True, default=None)
    client = models.CharField(max_length=50, blank=True)

    # `stdout` and `stderror` are actually `longblobs` in the database
    stdout = models.TextField(db_column='stdOut', blank=True)
    stderror = models.TextField(db_column='stdError', blank=True)
    exitcode = models.BigIntegerField(
        db_column='exitCode', null=True, blank=True)

    class Meta:
        db_table = u'Tasks'


class Agent(models.Model):
    """PREMIS Agents created for the system.

    """

    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    identifiertype = models.TextField(
        verbose_name='Agent Identifier Type', null=True,
        db_column='agentIdentifierType')
    identifiervalue = models.TextField(
        verbose_name='Agent Identifier Value',
        help_text=('Used for premis:agentIdentifierValue and'
                   ' premis:linkingAgentIdentifierValue in the METS file.'),
        null=True, blank=False, db_column='agentIdentifierValue')
    name = models.TextField(
        verbose_name='Agent Name',
        help_text='Used for premis:agentName in the METS file.',
        null=True, blank=False, db_column='agentName')
    agenttype = models.TextField(db_column='agentType')

    class Meta:
        db_table = u'Agents'


class Report(models.Model):
    """Reports of failures to display.

    Note: the sole place where it appears that `Report` instances are created
    is in MCPClient/lib/clientScripts/emailFailReport.py.

    """

    id = models.AutoField(primary_key=True, db_column='pk')
    unittype = models.CharField(max_length=50, db_column='unitType')
    unitname = models.CharField(max_length=50, db_column='unitName')

    # Foreign key to SIP or Transfer
    unitidentifier = models.CharField(
        max_length=36, db_column='unitIdentifier')

    content = models.TextField(db_column='content')
    created = models.DateTimeField(db_column='created', auto_now_add=True)

    class Meta:
        db_table = u'Reports'


###############################################################################
# Rights Statement-related Models
###############################################################################

# There are 17 Rights Statement-related models, whose relations imply the
# following hierarchy.

# - Rights Statement (RS)
#   - 02m RS Copyright (C)
#     - 02m RS C Note
#     - 02m RS C Document Identifier
#   - 02m RS License (L)
#     - 02m RS L Note
#     - 02m RS L Document Identifier
#   - 02m RS Rights Granted (RG)
#     - 02m RS RG Restriction
#     - 02m RS RG Note
#   - 02m RS Statute Information (SI)
#     - 02m RS SI Note
#     - 02m RS S(I) Document Identifier
#   - 02m RS Other Rights Information (ORI)
#     - 02m RS OR(I) Document Identifier
#     - 02m RS ORI Note
#   - 02m RS Linking Agent Identifier


class RightsStatement(models.Model):
    """A statement of rights, as applied to a SIP, Transfer or File instance.

    """

    id = models.AutoField(primary_key=True, db_column='pk')
    metadataappliestotype = models.ForeignKey(
        MetadataAppliesToType, to_field='id',
        db_column='metadataAppliesToType')
    metadataappliestoidentifier = models.CharField(
        max_length=36, blank=True, db_column='metadataAppliesToidentifier')
    rightsstatementidentifiertype = models.TextField(
        db_column='rightsStatementIdentifierType', blank=True,
        verbose_name='Type')
    rightsstatementidentifiervalue = models.TextField(
        db_column='rightsStatementIdentifierValue', blank=True,
        verbose_name='Value')
    rightsholder = models.IntegerField(
        db_column='fkAgent', default=0, verbose_name='Rights holder')
    RIGHTS_BASIS_CHOICES = (
        ('Copyright', 'Copyright'),
        ('Statute', 'Statute'),
        ('License', 'License'),
        ('Donor', 'Donor'),
        ('Policy', 'Policy'),
        ('Other', 'Other')
    )
    rightsbasis = models.CharField(
        db_column='rightsBasis', choices=RIGHTS_BASIS_CHOICES, max_length=64,
        verbose_name='Basis', default='Copyright')
    status = models.CharField(
        db_column='status', max_length=8, choices=METADATA_STATUS,
        default=METADATA_STATUS_ORIGINAL)

    class Meta:
        db_table = u'RightsStatement'
        verbose_name = 'Rights Statement'

    def __unicode__(self):
        return u'{basis} for {unit} ({id})'.format(
            basis=self.rightsbasis, unit=self.metadataappliestoidentifier,
            id=self.id)


class RightsStatementCopyright(models.Model):
    """Each `RightsStatement` instance can have zero or many
    `RightsStatementCopyright` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatement = models.ForeignKey(
        RightsStatement, db_column='fkRightsStatement')
    copyrightstatus = models.TextField(
        db_column='copyrightStatus', verbose_name='Copyright status')
    copyrightjurisdiction = models.TextField(
        db_column='copyrightJurisdiction',
        verbose_name='Copyright jurisdiction')
    copyrightstatusdeterminationdate = models.TextField(
        db_column='copyrightStatusDeterminationDate', blank=True, null=True,
        verbose_name='Copyright determination date',
        help_text='Use ISO 8061 (YYYY-MM-DD)')
    copyrightapplicablestartdate = models.TextField(
        db_column='copyrightApplicableStartDate', blank=True, null=True,
        verbose_name='Copyright start date',
        help_text='Use ISO 8061 (YYYY-MM-DD)')
    copyrightapplicableenddate = models.TextField(
        db_column='copyrightApplicableEndDate', blank=True, null=True,
        verbose_name='Copyright end date',
        help_text='Use ISO 8061 (YYYY-MM-DD)')
    copyrightenddateopen = models.BooleanField(
        default=False, db_column='copyrightApplicableEndDateOpen',
        verbose_name='Open End Date', help_text='Indicate end date is open')

    class Meta:
        db_table = u'RightsStatementCopyright'
        verbose_name = 'Rights: Copyright'


class RightsStatementCopyrightDocumentationIdentifier(models.Model):
    """Each `RightsStatementCopyright` instance can have zero or many
    `RightsStatementCopyrightDocumentationIdentifier` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightscopyright = models.ForeignKey(
        RightsStatementCopyright,
        db_column='fkRightsStatementCopyrightInformation')
    copyrightdocumentationidentifiertype = models.TextField(
        db_column='copyrightDocumentationIdentifierType',
        verbose_name='Copyright document identification type')
    copyrightdocumentationidentifiervalue = models.TextField(
        db_column='copyrightDocumentationIdentifierValue',
        verbose_name='Copyright document identification value')
    copyrightdocumentationidentifierrole = models.TextField(
        db_column='copyrightDocumentationIdentifierRole', null=True,
        blank=True, verbose_name='Copyright document identification role')

    class Meta:
        db_table = u'RightsStatementCopyrightDocumentationIdentifier'
        verbose_name = 'Rights: Copyright: Docs ID'


class RightsStatementCopyrightNote(models.Model):
    """Each `RightsStatementCopyright` instance can have zero or many
    `RightsStatementCopyrightNote` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightscopyright = models.ForeignKey(
        RightsStatementCopyright,
        db_column='fkRightsStatementCopyrightInformation')
    copyrightnote = models.TextField(
        db_column='copyrightNote', verbose_name='Copyright note')

    class Meta:
        db_table = u'RightsStatementCopyrightNote'
        verbose_name = 'Rights: Copyright: Note'


class RightsStatementLicense(models.Model):
    """Each `RightsStatement` instance can have zero or many
    `RightsStatementLicense` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatement = models.ForeignKey(
        RightsStatement, db_column='fkRightsStatement')
    licenseterms = models.TextField(
        db_column='licenseTerms', blank=True, null=True,
        verbose_name='License terms')
    licenseapplicablestartdate = models.TextField(
        db_column='licenseApplicableStartDate', blank=True, null=True,
        verbose_name='License start date',
        help_text='Use ISO 8061 (YYYY-MM-DD)')
    licenseapplicableenddate = models.TextField(
        db_column='licenseApplicableEndDate', blank=True, null=True,
        verbose_name='License end date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    licenseenddateopen = models.BooleanField(
        default=False, db_column='licenseApplicableEndDateOpen',
        verbose_name='Open End Date', help_text='Indicate end date is open')

    class Meta:
        db_table = u'RightsStatementLicense'
        verbose_name = 'Rights: License'


class RightsStatementLicenseDocumentationIdentifier(models.Model):
    """Each `RightsStatementLicense` instance can have zero or many
    `RightsStatementLicenseDocumentationIdentifier` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementlicense = models.ForeignKey(
        RightsStatementLicense, db_column='fkRightsStatementLicense')
    licensedocumentationidentifiertype = models.TextField(
        db_column='licenseDocumentationIdentifierType',
        verbose_name='License documentation identification type')
    licensedocumentationidentifiervalue = models.TextField(
        db_column='licenseDocumentationIdentifierValue',
        verbose_name='License documentation identification value')
    licensedocumentationidentifierrole = models.TextField(
        db_column='licenseDocumentationIdentifierRole', blank=True, null=True,
        verbose_name='License document identification role')

    class Meta:
        db_table = u'RightsStatementLicenseDocumentationIdentifier'
        verbose_name = 'Rights: License: Docs ID'


class RightsStatementLicenseNote(models.Model):
    """Each `RightsStatementLicense` instance can have zero or many
    `RightsStatementLicenseNote` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementlicense = models.ForeignKey(
        RightsStatementLicense, db_column='fkRightsStatementLicense')
    licensenote = models.TextField(
        db_column='licenseNote', verbose_name='License note')

    class Meta:
        db_table = u'RightsStatementLicenseNote'
        verbose_name = 'Rights: License: Note'


class RightsStatementRightsGranted(models.Model):
    """Each `RightsStatement` instance can have zero or many
    `RightsStatementRightsGranted` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatement = models.ForeignKey(
        RightsStatement, db_column='fkRightsStatement')
    act = models.TextField(db_column='act')
    startdate = models.TextField(
        db_column='startDate', verbose_name='Start',
        help_text='Use ISO 8061 (YYYY-MM-DD)', blank=True, null=True)
    enddate = models.TextField(
        db_column='endDate', verbose_name='End',
        help_text='Use ISO 8061 (YYYY-MM-DD)', blank=True, null=True)
    enddateopen = models.BooleanField(
        default=False, db_column='endDateOpen', verbose_name='Open End Date',
        help_text='Indicate end date is open')

    class Meta:
        db_table = u'RightsStatementRightsGranted'
        verbose_name = 'Rights: Granted'


class RightsStatementRightsGrantedNote(models.Model):
    """Each `RightsStatementRightsGranted` instance can have zero or many
    `RightsStatementRightsGrantedNote` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsgranted = models.ForeignKey(
        RightsStatementRightsGranted, related_name='notes',
        db_column='fkRightsStatementRightsGranted')
    rightsgrantednote = models.TextField(
        db_column='rightsGrantedNote', verbose_name='Rights note')

    class Meta:
        db_table = u'RightsStatementRightsGrantedNote'
        verbose_name = 'Rights: Granted: Note'


class RightsStatementRightsGrantedRestriction(models.Model):
    """Each `RightsStatementRightsGranted` instance can have zero or many
    `RightsStatementRightsGrantedRestriction` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk')
    rightsgranted = models.ForeignKey(
        RightsStatementRightsGranted, related_name='restrictions',
        db_column='fkRightsStatementRightsGranted')
    restriction = models.TextField(db_column='restriction')

    class Meta:
        db_table = u'RightsStatementRightsGrantedRestriction'
        verbose_name = 'Rights: Granted: Restriction'


class RightsStatementStatuteInformation(models.Model):
    """Each `RightsStatement` instance can have zero or many
    `RightsStatementStatuteInformation` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatement = models.ForeignKey(
        RightsStatement, db_column='fkRightsStatement')
    statutejurisdiction = models.TextField(
        db_column='statuteJurisdiction', verbose_name='Statute jurisdiction')
    statutecitation = models.TextField(
        db_column='statuteCitation', verbose_name='Statute citation')
    statutedeterminationdate = models.TextField(
        db_column='statuteInformationDeterminationDate',
        verbose_name='Statute determination date',
        help_text='Use ISO 8061 (YYYY-MM-DD)', blank=True, null=True)
    statuteapplicablestartdate = models.TextField(
        db_column='statuteApplicableStartDate', blank=True, null=True,
        verbose_name='Statute start date',
        help_text='Use ISO 8061 (YYYY-MM-DD)')
    statuteapplicableenddate = models.TextField(
        db_column='statuteApplicableEndDate', blank=True, null=True,
        verbose_name='Statute end date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    statuteenddateopen = models.BooleanField(
        default=False, db_column='statuteApplicableEndDateOpen',
        verbose_name='Open End Date', help_text='Indicate end date is open')

    class Meta:
        db_table = u'RightsStatementStatuteInformation'
        verbose_name = 'Rights: Statute'


class RightsStatementStatuteInformationNote(models.Model):
    """Each `RightsStatementStatuteInformation` instance can have zero or many
    `RightsStatementStatuteInformationNote` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatementstatute = models.ForeignKey(
        RightsStatementStatuteInformation,
        db_column='fkRightsStatementStatuteInformation')
    statutenote = models.TextField(
        db_column='statuteNote', verbose_name='Statute note')

    class Meta:
        db_table = u'RightsStatementStatuteInformationNote'
        verbose_name = 'Rights: Statute: Note'


class RightsStatementStatuteDocumentationIdentifier(models.Model):
    """Each `RightsStatementStatuteInformation` instance can have zero or many
    `RightsStatementStatuteDocumentationIdentifier` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementstatute = models.ForeignKey(
        RightsStatementStatuteInformation,
        db_column='fkRightsStatementStatuteInformation')
    statutedocumentationidentifiertype = models.TextField(
        db_column='statuteDocumentationIdentifierType',
        verbose_name='Statute document identification type')
    statutedocumentationidentifiervalue = models.TextField(
        db_column='statuteDocumentationIdentifierValue',
        verbose_name='Statute document identification value')
    statutedocumentationidentifierrole = models.TextField(
        db_column='statuteDocumentationIdentifierRole',
        blank=True, null=True,
        verbose_name='Statute document identification role')

    class Meta:
        db_table = u'RightsStatementStatuteDocumentationIdentifier'
        verbose_name = 'Rights: Statute: Docs ID'


class RightsStatementOtherRightsInformation(models.Model):
    """Each `RightsStatement` instance can have zero or many
    `RightsStatementOtherRightsInformation` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatement = models.ForeignKey(
        RightsStatement, db_column='fkRightsStatement')
    otherrightsbasis = models.TextField(
        db_column='otherRightsBasis', verbose_name='Other rights basis',
        default='Other')
    otherrightsapplicablestartdate = models.TextField(
        db_column='otherRightsApplicableStartDate', blank=True, null=True,
        verbose_name='Other rights start date',
        help_text='Use ISO 8061 (YYYY-MM-DD)')
    otherrightsapplicableenddate = models.TextField(
        db_column='otherRightsApplicableEndDate', blank=True, null=True,
        verbose_name='Other rights end date',
        help_text='Use ISO 8061 (YYYY-MM-DD)')
    otherrightsenddateopen = models.BooleanField(
        default=False, db_column='otherRightsApplicableEndDateOpen',
        verbose_name='Open End Date', help_text='Indicate end date is open')

    class Meta:
        db_table = u'RightsStatementOtherRightsInformation'
        verbose_name = 'Rights: Other'


class RightsStatementOtherRightsDocumentationIdentifier(models.Model):
    """Each `RightsStatementOtherRightsInformation` instance can have zero or
    many `RightsStatementOtherRightsDocumentationIdentifier` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementotherrights = models.ForeignKey(
        RightsStatementOtherRightsInformation,
        db_column='fkRightsStatementOtherRightsInformation')
    otherrightsdocumentationidentifiertype = models.TextField(
        db_column='otherRightsDocumentationIdentifierType',
        verbose_name='Other rights document identification type')
    otherrightsdocumentationidentifiervalue = models.TextField(
        db_column='otherRightsDocumentationIdentifierValue',
        verbose_name='Other right document identification value')
    otherrightsdocumentationidentifierrole = models.TextField(
        db_column='otherRightsDocumentationIdentifierRole',
        blank=True, null=True,
        verbose_name='Other rights document identification role')

    class Meta:
        db_table = u'RightsStatementOtherRightsDocumentationIdentifier'
        verbose_name = 'Rights: Other: Docs ID'


class RightsStatementOtherRightsInformationNote(models.Model):
    """Each `RightsStatementOtherRightsInformation` instance can have zero or
    many `RightsStatementOtherRightsInformationNote` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatementotherrights = models.ForeignKey(
        RightsStatementOtherRightsInformation,
        db_column='fkRightsStatementOtherRightsInformation')
    otherrightsnote = models.TextField(
        db_column='otherRightsNote', verbose_name='Other rights note')

    class Meta:
        db_table = u'RightsStatementOtherRightsNote'
        verbose_name = 'Rights: Other: Note'


class RightsStatementLinkingAgentIdentifier(models.Model):
    """Each `RightsStatement` instance can have zero or many
    `RightsStatementLinkingAgentIdentifier` instances.

    """

    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatement = models.ForeignKey(
        RightsStatement, db_column='fkRightsStatement')
    linkingagentidentifiertype = models.TextField(
        db_column='linkingAgentIdentifierType', verbose_name='Linking Agent',
        blank=True)
    linkingagentidentifiervalue = models.TextField(
        db_column='linkingAgentIdentifierValue',
        verbose_name='Linking Agent Value', blank=True)

    class Meta:
        db_table = u'RightsStatementLinkingAgentIdentifier'
        verbose_name = 'Rights: Agent'


###############################################################################
# MCP data interoperability
###############################################################################


class MicroServiceChain(models.Model):
    """A micro-service chain is conceptually a sequence of micro-service
    (links) that determine how the contents of a watched directory are
    processed.

    Example SQL to get the starting link and chain description for the
    "Standard Transfer" watched directory::

        SELECT link.microserviceGroup as `starting link micro-service group`,
            ch.description as `chain description`
            FROM WatchedDirectories
            INNER JOIN MicroServiceChains AS ch
            ON chain=ch.pk
            INNER JOIN MicroServiceChainLinks AS link
            ON ch.startingLink=link.pk
            WHERE watchedDirectoryPath LIKE
            '%activeTransfers/standardTransfer%';

    """

    id = UUIDPkField()
    startinglink = models.ForeignKey(
        'MicroServiceChainLink', db_column='startingLink')
    description = models.TextField(db_column='description')
    replaces = models.ForeignKey(
        'self', related_name='replaced_by', db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta:
        db_table = u'MicroServiceChains'

    def __unicode__(self):
        return u'MicroServiceChain ID: {uuid}; {desc}'.format(
            uuid=self.id,
            desc=self.description)


class MicroServiceChainLink(models.Model):
    """A micro-service chain link is a micro-service. In the dashboard's
    Transfer pane, for example, the "Micro-service: Validation" row corresponds
    to a MS chain link.

    """

    id = UUIDPkField()
    currenttask = models.ForeignKey('TaskConfig', db_column='currentTask')

    # Note: it is not necessary that a link have a default next link.
    defaultnextchainlink = models.ForeignKey(
        'self', db_column='defaultNextChainLink', null=True, blank=True)

    microservicegroup = models.CharField(
        max_length=50, db_column='microserviceGroup')
    reloadfilelist = models.BooleanField(
        default=True, db_column='reloadFileList')
    defaultexitmessage = models.CharField(
        max_length=36, db_column='defaultExitMessage', default='Failed')
    replaces = models.ForeignKey(
        'self', related_name='replaced_by', db_column='replaces', null=True,
        blank=True)
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta:
        db_table = u'MicroServiceChainLinks'

    def __unicode__(self):
        return u'MicroServiceChainLink ID: {}'.format(self.id)


class MicroServiceChainLinkExitCode(models.Model):
    """Link exit codes control what the next link will be when the current link
    is finished its work, given a certain exit code. To see the mapping in the
    DB::

        SELECT microServiceChainLink, exitCode, nextMicroserviceChainLink
        FROM MicroServiceChainLinksExitCodes
        ORDER BY microServiceChainLink;

    See `MCPServer/lib/jobChainLink.py`.

    """

    id = UUIDPkField()
    microservicechainlink = models.ForeignKey(
        'MicroServiceChainLink', related_name='exit_codes',
        db_column='microServiceChainLink')
    exitcode = models.IntegerField(db_column='exitCode', default=0)
    nextmicroservicechainlink = models.ForeignKey(
        'MicroServiceChainLink', related_name='parent_exit_codes+',
        db_column='nextMicroServiceChainLink', null=True, blank=True)
    exitmessage = models.CharField(
        max_length=50, db_column='exitMessage',
        default='Completed successfully')
    replaces = models.ForeignKey(
        'self', related_name='replaced_by', null=True, blank=True,
        db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta:
        db_table = u'MicroServiceChainLinksExitCodes'


class MicroServiceChainChoice(models.Model):
    """The MS Chain Choice model encodes a choice at a given link to activate a
    new chain.

    For example, the user may be given the choice to "Approve normalization",
    with the following options: "Redo", "Approve", or "Reject". This choice is
    encoded as `MicroServiceChainChoice` instances that map a single MS Chain
    Link to distinct MS Chains, each representing one of the possible options::

        SELECT TasksConfigs.description AS `link description (choice)`,
            MicroServiceChains.description `chain description (option)`
            FROM MicroServiceChainChoice
            JOIN MicroServiceChains
            ON MicroServiceChainChoice.chainAvailable = MicroServiceChains.pk
            JOIN MicroServiceChainLinks
            ON MicroServiceChainLinks.pk =
                MicroServiceChainChoice.choiceAvailableAtLink
            JOIN TasksConfigs
            ON TasksConfigs.pk = MicroServiceChainLinks.currentTask
            ORDER BY choiceAvailableAtLink DESC;

    """

    id = UUIDPkField()
    choiceavailableatlink = models.ForeignKey(
        'MicroServiceChainLink', db_column='choiceAvailableAtLink')
    chainavailable = models.ForeignKey(
        'MicroServiceChain', db_column='chainAvailable')
    replaces = models.ForeignKey(
        'self', related_name='replaced_by', null=True, blank=True,
        db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta:
        db_table = u'MicroServiceChainChoice'

    def __unicode__(self):
        return u'MicroServiceChainChoice ID: {uuid} ({chain} at {choice})'\
            .format(
                uuid=self.id,
                chain=self.chainavailable,
                choice=self.choiceavailableatlink)


class MicroServiceChoiceReplacementDic(models.Model):
    """The `replacementdic` attribute is a flat JSON object. A single MS chain
    link may have many of these "replacement dicts" but the `description`
    attribute serves to distinguish them.

    """

    id = UUIDPkField()
    choiceavailableatlink = models.ForeignKey(
        'MicroServiceChainLink', db_column='choiceAvailableAtLink')
    description = models.TextField(
        db_column='description', verbose_name='Description')
    replacementdic = models.TextField(
        db_column='replacementDic', verbose_name='Configuration')
    replaces = models.ForeignKey(
        'self', related_name='replaced_by', null=True, blank=True,
        db_column='replaces')
    lastmodified = models.DateTimeField(
        db_column='lastModified', auto_now=True)

    def clean(self):
        error = None
        try:
            config = ast.literal_eval(self.replacementdic)
        except ValueError:
            error = 'Invalid syntax.'
        except SyntaxError:
            error = 'Invalid syntax.'
        if error is None and not type(config) is dict:
            error = 'Invalid syntax.'
        if error is not None:
            raise forms.ValidationError(error)

    class Meta:
        db_table = u'MicroServiceChoiceReplacementDic'


class TaskType(models.Model):
    """Collectively, the `TaskType` models simply define a closed vocabulary of
    task types. An example task type is 'for each file'. The `jobChainLink`
    makes use of these.

    TODO: write a better description of what purpose task types serve exactly.

    """

    id = UUIDPkField()
    description = models.TextField(blank=True)
    replaces = models.ForeignKey(
        'self', related_name='replaced_by', null=True, blank=True,
        db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta:
        db_table = 'TaskTypes'

    def __unicode__(self):
        return u'TaskType ID: {}, desc: {}'.format(self.id, self.description)


class TaskConfig(models.Model):
    """Represents a single task within a micro-service chain link, for example,
    "Job: Approve standard transfer".

    To get the standard transfer's chain, that chain's starting link, and that
    link's current task's description and type::

        SELECT
            currTaskType.description as `current task type`,
            currTask.description as `current task description`,
            link.microserviceGroup as `starting link micro-service group`,
            ch.description as `chain description`
            FROM WatchedDirectories
            INNER JOIN MicroServiceChains AS ch
            ON chain=ch.pk
            INNER JOIN MicroServiceChainLinks AS link
            ON ch.startingLink=link.pk
            INNER JOIN TasksConfigs AS currTask
            ON link.currentTask=currTask.pk
            INNER JOIN TaskTypes AS currTaskType
            ON currTask.taskType=currTaskType.pk
            WHERE watchedDirectoryPath LIKE
                '%activeTransfers/standardTransfer%';

    """

    id = UUIDPkField()
    tasktype = models.ForeignKey('TaskType', db_column='taskType')
    # Foreign key to table depending on TaskType
    tasktypepkreference = models.CharField(
        max_length=36, db_column='taskTypePKReference', null=True, blank=True,
        default=None)
    description = models.TextField(db_column='description')
    replaces = models.ForeignKey(
        'self', related_name='replaced_by', null=True, blank=True,
        db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta:
        db_table = u'TasksConfigs'

    def __unicode__(self):
        return u'TaskConfig ID: {}, desc: {}'.format(self.id, self.description)


class StandardTaskConfig(models.Model):
    """The `execute` attribute holds the name of an executable; the file
    `MCPClient/lib/archivematicaClientModules` maps these `execute` values to
    the paths of the relevant shell or Python executables.

    """

    id = UUIDPkField()

    # The `execute` attribute holds the name of an executable; the file
    # `MCPClient/lib/archivematicaClientModules` maps these `execute` values to
    # the paths of the relevant shell or Python executables.
    execute = models.CharField(max_length=250, db_column='execute')

    # The `arguments` attribute is a string of space-delimited, "-enclosed
    # strings that are the command-line arguments to the executable. For
    # example, the `validateFile.py` executable expects 3 command-line
    # arguments, so the corresponding `arguments` value is
    # `"%relativeLocation%" "%fileUUID%" "%SIPUUID%"`. As illustrated here,
    # each string in `arguments` can contain %-enclosed replacement variables.
    arguments = models.TextField(db_column='arguments')

    # If present, then the executable will only be called against entities
    # within the referenced sub-directory. See, for example,
    # MCPServer/lib/linkTaskManagerFiles.py.
    filter_subdir = models.CharField(
        max_length=50, db_column='filterSubDir', null=True, blank=True)

    # Filters that ensure the executable only acts on files that start or end
    # with the values in the following two attributes. Only usage observed is
    # that certain executables only act on files that end with 'mets.xml'.
    filter_file_start = models.CharField(
        max_length=50, db_column='filterFileStart', null=True, blank=True)
    filter_file_end = models.CharField(
        max_length=50, db_column='filterFileEnd', null=True, blank=True)

    requires_output_lock = models.BooleanField(
        db_column='requiresOutputLock', default=False)
    stdout_file = models.CharField(
        max_length=250, db_column='standardOutputFile', null=True, blank=True)
    stderr_file = models.CharField(
        max_length=250, db_column='standardErrorFile', null=True, blank=True)
    replaces = models.ForeignKey(
        'self', related_name='replaced_by', null=True, blank=True,
        db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta:
        db_table = u'StandardTasksConfigs'


class TaskConfigAssignMagicLink(models.Model):
    """Unclear what this model is for. It seems only to be used in
    `MCPServer/lib/linkTaskManagerAssignMagicLink.py`.

    """

    id = UUIDPkField()
    execute = models.ForeignKey(
        'MicroServiceChainLink', null=True, db_column='execute', blank=True)
    replaces = models.ForeignKey(
        'self', related_name='replaced_by', null=True, blank=True,
        db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta(object):
        db_table = u'TasksConfigsAssignMagicLink'


class TaskConfigSetUnitVariable(models.Model):
    """This model causes `UnitVariable` instances to be updated or created. See
    `MCPServer/lib/linkTaskManagerSetUnitVariable.py` and
    `MCPServer/lib/unit.py`.

    """

    id = UUIDPkField()
    variable = models.TextField(blank=True)
    variablevalue = models.TextField(
        null=True, blank=True, db_column='variableValue')
    microservicechainlink = models.ForeignKey(
        'MicroServiceChainLink', null=True, db_column='microServiceChainLink')
    createdtime = models.DateTimeField(
        db_column='createdTime', auto_now_add=True)
    updatedtime = models.DateTimeField(db_column='updatedTime', auto_now=True)

    class Meta(object):
        db_table = u'TasksConfigsSetUnitVariable'


class TaskConfigUnitVariableLinkPull(models.Model):
    id = UUIDPkField()
    variable = models.TextField(blank=True)
    variablevalue = models.TextField(
        null=True, blank=True, db_column='variableValue')
    defaultmicroservicechainlink = models.ForeignKey(
        'MicroServiceChainLink', null=True,
        db_column='defaultMicroServiceChainLink')
    createdtime = models.DateTimeField(
        db_column='createdTime', auto_now_add=True)
    updatedtime = models.DateTimeField(db_column='updatedTime', auto_now=True)

    class Meta(object):
        db_table = u'TasksConfigsUnitVariableLinkPull'


class UnitVariable(models.Model):
    """Maps a variable name (`variable`) to a value (`variablevalue`) for a
    given unit (i.e., a SIP or a Transfer).

    """

    id = UUIDPkField()
    unittype = models.CharField(
        max_length=50, null=True, blank=True, db_column='unitType')
    unituuid = models.CharField(
        max_length=36, null=True,
        help_text='Semantically a foreign key to SIP or Transfer',
        db_column='unitUUID')
    variable = models.TextField(null=True, db_column='variable')
    variablevalue = models.TextField(null=True, db_column='variableValue')
    microservicechainlink = models.ForeignKey(
        'MicroServiceChainLink', null=True, blank=True,
        help_text=('UUID of the MicroServiceChainLink if used in task type'
                   ' linkTaskManagerUnitVariableLinkPull'),
        db_column='microServiceChainLink')
    createdtime = models.DateTimeField(
        db_column='createdTime', auto_now_add=True)
    updatedtime = models.DateTimeField(db_column='updatedTime', auto_now=True)

    class Meta:
        db_table = u'UnitVariables'


###############################################################################
# END MCP data interoperability
###############################################################################


class AtkDIPObjectResourcePairing(models.Model):
    """Note: "Atk" stands for "Archivists' Toolkit".

    """

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
        return ('ArchivesSpace Pairing<dipuuid: {s.dipuuid}, resourceid:'
                ' {s.resourceid}>'.format(s=self))

    class Meta:
        db_table = u'ArchivesSpaceDIPObjectResourcePairing'
        # Table name length is fine, but if the verbose name is too
        # long it can result in confusing errors when trying to
        # set up permissions: https://code.djangoproject.com/ticket/18866
        verbose_name = u'ASDIPObjectResourcePairing'


class ArchivesSpaceDOComponent(models.Model):
    """Represents a digital object component to be created in ArchivesSpace at
    the time an AIP is stored by Archivematica.

    In ArchivesSpace, a digital object component is meant to be parented to a
    digital object record. The workflow in use by the appraisal tab doesn't
    expose digital objects to the user, just components; one digital object
    should be created as a parent for these components before creating the
    components themselves.

    """

    sip = models.ForeignKey('SIP', to_field='uuid', null=True)
    resourceid = models.CharField(max_length=150)
    label = models.CharField(max_length=255, blank=True)
    title = models.TextField(blank=True)
    started = models.BooleanField(
        default=False,
        help_text=('Whether or not a SIP has been started using files in this'
                   ' digital object component.'))
    digitalobjectid = models.CharField(
        max_length=150, blank=True,
        help_text=('ID in the remote ArchivesSpace system of the digital'
                   ' object to which this object is parented.'))
    remoteid = models.CharField(
        max_length=150, blank=True,
        help_text=('ID in the remote ArchivesSpace system, after component has'
                   ' been created.'))


class TransferMetadataSet(models.Model):
    id = UUIDPkField()
    createdtime = models.DateTimeField(
        db_column='createdTime', auto_now_add=True)
    createdbyuserid = models.IntegerField(db_column='createdByUserID')

    class Meta:
        db_table = u'TransferMetadataSets'


class TransferMetadataField(models.Model):
    """These models define the fields that are displayed at
    `/transfer/component/<uuid>`

    """

    id = UUIDPkField()
    createdtime = models.DateTimeField(
        db_column='createdTime', auto_now_add=True)
    fieldlabel = models.CharField(
        max_length=50, blank=True, db_column='fieldLabel')
    fieldname = models.CharField(max_length=50, db_column='fieldName')
    fieldtype = models.CharField(max_length=50, db_column='fieldType')
    optiontaxonomy = models.ForeignKey(
        'Taxonomy', db_column='optionTaxonomyUUID', to_field='id', null=True)
    sortorder = models.IntegerField(default=0, db_column='sortOrder')

    class Meta:
        db_table = u'TransferMetadataFields'

    def __unicode__(self):
        return self.fieldlabel


class TransferMetadataFieldValue(models.Model):
    """Holds the value for a given field of a transfer metadata set.

    """

    id = UUIDPkField()
    createdtime = models.DateTimeField(
        db_column='createdTime', auto_now_add=True)
    set = models.ForeignKey(
        'TransferMetadataSet', db_column='setUUID', to_field='id')
    field = models.ForeignKey(
        'TransferMetadataField', db_column='fieldUUID', to_field='id')
    fieldvalue = models.TextField(blank=True, db_column='fieldValue')

    class Meta:
        db_table = u'TransferMetadataFieldValues'


# Taxonomies and their field definitions are in separate tables
# to leave room for future expansion. The possible taxonomy terms are
# designed to be editable, and forms to do so exist. (Forms for editing and
# defining new fields are present in the code but currently disabled.)
class Taxonomy(models.Model):
    id = UUIDPkField()
    createdtime = models.DateTimeField(
        db_column='createdTime', auto_now_add=True)
    name = models.CharField(max_length=255, blank=True, db_column='name')
    type = models.CharField(max_length=50, default='open')

    class Meta:
        db_table = u'Taxonomies'

    def __unicode__(self):
        return self.name


class TaxonomyTerm(models.Model):
    id = UUIDPkField()
    createdtime = models.DateTimeField(
        db_column='createdTime', auto_now_add=True)
    taxonomy = models.ForeignKey(
        'Taxonomy', db_column='taxonomyUUID', to_field='id')
    term = models.CharField(max_length=255, db_column='term')

    class Meta:
        db_table = u'TaxonomyTerms'

    def __unicode__(self):
        return self.term


class WatchedDirectory(models.Model):
    """The watched directories are those that Archivematica watches. When
    something changes in these directories, the `WatchedDirectory` activates a
    `MicroServiceChain` instance. See `MCPServer/lib/archivematicaMCP.py`
    and `MCPServer/lib/watchDirectory.py`.

    """

    id = UUIDPkField()
    watched_directory_path = models.TextField(
        null=True, blank=True, db_column='watchedDirectoryPath')
    chain = models.ForeignKey(
        'MicroServiceChain', null=True, db_column='chain')
    only_act_on_directories = models.BooleanField(
        default=True, db_column='onlyActOnDirectories')
    expected_type = models.ForeignKey(
        'WatchedDirectoryExpectedType', null=True, db_column='expectedType')
    replaces = models.ForeignKey(
        'WatchedDirectory', null=True, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta(object):
        db_table = u"WatchedDirectories"


class WatchedDirectoryExpectedType(models.Model):
    """One of 'SIP', 'DIP' or 'Transfer'.

    """

    id = UUIDPkField()
    description = models.TextField(null=True)
    replaces = models.ForeignKey(
        'WatchedDirectoryExpectedType', null=True, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta(object):
        db_table = u"WatchedDirectoriesExpectedTypes"


class FPCommandOutput(models.Model):
    file = models.ForeignKey('File', db_column='fileUUID', to_field='uuid')
    content = models.TextField(null=True)
    rule = models.ForeignKey(
        'fpr.FPRule', db_column='ruleUUID', to_field='uuid')

    class Meta(object):
        db_table = u'FPCommandOutput'

    def __unicode__(self):
        return u'<file: {file}; rule: {rule}; content: {content}'.format(
            file=self.file, rule=self.rule, content=self.content[:20])


class FileID(models.Model):
    """This table duplicates file ID values from FPR formats. It predates the
    current FPR tables.

    This table may be removed in the future.

    """

    id = models.AutoField(primary_key=True, db_column='pk')
    file = models.ForeignKey(
        'File', null=True, db_column='fileUUID', blank=True)
    format_name = models.TextField(db_column='formatName', blank=True)
    format_version = models.TextField(db_column='formatVersion', blank=True)
    format_registry_name = models.TextField(
        db_column='formatRegistryName', blank=True)
    format_registry_key = models.TextField(
        db_column='formatRegistryKey', blank=True)

    class Meta:
        db_table = 'FilesIDs'


class LevelOfDescription(models.Model):
    id = UUIDPkField()
    # Seems long, but AtoM allows this much.
    name = models.CharField(max_length='1024')
    # sortorder should be unique, but is not defined so here to enable swapping
    sortorder = models.IntegerField(default=0, db_column='sortOrder')

    def __unicode__(self):
        return u'{i.sortorder}: {i.name}'.format(i=self)
