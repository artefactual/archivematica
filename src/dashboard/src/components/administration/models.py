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

class ArchivistsToolkitConfig(models.Model):
    id = UUIDPkField()
    host = models.CharField(max_length=50)
    port = models.IntegerField(default=3306)
    dbname = models.CharField(max_length=50)
    dbuser = models.CharField(max_length=50)
    dbpass = models.CharField(max_length=50)
    atuser = models.CharField(max_length=50)
    premis = models.CharField(max_length=10)
    ead_actuate = models.CharField(max_length=50)
    ead_show = models.CharField(max_length=50)
    object_type = models.CharField(max_length=50, blank=True, null=True)
    use_statement = models.CharField(max_length=50)
    uri_prefix = models.CharField(max_length=50)
    access_conditions = models.CharField(max_length=50, blank=True, null=True)
    use_conditions = models.CharField(max_length=50, blank=True, null=True)

