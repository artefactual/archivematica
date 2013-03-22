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

from django.db import models
from contrib import utils
from django import forms
import ast
import main
import uuid

class UUIDPkField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 64)
        kwargs['blank'] = False
        kwargs['primary_key'] = True
        kwargs['editable'] = False
        kwargs['db_column'] = 'pk'
        kwargs['default'] = True # provide a placeholder pk value or else it won't save
        models.CharField.__init__(self, *args, **kwargs)

    def pre_save(self, model_instance, add):
        # set uuid during save
        setattr(model_instance, self.attname, uuid.uuid4().__str__())
        return super(models.CharField, self).pre_save(model_instance, add)

class DashboardSetting(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    name = models.CharField(max_length=255, db_column='name')
    value = models.TextField(db_column='value', blank=True)

    class Meta:
        db_table = u'DashboardSettings'

class Access(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    sipuuid = models.CharField(max_length=150, db_column='SIPUUID', blank=True)
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
            return utils.get_directory_name(jobs[0])
        except:
            return 'N/A'

class DublinCoreManager(models.Manager):
    def get_sip_metadata(self, uuid):
        return DublinCore.objects.get(metadataappliestotype__exact=1, metadataappliestoidentifier__exact=uuid)

class DublinCore(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    metadataappliestotype = models.CharField(max_length=50, db_column='metadataAppliesToType')
    metadataappliestoidentifier = models.CharField(max_length=50, blank=True, db_column='metadataAppliesToidentifier')
    title = models.TextField(db_column='title', blank=True)
    creator = models.TextField(db_column='creator', blank=True)
    subject = models.TextField(db_column='subject', blank=True)
    description = models.TextField(db_column='description', blank=True)
    publisher = models.TextField(db_column='publisher', blank=True)
    contributor = models.TextField(db_column='contributor', blank=True)
    date = models.TextField(db_column='date', blank=True)
    type = models.TextField(db_column='type', blank=True)
    format = models.TextField(db_column='format', blank=True)
    identifier = models.TextField(db_column='identifier', blank=True)
    source = models.TextField(db_column='source', blank=True)
    relation = models.TextField(db_column='relation', blank=True)
    language = models.TextField(db_column='language', blank=True)
    coverage = models.TextField(db_column='coverage', blank=True)
    rights = models.TextField(db_column='rights', blank=True)

    objects = DublinCoreManager()

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
    replaces = models.CharField(max_length=50, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta:
        db_table = u'MetadataAppliesToTypes'

class Job(models.Model):
    jobuuid = models.CharField(max_length=150, primary_key=True, db_column='jobUUID')
    jobtype = models.CharField(max_length=750, db_column='jobType', blank=True)
    createdtime = models.DateTimeField(db_column='createdTime')
    createdtimedec = models.DecimalField(null=True, db_column='createdTimeDec', blank=True, max_digits=24, decimal_places=10)
    directory = models.CharField(max_length=750, blank=True)
    sipuuid = models.CharField(max_length=150, db_column='SIPUUID', blank=True)
    unittype = models.CharField(max_length=150, db_column='unitType', blank=True)
    currentstep = models.CharField(max_length=150, db_column='currentStep', blank=True)
    microservicegroup = models.CharField(max_length=150, db_column='microserviceGroup', blank=True)
    subjobof = models.CharField(max_length=50, db_column='subJobOf', blank=True)
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
    uuid = models.CharField(max_length=150, primary_key=True, db_column='sipUUID')
    createdtime = models.DateTimeField(db_column='createdTime')
    currentpath = models.TextField(db_column='currentPath', blank=True)
    # ...
    hidden = models.BooleanField(default=False, blank=False)
    accessionid = models.CharField(max_length=255, db_column='accessionId')

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
    uuid = models.CharField(max_length=150, primary_key=True, db_column='transferUUID')
    currentlocation = models.TextField(db_column='currentLocation')
    # ...
    hidden = models.BooleanField(default=False, blank=False)

    objects = TransferManager()

    class Meta:
        db_table = u'Transfers'

class File(models.Model):
    uuid = models.CharField(max_length=150, primary_key=True, db_column='fileUUID')
    sip = models.ForeignKey(SIP, db_column='sipUUID', to_field = 'uuid')
    transfer = models.ForeignKey(Transfer, db_column='transferUUID', to_field = 'uuid')
    originallocation = models.TextField(db_column='originalLocation')
    currentlocation = models.TextField(db_column='currentLocation')

    class Meta:
        db_table = u'Files'

class FPRFileID(models.Model):
    uuid = models.CharField(max_length=150, primary_key=True, db_column='pk')
    description = models.TextField(db_column='description')
    validpreservationformat = models.IntegerField(null=True, db_column='validPreservationFormat', default=0)
    validaccessformat = models.IntegerField(null=True, db_column='validAccessFormat', default=0)
    fileidtype = models.CharField(null=True, max_length=50, db_column='fileIDType')
    replaces = models.CharField(null=True, max_length=50, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')

    class Meta:
        db_table = u'FileIDs'

class Task(models.Model):
    taskuuid = models.CharField(max_length=50, primary_key=True, db_column='taskUUID')
    job = models.ForeignKey(Job, db_column='jobuuid', to_field = 'jobuuid')
    createdtime = models.DateTimeField(db_column='createdTime')
    fileuuid = models.CharField(max_length=50, db_column='fileUUID', blank=True)
    filename = models.CharField(max_length=100, db_column='fileName', blank=True)
    execution = models.CharField(max_length=50, db_column='exec', blank=True)
    arguments = models.CharField(max_length=1000, blank=True)
    starttime = models.DateTimeField(db_column='startTime')
    client = models.CharField(max_length=50, blank=True)
    endtime = models.DateTimeField(db_column='endTime')
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

class RightsStatementCopyrightDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightscopyright = models.ForeignKey(RightsStatementCopyright, db_column='fkRightsStatementCopyrightInformation')
    copyrightdocumentationidentifiertype = models.TextField(db_column='copyrightDocumentationIdentifierType', blank=True, verbose_name='Copyright document identification type')
    copyrightdocumentationidentifiervalue = models.TextField(db_column='copyrightDocumentationIdentifierValue', blank=True, verbose_name='Copyright document identification value')
    copyrightdocumentationidentifierrole = models.TextField(db_column='copyrightDocumentationIdentifierRole', blank=True, verbose_name='Copyright document identification role')

    class Meta:
        db_table = u'RightsStatementCopyrightDocumentationIdentifier'

class RightsStatementCopyrightNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightscopyright = models.ForeignKey(RightsStatementCopyright, db_column='fkRightsStatementCopyrightInformation')
    copyrightnote = models.TextField(db_column='copyrightNote', blank=True, verbose_name='Copyright note')

    class Meta:
        db_table = u'RightsStatementCopyrightNote'

class RightsStatementLicense(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    licenseterms = models.TextField(db_column='licenseTerms', blank=True, verbose_name='License terms')
    licenseapplicablestartdate = models.TextField(db_column='licenseApplicableStartDate', blank=True, verbose_name='License start date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    licenseapplicableenddate = models.TextField(db_column='licenseApplicableEndDate', blank=True, verbose_name='License end date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    licenseenddateopen = models.BooleanField(db_column='licenseApplicableEndDateOpen', verbose_name='Open End Date', help_text='Indicate end date is open')

    class Meta:
        db_table = u'RightsStatementLicense'

class RightsStatementLicenseDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementlicense = models.ForeignKey(RightsStatementLicense, db_column='fkRightsStatementLicense')
    licensedocumentationidentifiertype = models.TextField(db_column='licenseDocumentationIdentifierType', blank=True, verbose_name='License documentation identification type')
    licensedocumentationidentifiervalue = models.TextField(db_column='licenseDocumentationIdentifierValue', blank=True, verbose_name='License documentation identification value')
    licensedocumentationidentifierrole = models.TextField(db_column='licenseDocumentationIdentifierRole', blank=True, verbose_name='License document identification role')

    class Meta:
        db_table = u'RightsStatementLicenseDocumentationIdentifier'

class RightsStatementLicenseNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementlicense = models.ForeignKey(RightsStatementLicense, db_column='fkRightsStatementLicense')
    licensenote = models.TextField(db_column='licenseNote', blank=True, verbose_name='License note')

    class Meta:
        db_table = u'RightsStatementLicenseNote'

class RightsStatementRightsGranted(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    act = models.TextField(db_column='act', blank=True)
    startdate = models.TextField(db_column='startDate', verbose_name='Start', help_text='Use ISO 8061 (YYYY-MM-DD)', blank=True)
    enddate = models.TextField(db_column='endDate', verbose_name='End', help_text='Use ISO 8061 (YYYY-MM-DD)', blank=True)
    enddateopen = models.BooleanField(db_column='endDateOpen', verbose_name='Open End Date', help_text='Indicate end date is open')

    class Meta:
        db_table = u'RightsStatementRightsGranted'

class RightsStatementRightsGrantedNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsgranted = models.ForeignKey(RightsStatementRightsGranted, db_column='fkRightsStatementRightsGranted')
    rightsgrantednote = models.TextField(db_column='rightsGrantedNote', blank=True, verbose_name='Rights note')

    class Meta:
        db_table = u'RightsStatementRightsGrantedNote'

class RightsStatementRightsGrantedRestriction(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsgranted = models.ForeignKey(RightsStatementRightsGranted, db_column='fkRightsStatementRightsGranted')
    restriction = models.TextField(db_column='restriction', blank=True)

    class Meta:
        db_table = u'RightsStatementRightsGrantedRestriction'

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

class RightsStatementStatuteInformationNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatementstatute = models.ForeignKey(RightsStatementStatuteInformation, db_column='fkRightsStatementStatuteInformation')
    statutenote = models.TextField(db_column='statuteNote', verbose_name='Statute note', blank=True)

    class Meta:
        db_table = u'RightsStatementStatuteInformationNote'

class RightsStatementStatuteDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementstatute = models.ForeignKey(RightsStatementStatuteInformation, db_column='fkRightsStatementStatuteInformation')
    statutedocumentationidentifiertype = models.TextField(db_column='statuteDocumentationIdentifierType', blank=True, verbose_name='Statute document identification type')
    statutedocumentationidentifiervalue = models.TextField(db_column='statuteDocumentationIdentifierValue', blank=True, verbose_name='Statute document identification value')
    statutedocumentationidentifierrole = models.TextField(db_column='statuteDocumentationIdentifierRole', blank=True, verbose_name='Statute document identification role')

    class Meta:
        db_table = u'RightsStatementStatuteDocumentationIdentifier'

class RightsStatementOtherRightsInformation(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    otherrightsbasis = models.TextField(db_column='otherRightsBasis', verbose_name='Other rights basis', blank=True)
    otherrightsapplicablestartdate = models.TextField(db_column='otherRightsApplicableStartDate', blank=True, verbose_name='Other rights start date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    otherrightsapplicableenddate = models.TextField(db_column='otherRightsApplicableEndDate', blank=True, verbose_name='Other rights end date', help_text='Use ISO 8061 (YYYY-MM-DD)')
    otherrightsenddateopen = models.BooleanField(db_column='otherRightsApplicableEndDateOpen', verbose_name='Open End Date', help_text='Indicate end date is open')

    class Meta:
        db_table = u'RightsStatementOtherRightsInformation'

class RightsStatementOtherRightsDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk', editable=False)
    rightsstatementotherrights = models.ForeignKey(RightsStatementOtherRightsInformation, db_column='fkRightsStatementOtherRightsInformation')
    otherrightsdocumentationidentifiertype = models.TextField(db_column='otherRightsDocumentationIdentifierType', blank=True, verbose_name='Other rights document identification type')
    otherrightsdocumentationidentifiervalue = models.TextField(db_column='otherRightsDocumentationIdentifierValue', blank=True, verbose_name='Other right document identification value')
    otherrightsdocumentationidentifierrole = models.TextField(db_column='otherRightsDocumentationIdentifierRole', blank=True, verbose_name='Other rights document identification role')

    class Meta:
        db_table = u'RightsStatementOtherRightsDocumentationIdentifier'

class RightsStatementOtherRightsInformationNote(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatementotherrights = models.ForeignKey(RightsStatementOtherRightsInformation, db_column='fkRightsStatementOtherRightsInformation')
    otherrightsnote = models.TextField(db_column='otherRightsNote', verbose_name='Other rights note', blank=True)

    class Meta:
        db_table = u'RightsStatementOtherRightsNote'

class RightsStatementLinkingAgentIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    rightsstatement = models.ForeignKey(RightsStatement, db_column='fkRightsStatement')
    linkingagentidentifiertype = models.TextField(db_column='linkingAgentIdentifierType', verbose_name='Linking Agent', blank=True)
    linkingagentidentifiervalue = models.TextField(db_column='linkingAgentIdentifierValue', verbose_name='Linking Agent Value', blank=True)

    class Meta:
        db_table = u'RightsStatementLinkingAgentIdentifier'

class SourceDirectory(models.Model):
    id = UUIDPkField()
    path = models.TextField(db_column='path')

    def __unicode__(self):
        return self.path

    class Meta:
        db_table = u'SourceDirectories'

class StorageDirectory(models.Model):
    id = UUIDPkField()
    path = models.TextField(db_column='path')

    def __unicode__(self):
        return self.path

    class Meta:
        db_table = u'StorageDirectories'

""" MCP data interoperability """

class MicroServiceChain(models.Model):
    id = UUIDPkField()
    startinglink = models.CharField(max_length=50, db_column='startingLink')
    description = models.TextField(db_column='description')

    class Meta:
        db_table = u'MicroServiceChains'

class MicroServiceChainLink(models.Model):
    id = UUIDPkField()
    currenttask =  models.CharField(max_length=50, db_column='currentTask')
    defaultnextchainlink = models.CharField(max_length=50, null=True, default=1, db_column='defaultNextChainLink')
    defaultplaysound = models.IntegerField(null=True, db_column='defaultPlaySound')
    microservicegroup = models.TextField(db_column='microserviceGroup')
    reloadfilelist = models.IntegerField(default=1, db_column='reloadFileList')
    defaultexitmessage = models.TextField(default='Failed', db_column='defaultExitMessage')

    class Meta:
        db_table = u'MicroServiceChainLinks'

class MicroServiceChainLinkExitCode(models.Model):
    id = UUIDPkField()
    microservicechainlink = models.CharField(max_length=50, db_column='microServiceChainLink')
    exitcode = models.IntegerField(db_column='exitCode')
    nextmicroservicechainlink = models.CharField(max_length=50, db_column='nextMicroServiceChainLink')
    playsound = models.IntegerField(null=True, db_column='playSound')
    exitmessage = models.TextField(db_column='exitMessage')

    class Meta:
        db_table = u'MicroServiceChainLinksExitCodes'

class MicroServiceChainChoice(models.Model):
    id = UUIDPkField()
    choiceavailableatlink = models.CharField(max_length=150, db_column='choiceAvailableAtLink')
    chainavailable = models.CharField(max_length=50, db_column='chainAvailable')

    class Meta:
        db_table = u'MicroServiceChainChoice'

class MicroServiceChoiceReplacementDic(models.Model):
    id = UUIDPkField()
    choiceavailableatlink = models.CharField(max_length=50, db_column='choiceAvailableAtLink')
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
    tasktype = models.IntegerField(db_column='taskType')
    tasktypepkreference = models.IntegerField(db_column='taskTypePKReference')
    description = models.TextField(db_column='description')

    class Meta:
        db_table = u'TasksConfigs'
