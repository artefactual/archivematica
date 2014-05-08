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

# Core Django, alphabetical by import source
from django.db import models
from django import forms

# Third party dependencies, alphabetical by import source
from django_extensions.db.fields import UUIDField

# This project, alphabetical by import source
from contrib import utils
import main

class UUIDPkField(UUIDField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 36)
        kwargs['primary_key'] = True
        kwargs['db_column'] = 'pk'
        super(UUIDPkField, self).__init__(*args, **kwargs)

class DashboardSetting(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    name = models.CharField(max_length=255, db_column='name')
    value = models.TextField(db_column='value', blank=True)

    class Meta:
        db_table = u'DashboardSettings'

class Access(models.Model):
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
    statuscode = models.IntegerField(null=True, db_column='statusCode', blank=True)
    # Rsync exit code
    exitcode = models.IntegerField(null=True, db_column='exitCode', blank=True)
    # Timestamps
    createdtime = models.DateTimeField(db_column='createdTime', auto_now_add=True)
    updatedtime = models.DateTimeField(db_column='updatedTime', auto_now=True)

    class Meta:
        db_table = u'Accesses'

    def get_title(self):
        try:
            jobs = main.models.Job.objects.filter(sipuuid=self.sipuuid, subjobof='')
            return utils.get_directory_name_from_job(jobs[0])
        except:
            return 'N/A'


class DublinCore(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    metadataappliestotype = models.CharField(max_length=36, db_column='metadataAppliesToType')
    metadataappliestoidentifier = models.CharField(max_length=36, blank=True, null=True, db_column='metadataAppliesToidentifier')
    title = models.CharField(max_length=255, db_column='title', blank=True, null=True)
    is_part_of = models.CharField(verbose_name='Part of AIC', help_text='Optional: leave blank if unsure', max_length=255, db_column='isPartOf', blank=True, null=True)
    creator = models.CharField(max_length=255, db_column='creator', blank=True, null=True)
    subject = models.CharField(max_length=255, db_column='subject', blank=True, null=True)
    description = models.TextField(db_column='description', blank=True, null=True)
    publisher = models.CharField(max_length=255, db_column='publisher', blank=True, null=True)
    contributor = models.CharField(max_length=255, db_column='contributor', blank=True, null=True)
    date = models.CharField(help_text='Use ISO 8061 (YYYY-MM-DD or YYYY-MM-DD/YYYY-MM-DD)', max_length=255, db_column='date', blank=True, null=True)
    type = models.CharField(max_length=255, db_column='type', blank=True, null=True)
    format = models.CharField(max_length=255, db_column='format', blank=True, null=True)
    identifier = models.CharField(max_length=255, db_column='identifier', blank=True, null=True)
    source = models.CharField(max_length=255, db_column='source', blank=True, null=True)
    relation = models.CharField(max_length=255, db_column='relation', blank=True, null=True)
    language = models.CharField(help_text='Use ISO 639', max_length=255, db_column='language', blank=True, null=True)
    coverage = models.CharField(max_length=255, db_column='coverage', blank=True, null=True)
    rights = models.TextField(db_column='rights', blank=True, null=True)

    class Meta:
        db_table = u'Dublincore'

    def __unicode__(self):
        if self.title:
            return u'%s' % self.title
        else:
            return u'Untitled'

class MetadataAppliesToType(models.Model):
    id = UUIDPkField()
    description = models.CharField(max_length=50, db_column='description')
    replaces = models.CharField(max_length=36, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta:
        db_table = u'MetadataAppliesToTypes'


class Event(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    event_id = UUIDField(auto=False, null=True, unique=True, db_column='eventIdentifierUUID')
    file_uuid = models.ForeignKey('File', db_column='fileUUID', to_field='uuid', null=True, blank=True)
    event_type = models.CharField(max_length=256, db_column='eventType')
    event_datetime = models.DateTimeField(db_column='eventDateTime')
    event_detail = models.TextField(db_column='eventDetail')
    event_outcome = models.CharField(max_length=256, db_column='eventOutcome')
    event_outcome_detail = models.TextField(db_column='eventOutcomeDetailNote')
    linking_agent = models.ForeignKey('Agent', db_column='linkingAgentIdentifier')

    class Meta:
        db_table = u'Events'

    def __unicode__(self):
        return u"{event_type} event on {file} ({event_detail})".format(
            event_type=self.event_type,
            file=self.file_uuid,
            event_detail=self.event_detail)


class Derivation(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    source_file = models.ForeignKey('File', db_column='sourceFileUUID', to_field='uuid', related_name='derived_file_set', null=True)
    derived_file = models.ForeignKey('File', db_column='derivedFileUUID', to_field='uuid', related_name='original_file_set', null=True)
    event = models.ForeignKey(Event, db_column='relatedEventUUID', to_field='event_id', null=True)

    class Meta:
        db_table=u'Derivations'

    def __unicode__(self):
        return u'{derived} derived from {src} in {event}'.format(
            src=self.source_file,
            derived=self.derived_file,
            event=self.event)


class Job(models.Model):
    jobuuid = models.CharField(max_length=36, primary_key=True, db_column='jobUUID')
    jobtype = models.CharField(max_length=250, db_column='jobType', blank=True)
    createdtime = models.DateTimeField(db_column='createdTime')
    createdtimedec = models.DecimalField(null=True, db_column='createdTimeDec', blank=True, max_digits=24, decimal_places=10)
    directory = models.TextField(blank=True)
    sipuuid = models.CharField(max_length=36, db_column='SIPUUID', blank=True)
    unittype = models.CharField(max_length=36, db_column='unitType', blank=True)
    currentstep = models.CharField(max_length=50, db_column='currentStep', blank=True)
    microservicegroup = models.CharField(max_length=50, db_column='microserviceGroup', blank=True)
    subjobof = models.CharField(max_length=36, db_column='subJobOf', blank=True)
    hidden = models.BooleanField(default=False, blank=False)

    class Meta:
        db_table = u'Jobs'

class SIPManager(models.Manager):
    def is_hidden(self, uuid):
        try:
            return SIP.objects.get(uuid__exact=uuid).hidden is True
        except:
            return False

class SIP(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True, db_column='sipUUID')
    createdtime = models.DateTimeField(db_column='createdTime')
    currentpath = models.TextField(db_column='currentPath', null=True, blank=True)
    # ...
    hidden = models.BooleanField(default=False, blank=False)
    aip_filename = models.TextField(db_column='aipFilename', null=True, blank=True)
    SIP_TYPE_CHOICES = (
        ('SIP', 'SIP'),
        ('AIC', 'AIC')
    )
    sip_type = models.CharField(max_length=8, choices=SIP_TYPE_CHOICES, db_column='sipType', null=True)

    objects = SIPManager()

    class Meta:
        db_table = u'SIPs'

class TransferManager(models.Manager):
    def is_hidden(self, uuid):
        try:
            return Transfer.objects.get(uuid__exact=uuid).hidden is True
        except:
            return False

class Transfer(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True, db_column='transferUUID')
    currentlocation = models.TextField(db_column='currentLocation')
    type = models.CharField(max_length=50, db_column='type')
    accessionid = models.TextField(db_column='accessionID')
    # ...
    hidden = models.BooleanField(default=False, blank=False)

    objects = TransferManager()

    class Meta:
        db_table = u'Transfers'

class File(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True, db_column='fileUUID')
    sip = models.ForeignKey(SIP, db_column='sipUUID', to_field = 'uuid')
    transfer = models.ForeignKey(Transfer, db_column='transferUUID', to_field = 'uuid')
    # both actually `longblob` in the database
    originallocation = models.TextField(db_column='originalLocation')
    currentlocation = models.TextField(db_column='currentLocation')
    filegrpuse = models.TextField(db_column='fileGrpUse')

    class Meta:
        db_table = u'Files'

    def __unicode__(self):
        return u'{uuid}: {originallocation} now at {currentlocation}'.format(
            uuid=self.uuid,
            originallocation=self.originallocation,
            currentlocation=self.currentlocation)

class FileFormatVersion(models.Model):
    id = models.IntegerField(primary_key=True, db_column='pk')
    file_uuid = models.ForeignKey(File, db_column='fileUUID', to_field='uuid', null=True)
    format_version = models.ForeignKey('fpr.FormatVersion', db_column='fileID', to_field='uuid', null=True)

    class Meta:
        db_table = u'FilesIdentifiedIDs'

    def __unicode__(self):
        return u'{file} is {format}'.format(file=self.file_uuid, format=self.format_version)

class FPRFileID(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True, db_column='pk')
    description = models.TextField(db_column='description')
    validpreservationformat = models.IntegerField(null=True, db_column='validPreservationFormat', default=0)
    validaccessformat = models.IntegerField(null=True, db_column='validAccessFormat', default=0)
    fileidtype = models.CharField(null=True, max_length=50, db_column='fileIDType')
    replaces = models.CharField(null=True, max_length=36, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta:
        db_table = u'FileIDs'

class Task(models.Model):
    taskuuid = models.CharField(max_length=36, primary_key=True, db_column='taskUUID')
    job = models.ForeignKey(Job, db_column='jobuuid', to_field = 'jobuuid')
    createdtime = models.DateTimeField(db_column='createdTime')
    fileuuid = models.CharField(max_length=36, db_column='fileUUID', blank=True)
    # Actually a `longblob` in the database, since filenames may contain
    # arbitrary non-unicode characters - other blob and binary fields
    # have these types for the same reason.
    # Note that Django doesn't have a specific blob type, hence the use of
    # the char field types instead.
    filename = models.CharField(max_length=100, db_column='fileName', blank=True)
    execution = models.CharField(max_length=250, db_column='exec', blank=True)
    # actually a `varbinary(1000)` in the database
    arguments = models.CharField(max_length=1000, blank=True)
    starttime = models.DateTimeField(db_column='startTime')
    client = models.CharField(max_length=50, blank=True)
    endtime = models.DateTimeField(db_column='endTime')
    # both actually `longblobs` in the database
    stdout = models.TextField(db_column='stdOut', blank=True)
    stderror = models.TextField(db_column='stdError', blank=True)
    exitcode = models.IntegerField(null=True, db_column='exitCode', blank=True)

    class Meta:
        db_table = u'Tasks'

class Agent(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    identifiertype = models.TextField(db_column='agentIdentifierType')
    identifiervalue = models.TextField(db_column='agentIdentifierValue')
    name = models.TextField(db_column='agentName')

    class Meta:
        db_table = u'Agents'

class Report(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    unittype = models.CharField(max_length=50, db_column='unitType')
    unitname = models.CharField(max_length=50, db_column='unitName')
    unitidentifier = models.CharField(max_length=50, db_column='unitIdentifier')
    content = models.TextField(db_column='content')
    created = models.DateTimeField(db_column='created')

    class Meta:
        db_table = u'Reports'

class RightsStatement(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    metadataappliestotype = models.CharField(max_length=50, db_column='metadataAppliesToType')
    metadataappliestoidentifier = models.CharField(max_length=50, blank=True, db_column='metadataAppliesToidentifier')
    rightsstatementidentifiertype = models.TextField(db_column='rightsStatementIdentifierType', blank=True, verbose_name='Type')
    rightsstatementidentifiervalue = models.TextField(db_column='rightsStatementIdentifierValue', blank=True, verbose_name='Value')
    #rightsholder = models.TextField(db_column='fkAgent', blank=True, verbose_name='Rights holder')
    rightsbasis = models.TextField(db_column='rightsBasis', verbose_name='Basis', blank=True)

    class Meta:
        db_table = u'RightsStatement'
        verbose_name = 'Rights Statement'

class RightsStatementCopyright(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    copyrightstatus = models.TextField(db_column='copyrightStatus', blank=True, verbose_name='Copyright status')
    copyrightjurisdiction = models.TextField(db_column='copyrightJurisdiction', blank=True, verbose_name='Copyright jurisdiction')
    copyrightstatusdeterminationdate = models.TextField(db_column='copyrightStatusDeterminationDate', blank=True, verbose_name='Copyright determination date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    copyrightapplicablestartdate = models.TextField(db_column='copyrightApplicableStartDate', blank=True, verbose_name='Copyright start date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    copyrightapplicableenddate = models.TextField(db_column='copyrightApplicableEndDate', blank=True, verbose_name='Copyright end date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    copyrightenddateopen = models.BooleanField(db_column='copyrightApplicableEndDateOpen', verbose_name='Open End Date', help_text='Indicate end date is open')

    class Meta:
        db_table = u'RightsStatementCopyright'
        verbose_name = 'Rights: Copyright'

class RightsStatementCopyrightDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightscopyright = models.ForeignKey(RightsStatementCopyright, db_column='fkRightsStatementCopyrightInformation')
    copyrightdocumentationidentifiertype = models.TextField(db_column='copyrightDocumentationIdentifierType', blank=True, verbose_name='Copyright document identification type')
    copyrightdocumentationidentifiervalue = models.TextField(db_column='copyrightDocumentationIdentifierValue', blank=True, verbose_name='Copyright document identification value')
    copyrightdocumentationidentifierrole = models.TextField(db_column='copyrightDocumentationIdentifierRole', blank=True, verbose_name='Copyright document identification role')

    class Meta:
        db_table = u'RightsStatementCopyrightDocumentationIdentifier'
        verbose_name = 'Rights: Copyright: Docs ID'

class RightsStatementCopyrightNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightscopyright = models.ForeignKey(RightsStatementCopyright, db_column='fkRightsStatementCopyrightInformation')
    copyrightnote = models.TextField(db_column='copyrightNote', blank=True, verbose_name='Copyright note')

    class Meta:
        db_table = u'RightsStatementCopyrightNote'
        verbose_name = 'Rights: Copyright: Note'

class RightsStatementLicense(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    licenseterms = models.TextField(db_column='licenseTerms', blank=True, verbose_name='License terms')
    licenseapplicablestartdate = models.TextField(db_column='licenseApplicableStartDate', blank=True, verbose_name='License start date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    licenseapplicableenddate = models.TextField(db_column='licenseApplicableEndDate', blank=True, verbose_name='License end date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    licenseenddateopen = models.BooleanField(db_column='licenseApplicableEndDateOpen', verbose_name='Open End Date', help_text='Indicate end date is open')

    class Meta:
        db_table = u'RightsStatementLicense'
        verbose_name = 'Rights: License'

class RightsStatementLicenseDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementlicense = models.ForeignKey(RightsStatementLicense, db_column='fkRightsStatementLicense')
    licensedocumentationidentifiertype = models.TextField(db_column='licenseDocumentationIdentifierType', blank=True, verbose_name='License documentation identification type')
    licensedocumentationidentifiervalue = models.TextField(db_column='licenseDocumentationIdentifierValue', blank=True, verbose_name='License documentation identification value')
    licensedocumentationidentifierrole = models.TextField(db_column='licenseDocumentationIdentifierRole', blank=True, verbose_name='License document identification role')

    class Meta:
        db_table = u'RightsStatementLicenseDocumentationIdentifier'
        verbose_name = 'Rights: License: Docs ID'

class RightsStatementLicenseNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementlicense = models.ForeignKey(RightsStatementLicense, db_column='fkRightsStatementLicense')
    licensenote = models.TextField(db_column='licenseNote', blank=True, verbose_name='License note')

    class Meta:
        db_table = u'RightsStatementLicenseNote'
        verbose_name = 'Rights: License: Note'

class RightsStatementRightsGranted(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    act = models.TextField(db_column='act', blank=True)
    startdate = models.TextField(db_column='startDate', verbose_name='Start', help_text='Use ISO 8061 (YYYY-MM-DD)', blank=True)
    enddate = models.TextField(db_column='endDate', verbose_name='End', help_text='Use ISO 8061 (YYYY-MM-DD)', blank=True)
    enddateopen = models.BooleanField(db_column='endDateOpen', verbose_name='Open End Date', help_text='Indicate end date is open')

    class Meta:
        db_table = u'RightsStatementRightsGranted'
        verbose_name = 'Rights: Granted'

class RightsStatementRightsGrantedNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsgranted = models.ForeignKey(RightsStatementRightsGranted, db_column='fkRightsStatementRightsGranted')
    rightsgrantednote = models.TextField(db_column='rightsGrantedNote', blank=True, verbose_name='Rights note')

    class Meta:
        db_table = u'RightsStatementRightsGrantedNote'
        verbose_name = 'Rights: Granted: Note'

class RightsStatementRightsGrantedRestriction(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsgranted = models.ForeignKey(RightsStatementRightsGranted, db_column='fkRightsStatementRightsGranted')
    restriction = models.TextField(db_column='restriction', blank=True)

    class Meta:
        db_table = u'RightsStatementRightsGrantedRestriction'
        verbose_name = 'Rights: Granted: Restriction'

class RightsStatementStatuteInformation(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    statutejurisdiction = models.TextField(db_column='statuteJurisdiction', verbose_name='Statute jurisdiction', blank=True)
    statutecitation = models.TextField(db_column='statuteCitation', verbose_name='Statute citation', blank=True)
    statutedeterminationdate = models.TextField(db_column='statuteInformationDeterminationDate', verbose_name='Statute determination date', help_text='Use ISO 8061 (YYYY-MM-DD)', blank=True)
    statuteapplicablestartdate = models.TextField(db_column='statuteApplicableStartDate', blank=True, verbose_name='Statute start date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    statuteapplicableenddate = models.TextField(db_column='statuteApplicableEndDate', blank=True, verbose_name='Statute end date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    statuteenddateopen = models.BooleanField(db_column='statuteApplicableEndDateOpen', verbose_name='Open End Date', help_text='Indicate end date is open')

    class Meta:
        db_table = u'RightsStatementStatuteInformation'
        verbose_name = 'Rights: Statute'

class RightsStatementStatuteInformationNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatementstatute = models.ForeignKey(RightsStatementStatuteInformation, db_column='fkRightsStatementStatuteInformation')
    statutenote = models.TextField(db_column='statuteNote', verbose_name='Statute note', blank=True)

    class Meta:
        db_table = u'RightsStatementStatuteInformationNote'
        verbose_name = 'Rights: Statute: Note'

class RightsStatementStatuteDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementstatute = models.ForeignKey(RightsStatementStatuteInformation, db_column='fkRightsStatementStatuteInformation')
    statutedocumentationidentifiertype = models.TextField(db_column='statuteDocumentationIdentifierType', blank=True, verbose_name='Statute document identification type')
    statutedocumentationidentifiervalue = models.TextField(db_column='statuteDocumentationIdentifierValue', blank=True, verbose_name='Statute document identification value')
    statutedocumentationidentifierrole = models.TextField(db_column='statuteDocumentationIdentifierRole', blank=True, verbose_name='Statute document identification role')

    class Meta:
        db_table = u'RightsStatementStatuteDocumentationIdentifier'
        verbose_name = 'Rights: Statute: Docs ID'

class RightsStatementOtherRightsInformation(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    otherrightsbasis = models.TextField(db_column='otherRightsBasis', verbose_name='Other rights basis', blank=True)
    otherrightsapplicablestartdate = models.TextField(db_column='otherRightsApplicableStartDate', blank=True, verbose_name='Other rights start date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    otherrightsapplicableenddate = models.TextField(db_column='otherRightsApplicableEndDate', blank=True, verbose_name='Other rights end date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    otherrightsenddateopen = models.BooleanField(db_column='otherRightsApplicableEndDateOpen', verbose_name='Open End Date', help_text='Indicate end date is open')

    class Meta:
        db_table = u'RightsStatementOtherRightsInformation'
        verbose_name = 'Rights: Other'

class RightsStatementOtherRightsDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementotherrights = models.ForeignKey(RightsStatementOtherRightsInformation, db_column='fkRightsStatementOtherRightsInformation')
    otherrightsdocumentationidentifiertype = models.TextField(db_column='otherRightsDocumentationIdentifierType', blank=True, verbose_name='Other rights document identification type')
    otherrightsdocumentationidentifiervalue = models.TextField(db_column='otherRightsDocumentationIdentifierValue', blank=True, verbose_name='Other right document identification value')
    otherrightsdocumentationidentifierrole = models.TextField(db_column='otherRightsDocumentationIdentifierRole', blank=True, verbose_name='Other rights document identification role')

    class Meta:
        db_table = u'RightsStatementOtherRightsDocumentationIdentifier'
        verbose_name = 'Rights: Other: Docs ID'

class RightsStatementOtherRightsInformationNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatementotherrights = models.ForeignKey(RightsStatementOtherRightsInformation, db_column='fkRightsStatementOtherRightsInformation')
    otherrightsnote = models.TextField(db_column='otherRightsNote', verbose_name='Other rights note', blank=True)

    class Meta:
        db_table = u'RightsStatementOtherRightsNote'
        verbose_name = 'Rights: Other: Note'

class RightsStatementLinkingAgentIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    linkingagentidentifiertype = models.TextField(db_column='linkingAgentIdentifierType', verbose_name='Linking Agent', blank=True)
    linkingagentidentifiervalue = models.TextField(db_column='linkingAgentIdentifierValue', verbose_name='Linking Agent Value', blank=True)

    class Meta:
        db_table = u'RightsStatementLinkingAgentIdentifier'
        verbose_name = 'Rights: Agent'

""" MCP data interoperability """

class MicroServiceChain(models.Model):
    id = UUIDPkField()
    startinglink = models.CharField(max_length=36, db_column='startingLink')
    description = models.TextField(db_column='description')

    class Meta:
        db_table = u'MicroServiceChains'

    def __unicode__(self):
        return u'MicroServiceChain ID: {uuid}; {desc}'.format(
            uuid=self.id,
            desc=self.description)

class MicroServiceChainLink(models.Model):
    id = UUIDPkField()
    currenttask =  models.CharField(max_length=36, db_column='currentTask')
    defaultnextchainlink = models.CharField(max_length=36, null=True, default=1, db_column='defaultNextChainLink')
    defaultplaysound = models.IntegerField(null=True, db_column='defaultPlaySound')
    microservicegroup = models.TextField(db_column='microserviceGroup')
    reloadfilelist = models.IntegerField(default=1, db_column='reloadFileList')
    defaultexitmessage = models.TextField(default='Failed', db_column='defaultExitMessage')

    class Meta:
        db_table = u'MicroServiceChainLinks'

    def __unicode__(self):
        return u'MicroServiceChainLink ID: {}'.format(self.id)

class MicroServiceChainLinkExitCode(models.Model):
    id = UUIDPkField()
    microservicechainlink = models.CharField(max_length=36, db_column='microServiceChainLink')
    exitcode = models.IntegerField(db_column='exitCode')
    nextmicroservicechainlink = models.CharField(max_length=36, db_column='nextMicroServiceChainLink')
    playsound = models.IntegerField(null=True, db_column='playSound')
    exitmessage = models.TextField(db_column='exitMessage')

    class Meta:
        db_table = u'MicroServiceChainLinksExitCodes'

class MicroServiceChainChoice(models.Model):
    id = UUIDPkField()
    choiceavailableatlink = models.CharField(max_length=36, db_column='choiceAvailableAtLink')
    chainavailable = models.ForeignKey(MicroServiceChain, db_column='chainAvailable')

    class Meta:
        db_table = u'MicroServiceChainChoice'

    def __unicode__(self):
        return u'MicroServiceChainChoice ID: {uuid} ({chain} at {choice})'.format(
            uuid=self.id,
            chain=self.chainavailable,
            choice=self.choiceavailableatlink)

class MicroServiceChoiceReplacementDic(models.Model):
    id = UUIDPkField()
    choiceavailableatlink = models.CharField(max_length=36, db_column='choiceAvailableAtLink')
    description = models.TextField(db_column='description', verbose_name='Description')
    replacementdic = models.TextField(db_column='replacementDic', verbose_name='Configuration')

    def clean(self):
        error = None
        try:
            config = ast.literal_eval(self.replacementdic)
        except ValueError:
            error = 'Invalid syntax.'
        except SyntaxError:
            error = 'Invalid syntax.'
        if error == None and not type(config) is dict:
            error = 'Invalid syntax.'
        if error != None:
            raise forms.ValidationError(error)

    class Meta:
        db_table = u'MicroServiceChoiceReplacementDic'

class StandardTaskConfig(models.Model):
    id = UUIDPkField()
    execute = models.TextField(db_column='execute', blank=True)
    arguments = models.TextField(db_column='arguments', blank=True)

    class Meta:
        db_table = u'StandardTasksConfigs'

class TaskConfig(models.Model):
    id = UUIDPkField()
    # Foreign key to TaskTypes
    tasktype = models.CharField(max_length=36, db_column='taskType')
    tasktypepkreference = models.CharField(max_length=36, null=True, blank=True, db_column='taskTypePKReference')
    description = models.TextField(db_column='description')

    class Meta:
        db_table = u'TasksConfigs'

    def __unicode__(self):
        return u'TaskConfig ID: {}, desc: {}'.format(self.id, self.description)

class UnitVariable(models.Model):
    id = UUIDPkField()
    unittype = models.CharField(max_length=50, null=True, db_column='unitType')
    unituuid = models.CharField(max_length=36, null=True, help_text='Semantically a foreign key to SIP or Transfer', db_column='unitUUID')
    variable = models.TextField(null=True, db_column='variable')
    variablevalue = models.TextField(null=True, db_column='variableValue')
    microservicechainlink = models.CharField(null=True, max_length=36, help_text='UUID of the MicroServiceChainLink if used in task type linkTaskManagerUnitVariableLinkPull', db_column='microServiceChainLink')
    createdtime = models.DateTimeField(db_column='createdTime', auto_now_add=True)
    updatedtime = models.DateTimeField(db_column='updatedTime', auto_now=True)

    class Meta:
        db_table = u'UnitVariables'

class AtkDIPObjectResourcePairing(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    dipuuid = models.CharField(max_length=50, db_column='dipUUID')
    fileuuid = models.CharField(max_length=50, db_column='fileUUID')
    resourceid = models.IntegerField(db_column='resourceId')
    resourcecomponentid = models.IntegerField(db_column='resourceComponentId')

    class Meta:
        db_table = u'AtkDIPObjectResourcePairing'
