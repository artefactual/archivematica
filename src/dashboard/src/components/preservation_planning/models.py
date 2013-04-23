from django.db import models
from main.models import UUIDPkField
        
class FormatID(models.Model):
    uuid = UUIDPkField()
    description = models.CharField(db_column='description')
    validpreservationformat = models.BooleanField(null=True, db_column='validPreservationFormat', default=0)
    validaccessformat = models.BooleanField(null=True, db_column='validAccessFormat', default=0)
    tool = models.CharField(null=True, max_length=50, db_column='fileIDType')
    replaces = models.CharField(null=True, max_length=50, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')
    enabled = models.BooleanField(db_column='enabled', default=1)
    class Meta:
        db_table = u'FileIDs'
        
class FormatIDToolOutput(models.Model):
    uuid = UUIDPkField()
    formatID = models.ForeignKey(FormatID, db_column='fileID')
    toolOutput = models.TextField(db_column='id')
    tool = models.CharField(max_length=150, db_column='tool')
    toolVersion = models.CharField(max_length=20, db_column='toolVersion')
    replaces = models.CharField(null=True, max_length=50, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified')
    enabled = models.BooleanField(db_column='enabled')
    class Meta:
        db_table = u'FileIDsBySingleID'
        
class Command(models.Model):
    uuid = UUIDPkField()
    commandUsage = models.CharField(max_length=15)
    #commandType = models.ForeignKey(CommandType, db_column='commandType')
    commandType = models.CharField(max_length=36)
    #verificationCommand = models.ForeignKey('self', null=True, related_name='+', db_column='verificationCommand')
    verificationCommand = models.CharField(max_length=36, null=True, blank=True)
    #eventDetailCommand = models.ForeignKey('self', null=True, related_name='+', db_column='eventDetailCommand')
    eventDetailCommand = models.CharField(max_length=36, null=True, blank=True)
    #supportedBy = models.ForeignKey('self', null=True, related_name='+', db_column='supportedBy')
    supportedBy = models.CharField(max_length=36, null=True, default='ca278b07-8137-4a75-b84f-9b10994ed006', db_column='supportedBy')
    command = models.TextField(db_column='command')
    outputLocation = models.TextField(db_column='outputLocation', null=True)
    description = models.TextField(db_column='description')
    outputFileFormat = models.TextField(db_column='outputFileFormat', null=True)
    #replaces = models.ForeignKey('self', related_name='+', db_column='replaces', null=True)
    replaces = models.CharField(max_length=36, null=True, db_column='replaces')
    lastmodified = models.DateTimeField(db_column='lastModified', null=True, blank=True)
    enabled = models.IntegerField(null=True, db_column='enabled', default=1)
    class Meta:
        db_table = u'Commands'
        
class FormatPolicyRule(models.Model):
    uuid = UUIDPkField() 
    #commandClassification = models.ForeignKey(CommandClassification, db_column='commandClassification')
    purpose = models.CharField(max_length=36, db_column='commandClassification')
    #command = models.ForeignKey(Command, null=True, db_column='command')
    #fileID = models.ForeignKey(FileID, db_column='fileID')
    #replaces = models.CharField(null=True, max_length=50, db_column='replaces')
    command = models.CharField(max_length=36, null=True)
    formatID = models.CharField(max_length=36, null=True, db_column='fileID')
    replaces = models.CharField(max_length=36, null=True)
    lastModified = models.DateTimeField(db_column='lastModified')
    enabled = models.IntegerField(null=True, db_column='enabled', default=1)
    class Meta:
        db_table = u'CommandRelationships'

