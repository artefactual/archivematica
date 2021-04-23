# -*- coding: utf-8 -*-

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
from __future__ import absolute_import

import itertools
import logging
import os
import re

# Core Django, alphabetical by import source
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.six import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
import six

# Third party dependencies, alphabetical by import source
from django_extensions.db.fields import UUIDField

from version import get_preservation_system_identifier

LOGGER = logging.getLogger("archivematica.dashboard")

METADATA_STATUS_ORIGINAL = "ORIGINAL"
METADATA_STATUS_REINGEST = "REINGEST"
METADATA_STATUS_UPDATED = "UPDATED"
METADATA_STATUS = (
    (METADATA_STATUS_ORIGINAL, "original"),
    (METADATA_STATUS_REINGEST, "parsed from reingest"),
    (METADATA_STATUS_UPDATED, "updated"),  # Might be updated for both, on rereingest
)

# How many objects are created through bulk_create in a single database query
BULK_CREATE_BATCH_SIZE = 2000

# CUSTOM FIELDS


class UUIDPkField(UUIDField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 36)
        kwargs["primary_key"] = True
        kwargs["db_column"] = "pk"
        super(UUIDPkField, self).__init__(*args, **kwargs)


class BlobTextField(models.TextField):
    """
    Text field backed by `longblob` instead of `longtext`.

    Used for storing strings that need to match paths on disk with filenames unchanged.

    BLOBs are byte strings (bynary character set and collation).
    """

    def db_type(self, connection):
        return "longblob"


# SIGNALS


@receiver(post_save, sender=User)
def create_user_agent(sender, instance, **kwargs):
    LOGGER.debug("Caught post_save signal from %s with instance %r", sender, instance)
    agent, created = Agent.objects.update_or_create(
        userprofile__user=instance,
        defaults={
            "identifiertype": "Archivematica user pk",
            "identifiervalue": str(instance.id),
            "name": 'username="{}", first_name="{}", last_name="{}"'.format(
                six.ensure_str(instance.username),
                six.ensure_str(instance.first_name),
                six.ensure_str(instance.last_name),
            ),
            "agenttype": "Archivematica user",
        },
    )
    LOGGER.debug("Agent: %s; created: %s", agent, created)
    if created:
        UserProfile.objects.update_or_create(user=instance, defaults={"agent": agent})


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
        return {
            key: value
            for (key, value) in self.get_queryset()
            .filter(scope=scope)
            .values_list("name", "value")
        }

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
            self.bulk_create(
                [
                    DashboardSetting(
                        scope=scope,
                        name=six.text_type(name),
                        value=six.text_type(value),
                    )
                    for name, value in items.items()
                ]
            )

    def unset_dict(self, scope):
        return self.get_queryset().filter(scope=scope).delete()


class DashboardSetting(models.Model):
    """ Settings related to the dashboard stored as key-value pairs. """

    id = models.AutoField(primary_key=True, db_column="pk")
    scope = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255, db_column="name")
    value = models.TextField(db_column="value", blank=True)
    lastmodified = models.DateTimeField(auto_now=True, db_column="lastModified")

    objects = DashboardSettingManager()

    class Meta:
        db_table = u"DashboardSettings"

    def __str__(self):
        return "[scope={}|name={}]: {}".format(
            self.scope if self.scope else "<blank>", self.name, self.value
        )


class Access(models.Model):
    """ Information about an upload to AtoM for a SIP. """

    id = models.AutoField(primary_key=True, db_column="pk")
    sipuuid = models.CharField(max_length=36, db_column="SIPUUID", blank=True)
    # Qubit ID (slug) generated or preexisting if a new description was not created
    resource = models.TextField(db_column="resource", blank=True)
    # Before the UploadDIP micro-service is executed, a dialog shows up and ask the user
    # the target archival description when the DIP will be deposited via SWORD
    # This column is mandatory, the user won't be able to submit the form if this field is empty
    target = models.TextField(db_column="target", blank=True)
    # Human readable status of an upload (rsync progress percentage, etc)
    status = models.TextField(db_column="status", blank=True)
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
    statuscode = models.PositiveSmallIntegerField(
        db_column="statusCode", null=True, blank=True
    )  # Actually a unsigned tinyint
    # Rsync exit code
    exitcode = models.PositiveSmallIntegerField(
        db_column="exitCode", null=True, blank=True
    )  # Actually a unsigned tinyint
    # Timestamps
    createdtime = models.DateTimeField(db_column="createdTime", auto_now_add=True)
    updatedtime = models.DateTimeField(db_column="updatedTime", auto_now=True)

    class Meta:
        db_table = u"Accesses"

    def get_title(self):
        return Job.objects.filter(sipuuid=self.sipuuid).get_directory_name()


@python_2_unicode_compatible
class DublinCore(models.Model):
    """ DublinCore metadata associated with a SIP or Transfer. """

    id = models.AutoField(primary_key=True, db_column="pk")
    metadataappliestotype = models.ForeignKey(
        "MetadataAppliesToType",
        db_column="metadataAppliesToType",
        on_delete=models.CASCADE,
    )
    metadataappliestoidentifier = models.CharField(
        max_length=36,
        blank=True,
        null=True,
        default=None,
        db_column="metadataAppliesToidentifier",
    )  # Foreign key to SIPs or Transfers
    title = models.TextField(db_column="title", blank=True)
    is_part_of = models.TextField(
        db_column="isPartOf",
        verbose_name=_("Part of AIC"),
        help_text=_("Optional: leave blank if unsure"),
        blank=True,
    )
    creator = models.TextField(db_column="creator", blank=True)
    subject = models.TextField(db_column="subject", blank=True)
    description = models.TextField(db_column="description", blank=True)
    publisher = models.TextField(db_column="publisher", blank=True)
    contributor = models.TextField(db_column="contributor", blank=True)
    date = models.TextField(
        help_text=_("Use ISO 8601 (YYYY-MM-DD or YYYY-MM-DD/YYYY-MM-DD)"),
        db_column="date",
        blank=True,
    )
    type = models.TextField(db_column="type", blank=True)
    format = models.TextField(db_column="format", blank=True)
    identifier = models.TextField(db_column="identifier", blank=True)
    source = models.TextField(db_column="source", blank=True)
    relation = models.TextField(db_column="relation", blank=True)
    language = models.TextField(
        help_text=_("Use ISO 639"), db_column="language", blank=True
    )
    coverage = models.TextField(db_column="coverage", blank=True)
    rights = models.TextField(db_column="rights", blank=True)
    status = models.CharField(
        db_column="status",
        max_length=8,
        choices=METADATA_STATUS,
        default=METADATA_STATUS_ORIGINAL,
    )

    class Meta:
        db_table = u"Dublincore"

    def __str__(self):
        if self.title:
            return u"%s" % self.title
        else:
            return six.text_type(_("Untitled"))


@python_2_unicode_compatible
class MetadataAppliesToType(models.Model):
    """
    What type of unit (SIP, DIP, Transfer etc) the metadata link is.

    TODO replace this with choices fields.
    """

    id = UUIDPkField()
    description = models.CharField(max_length=50, db_column="description")
    replaces = models.CharField(
        max_length=36, db_column="replaces", null=True, blank=True
    )
    lastmodified = models.DateTimeField(db_column="lastModified", auto_now=True)

    class Meta:
        db_table = u"MetadataAppliesToTypes"

    def __str__(self):
        return six.text_type(self.description)


@python_2_unicode_compatible
class Event(models.Model):
    """ PREMIS Events associated with Files. """

    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    event_id = UUIDField(
        auto=False, null=True, unique=True, db_column="eventIdentifierUUID"
    )
    file_uuid = models.ForeignKey(
        "File",
        db_column="fileUUID",
        to_field="uuid",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    event_type = models.TextField(db_column="eventType", blank=True)
    event_datetime = models.DateTimeField(db_column="eventDateTime", auto_now=True)
    event_detail = models.TextField(db_column="eventDetail", blank=True)
    event_outcome = models.TextField(db_column="eventOutcome", blank=True)
    event_outcome_detail = models.TextField(
        db_column="eventOutcomeDetailNote", blank=True
    )  # TODO convert this to a BinaryField with Django >= 1.6
    agents = models.ManyToManyField("Agent")

    class Meta:
        db_table = u"Events"

    def __str__(self):
        return six.text_type(
            _("%(type)s event on %(file_uuid)s (%(detail)s)")
            % {
                "type": self.event_type,
                "file_uuid": self.file_uuid,
                "detail": self.event_detail,
            }
        )


@python_2_unicode_compatible
class Derivation(models.Model):
    """
    Link between original and normalized files.

    Eg original to preservation copy, or original to access copy.
    """

    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    source_file = models.ForeignKey(
        "File",
        db_column="sourceFileUUID",
        to_field="uuid",
        related_name="derived_file_set",
        on_delete=models.CASCADE,
    )
    derived_file = models.ForeignKey(
        "File",
        db_column="derivedFileUUID",
        to_field="uuid",
        related_name="original_file_set",
        on_delete=models.CASCADE,
    )
    event = models.ForeignKey(
        "Event",
        db_column="relatedEventUUID",
        to_field="event_id",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = u"Derivations"

    def __str__(self):
        return six.text_type(
            _("%(derived)s derived from %(src)s in %(event)s")
            % {
                "derived": self.derived_file,
                "src": self.source_file,
                "event": self.event,
            }
        )


class UnitHiddenManager(models.Manager):
    def is_hidden(self, uuid):
        """ Return True if the unit (SIP, Transfer) with uuid is hidden. """
        try:
            return self.get_queryset().get(uuid=uuid).hidden
        except:
            return False


@python_2_unicode_compatible
class SIP(models.Model):
    """ Information on SIP units. """

    uuid = models.CharField(max_length=36, primary_key=True, db_column="sipUUID")
    createdtime = models.DateTimeField(db_column="createdTime", auto_now_add=True)
    # If currentpath is null, this SIP is understood to not have been started yet.
    currentpath = models.TextField(db_column="currentPath", null=True, blank=True)
    hidden = models.BooleanField(default=False)
    aip_filename = models.TextField(db_column="aipFilename", null=True, blank=True)
    SIP_TYPE_CHOICES = (
        ("SIP", _("SIP")),
        ("AIC", _("AIC")),
        ("AIP-REIN", _("Reingested AIP")),
        ("AIC-REIN", _("Reingested AIC")),
    )
    sip_type = models.CharField(
        max_length=8, choices=SIP_TYPE_CHOICES, db_column="sipType", default="SIP"
    )
    identifiers = models.ManyToManyField("Identifier")
    diruuids = models.BooleanField(db_column="dirUUIDs", default=False)

    objects = UnitHiddenManager()

    class Meta:
        db_table = u"SIPs"

    def __str__(self):
        return six.text_type(_("SIP: {path}") % {"path": self.currentpath})

    def update_active_agent(self, user_id):
        UnitVariable.objects.update_active_agent("SIP", self.uuid, user_id)

    def add_custom_identifier(self, scheme, value):
        """Allow callers to add custom identifiers to the model's instance."""
        self.identifiers.create(type=scheme, value=value)

    @property
    def agents(self):
        """Returns a queryset of agents related to this SIP."""
        agent_lookups = Agent.objects.default_agents_query_keywords()

        try:
            unit_variable = UnitVariable.objects.get(
                unittype="SIP", unituuid=self.uuid, variable="activeAgent"
            )
        except UnitVariable.DoesNotExist:
            pass
        else:
            agent_lookups = agent_lookups | models.Q(id=unit_variable.variablevalue)

        return Agent.objects.filter(agent_lookups)


class TransferManager(models.Manager):
    def is_hidden(self, uuid):
        try:
            return Transfer.objects.get(uuid__exact=uuid).hidden is True
        except:
            return False


class Transfer(models.Model):
    """ Information on Transfer units. """

    uuid = models.CharField(max_length=36, primary_key=True, db_column="transferUUID")
    currentlocation = models.TextField(db_column="currentLocation")
    type = models.CharField(max_length=50, db_column="type")
    accessionid = models.TextField(db_column="accessionID")
    sourceofacquisition = models.TextField(db_column="sourceOfAcquisition", blank=True)
    typeoftransfer = models.TextField(db_column="typeOfTransfer", blank=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    access_system_id = models.TextField(db_column="access_system_id")
    hidden = models.BooleanField(default=False)
    transfermetadatasetrow = models.ForeignKey(
        "TransferMetadataSet",
        db_column="transferMetadataSetRowUUID",
        to_field="id",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    diruuids = models.BooleanField(db_column="dirUUIDs", default=False)

    objects = UnitHiddenManager()

    class Meta:
        db_table = u"Transfers"

    def update_active_agent(self, user_id):
        UnitVariable.objects.update_active_agent("Transfer", self.uuid, user_id)

    @property
    def agents(self):
        """Returns a queryset of agents related to this tranfer."""
        agent_lookups = Agent.objects.default_agents_query_keywords()

        try:
            unit_variable = UnitVariable.objects.get(
                unittype="Transfer", unituuid=self.uuid, variable="activeAgent"
            )
        except UnitVariable.DoesNotExist:
            pass
        else:
            agent_lookups = agent_lookups | models.Q(id=unit_variable.variablevalue)

        return Agent.objects.filter(agent_lookups)

    def set_processing_configuration(self, processing_configuration):
        UnitVariable.objects.update_processing_configuration(
            "Transfer", self.uuid, processing_configuration
        )

    @property
    def processing_configuration(self):
        try:
            unit_variable = UnitVariable.objects.get(
                unittype="Transfer",
                unituuid=self.uuid,
                variable="processingConfiguration",
            )
        except UnitVariable.DoesNotExist:
            result = None
        else:
            result = unit_variable.variablevalue
        return result or "default"


@python_2_unicode_compatible
class SIPArrange(models.Model):
    """ Information about arranged files: original and arranged location, current status. """

    original_path = BlobTextField(null=True, blank=True, default=None)
    arrange_path = BlobTextField()
    file_uuid = UUIDField(auto=False, null=True, blank=True, default=None, unique=True)
    transfer_uuid = UUIDField(auto=False, null=True, blank=True, default=None)
    sip = models.ForeignKey(
        SIP,
        to_field="uuid",
        null=True,
        blank=True,
        default=None,
        on_delete=models.CASCADE,
    )
    level_of_description = models.CharField(max_length=2014)
    sip_created = models.BooleanField(default=False)
    aip_created = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Arranged SIPs")

    def __str__(self):
        return six.text_type(
            _("%(original)s -> %(arrange)s")
            % {"original": self.original_path, "arrange": self.arrange_path}
        )

    @classmethod
    def create_many(cls, arranges):
        """Bulk create a list of SIPArrange model instances.

        If some of the SIPArrange instances already exist, bulk creation
        will fail and this will revert back to saving each instance
        individually ignoring the existing ones.
        """
        try:
            cls.objects.bulk_create(arranges, BULK_CREATE_BATCH_SIZE)
        except IntegrityError:
            for arrange in arranges:
                try:
                    arrange.save()
                except IntegrityError:
                    continue


class SIPArrangeAccessMapping(models.Model):
    """ Maps directories within SIPArrange to descriptive objects in a remote archival management system. """

    ARCHIVESSPACE = "archivesspace"
    ATOM = "atom"
    SYSTEMS = ((ARCHIVESSPACE, "ArchivesSpace"), (ATOM, "AtoM"))

    arrange_path = models.CharField(max_length=255)
    system = models.CharField(choices=SYSTEMS, default=ATOM, max_length=255)
    identifier = models.CharField(max_length=255)

    def __str__(self):
        return "arrange_path={s.arrange_path}, system={s.system}, identifier={s.identifier}".format(
            s=self
        )


class Identifier(models.Model):
    """Identifiers used by File, Directory SIP models. Used for Handle System
    handles/PIDs and maybe for other types of identifier in the future.
    """

    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    type = models.TextField(verbose_name=_("Identifier Type"), null=True, blank=False)
    value = models.TextField(
        verbose_name=_("Identifier Value"),
        help_text=_(
            "Used for premis:objectIdentifierType and"
            " premis:objectIdentifierValue in the METS file."
        ),
        null=True,
        blank=False,
    )

    def __str__(self):
        return u"Identifier {i.value} of type {i.type}".format(i=self)

    class Meta:
        db_table = u"Identifiers"


@python_2_unicode_compatible
class File(models.Model):
    """ Information about Files in units (Transfers, SIPs). """

    uuid = models.CharField(max_length=36, primary_key=True, db_column="fileUUID")
    sip = models.ForeignKey(
        SIP,
        db_column="sipUUID",
        to_field="uuid",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    transfer = models.ForeignKey(
        Transfer,
        db_column="transferUUID",
        to_field="uuid",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    # both actually `longblob` in the database
    originallocation = BlobTextField(db_column="originalLocation")
    currentlocation = BlobTextField(db_column="currentLocation", null=True)
    filegrpuse = models.CharField(
        max_length=50, db_column="fileGrpUse", default="Original"
    )
    filegrpuuid = models.CharField(max_length=36, db_column="fileGrpUUID", blank=True)
    checksum = models.CharField(max_length=128, db_column="checksum", blank=True)
    checksumtype = models.CharField(max_length=36, db_column="checksumType", blank=True)
    size = models.BigIntegerField(db_column="fileSize", null=True, blank=True)
    label = models.TextField(blank=True)
    modificationtime = models.DateTimeField(
        db_column="modificationTime", null=True, auto_now_add=True
    )
    enteredsystem = models.DateTimeField(db_column="enteredSystem", auto_now_add=True)
    removedtime = models.DateTimeField(db_column="removedTime", null=True, default=None)

    # This should hold any handles generated for the file.
    # Its format is expected to be "<NAMING_AUTHORITY>/<HANDLE>" i.e,.
    # "<NAMING_AUTHORITY>/<UUID>", e.g.,
    # "12345/6e6ea3f0-93ce-4798-bb75-a88e2d0d6f09". Note that neither the
    # resolver URL for constructing PURLs nor the qualifier (for constructing
    # qualified PURLs) should be included in this value. If needed, these
    # values can be constructed using the DashboardSettings rows with scope
    # 'handle'.
    identifiers = models.ManyToManyField("Identifier")

    class Meta:
        db_table = u"Files"
        # Additional fields indexed via raw migration (as they are blobs):
        # ("transfer", "currentlocation"),
        # ("sip", "currentlocation"),
        # ("transfer", "originallocation"),
        # ("sip", "originallocation"),
        index_together = (("sip", "filegrpuse"),)

    def __str__(self):
        return six.text_type(
            _("File %(uuid)s:%(originallocation)s now at %(currentlocation)s")
            % {
                "uuid": self.uuid,
                "originallocation": self.originallocation,
                "currentlocation": self.currentlocation,
            }
        )

    def add_custom_identifier(self, scheme, value):
        """Allow callers to add custom identifiers to the model's instance."""
        self.identifiers.create(type=scheme, value=value)


@python_2_unicode_compatible
class Directory(models.Model):
    """Information about Directories in units (Transfers, SIPs).
    Note: Directory instances are only created if the user explicitly
    configures Archivematica to assign UUIDs to directories.
    """

    uuid = models.CharField(max_length=36, primary_key=True, db_column="directoryUUID")
    sip = models.ForeignKey(
        SIP,
        db_column="sipUUID",
        to_field="uuid",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    transfer = models.ForeignKey(
        Transfer,
        db_column="transferUUID",
        to_field="uuid",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    originallocation = BlobTextField(db_column="originalLocation")
    currentlocation = BlobTextField(db_column="currentLocation", null=True)
    enteredsystem = models.DateTimeField(db_column="enteredSystem", auto_now_add=True)
    identifiers = models.ManyToManyField("Identifier")

    class Meta:
        db_table = u"Directories"

    def __str__(self):
        return six.text_type(
            _("Directory %(uuid)s: %(originallocation)s now at %(currentlocation)s")
            % {
                "uuid": self.uuid,
                "originallocation": self.originallocation,
                "currentlocation": self.currentlocation,
            }
        )

    def add_custom_identifier(self, scheme, value):
        """Allow callers to add custom identifiers to the model's instance."""
        self.identifiers.create(type=scheme, value=value)

    @classmethod
    def create_many(cls, dir_paths_uuids, unit_mdl, unit_type="transfer"):
        """Create ``Directory`` models to encode the relationship between each
        directory path/UUID entry in ``dir_paths_uuids`` and the ``Transfer``
        model that the directories are a part of. ``dir_paths_uuids`` is
        expected to be a dict instance where the ``originallocation`` field is
        optional. The ``originallocation`` but can be set according to the
        requirements of the PREMIS record that eventually needs to be created
        using this model.
        """
        unit_type = {"transfer": "transfer"}.get(unit_type, "sip")
        paths = []
        for dir_ in dir_paths_uuids:
            dir_path = dir_.get("currentLocation")
            dir_uuid = dir_.get("uuid")
            orig_path = dir_.get("originalLocation", dir_path)
            paths.append(
                cls(
                    **{
                        "uuid": dir_uuid,
                        unit_type: unit_mdl,
                        "originallocation": orig_path,
                        "currentlocation": dir_path,
                    }
                )
            )
        return cls.objects.bulk_create(paths)


@python_2_unicode_compatible
class FileFormatVersion(models.Model):
    """
    Link between a File and the FormatVersion it is identified as.

    TODO? Replace this with a foreign key from File to FormatVersion.
    """

    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    file_uuid = models.ForeignKey(
        "File", db_column="fileUUID", to_field="uuid", on_delete=models.CASCADE
    )
    format_version = models.ForeignKey(
        "fpr.FormatVersion",
        db_column="fileID",
        to_field="uuid",
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = u"FilesIdentifiedIDs"

    def __str__(self):
        return six.text_type(
            _("%(file)s is %(format)s")
            % {"file": self.file_uuid, "format": self.format_version}
        )


class JobQuerySet(models.QuerySet):
    def get_directory_name(self):
        """Return the directory name of a unit.

        This is a convenience manager method to obtain the directory name of a
        specific unit from a QuerySet of jobs associated to that unit.

        TODO(sevein): why is the name not a property of the unit?
        """
        try:
            job = self.first()
        # No jobs yet, e.g. not started; there will be no directory name yet.
        except IndexError:
            return _("(Unnamed)")
        return job.get_directory_name()


class Job(models.Model):
    jobuuid = UUIDField(db_column="jobUUID", primary_key=True)
    jobtype = models.CharField(max_length=250, db_column="jobType", blank=True)
    createdtime = models.DateTimeField(db_column="createdTime")
    createdtimedec = models.DecimalField(
        db_column="createdTimeDec", max_digits=26, decimal_places=10, default=0.0
    )
    directory = models.TextField(blank=True)
    sipuuid = models.CharField(
        max_length=36, db_column="SIPUUID", db_index=True
    )  # Foreign key to SIPs or Transfers
    unittype = models.CharField(max_length=50, db_column="unitType", blank=True)
    STATUS_UNKNOWN = 0
    STATUS_AWAITING_DECISION = 1
    STATUS_COMPLETED_SUCCESSFULLY = 2
    STATUS_EXECUTING_COMMANDS = 3
    STATUS_FAILED = 4
    STATUS = (
        (STATUS_UNKNOWN, _("Unknown")),
        (STATUS_AWAITING_DECISION, _("Awaiting decision")),
        (STATUS_COMPLETED_SUCCESSFULLY, _("Completed successfully")),
        (STATUS_EXECUTING_COMMANDS, _("Executing command(s)")),
        (STATUS_FAILED, _("Failed")),
    )
    currentstep = models.IntegerField(
        db_column="currentStep", choices=STATUS, default=0, blank=False
    )
    microservicegroup = models.CharField(
        max_length=50, db_column="microserviceGroup", blank=True
    )
    hidden = models.BooleanField(default=False)
    microservicechainlink = UUIDField(
        auto=False, null=True, blank=True, db_column="MicroServiceChainLinksPK"
    )
    subjobof = models.CharField(max_length=36, db_column="subJobOf", blank=True)

    objects = JobQuerySet.as_manager()

    class Meta:
        db_table = u"Jobs"
        index_together = (
            ("sipuuid", "createdtime", "createdtimedec"),
            ("sipuuid", "jobtype", "createdtime", "createdtimedec"),
            ("sipuuid", "currentstep", "microservicegroup", "microservicechainlink"),
            ("jobtype", "currentstep"),
        )

    @staticmethod
    def _match_directory_patterns(directory):
        """Attempt to match the two different regex variants we might
        receive in a Job.
        """
        MATCH_GROUP = "directory"
        NEW_TRANSFER_REGEX = r"^.*/(?P<directory>.*)/$"
        TRANSFER_REGEX = (
            r"^.*/(?P<directory>.*)-" r"[\w]{8}(-[\w]{4})" r"{3}-[\w]{12}[/]{0,1}$"
        )
        try:
            return re.search(TRANSFER_REGEX, directory).group(MATCH_GROUP)
        except AttributeError:
            pass
        try:
            directory = os.path.join(directory, "")
            return re.search(NEW_TRANSFER_REGEX, directory).group(MATCH_GROUP)
        except AttributeError:
            return

    def get_directory_name(self):
        if not self.directory:
            return self.sipuuid
        transfer_name = self._match_directory_patterns(self.directory)
        if not transfer_name:
            return self.sipuuid
        return transfer_name


class Task(models.Model):
    taskuuid = models.CharField(max_length=36, primary_key=True, db_column="taskUUID")
    job = models.ForeignKey(
        "Job", db_column="jobuuid", to_field="jobuuid", on_delete=models.CASCADE
    )
    createdtime = models.DateTimeField(db_column="createdTime")
    fileuuid = models.CharField(
        max_length=36, db_column="fileUUID", null=True, blank=True
    )
    # Actually a `longblob` in the database, since filenames may contain
    # arbitrary non-unicode characters - other blob and binary fields
    # have these types for the same reason.
    # Note that Django doesn't have a specific blob type, hence the use of
    # the char field types instead.
    filename = models.TextField(db_column="fileName", blank=True)
    execution = models.CharField(max_length=250, db_column="exec", blank=True)
    # actually a `varbinary(1000)` in the database
    arguments = models.CharField(max_length=1000, blank=True)
    starttime = models.DateTimeField(db_column="startTime", null=True, default=None)
    endtime = models.DateTimeField(db_column="endTime", null=True, default=None)
    client = models.CharField(max_length=50, blank=True)
    # stdout and stderror actually `longblobs` in the database
    stdout = models.TextField(db_column="stdOut", blank=True)
    stderror = models.TextField(db_column="stdError", blank=True)
    exitcode = models.BigIntegerField(db_column="exitCode", null=True, blank=True)

    class Meta:
        db_table = u"Tasks"


class AgentManager(models.Manager):

    # Objects with static identifiers. Item with ID 1 was abandoned.
    DEFAULT_ORGANIZATION_AGENT_PK = 2

    def default_organization_agent(self):
        return self.get(pk=self.DEFAULT_ORGANIZATION_AGENT_PK)

    def default_agents_query_keywords(self):
        """Returns QuerySet keyword arguments for the default agents."""
        return models.Q(pk=(self.DEFAULT_ORGANIZATION_AGENT_PK))

    def extend_queryset_with_preservation_system(self, agent_queryset):
        """Returns iterator wrapping the QuerySet with the preservation system agent."""
        return itertools.chain(
            (self.get_preservation_system_agent(),),
            agent_queryset,
        )

    def get_preservation_system_agent(self):
        """Returns synthetic agent describing the preservation system."""
        try:
            agent = self._preservation_system_agent
        except AttributeError:
            agent = self._preservation_system_agent = Agent(
                name="Archivematica",
                agenttype="software",
                identifiertype="preservation system",
                identifiervalue=get_preservation_system_identifier(),
            )
        return agent


class Agent(models.Model):
    """ PREMIS Agents created for the system.  """

    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    identifiertype = models.TextField(
        verbose_name=_("Agent Identifier Type"),
        null=True,
        db_column="agentIdentifierType",
    )
    identifiervalue = models.TextField(
        verbose_name=_("Agent Identifier Value"),
        help_text=_(
            "Used for premis:agentIdentifierValue and premis:linkingAgentIdentifierValue in the METS file."
        ),
        null=True,
        blank=False,
        db_column="agentIdentifierValue",
    )
    name = models.TextField(
        verbose_name=_("Agent Name"),
        help_text=_("Used for premis:agentName in the METS file."),
        null=True,
        blank=False,
        db_column="agentName",
    )
    agenttype = models.TextField(
        verbose_name=_("Agent Type"),
        help_text=_("Used for premis:agentType in the METS file."),
        db_column="agentType",
        default="organization",
    )

    objects = AgentManager()

    def __str__(self):
        return (
            u"{a.agenttype}; {a.identifiertype}: {a.identifiervalue}; {a.name}".format(
                a=self
            )
        )

    class Meta:
        db_table = u"Agents"


class UserProfile(models.Model):
    """ Extension of the User model for additional information. """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    agent = models.OneToOneField(Agent, on_delete=models.CASCADE)
    system_emails = models.BooleanField(
        default=True,
        help_text=_(
            "If checked, this user will receive system emails, such as Transfer Fail and Normalization Reports."
        ),
        verbose_name=_("Send system emails?"),
    )

    class Meta:
        db_table = u"main_userprofile"


class Report(models.Model):
    """ Reports of failures to display. """

    id = models.AutoField(primary_key=True, db_column="pk")
    unittype = models.CharField(max_length=50, db_column="unitType")
    unitname = models.CharField(max_length=50, db_column="unitName")
    unitidentifier = models.CharField(
        max_length=36, db_column="unitIdentifier"
    )  # Foreign key to SIP or Transfer
    content = models.TextField(db_column="content")
    created = models.DateTimeField(db_column="created", auto_now_add=True)

    class Meta:
        db_table = u"Reports"


@python_2_unicode_compatible
class RightsStatement(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk")
    metadataappliestotype = models.ForeignKey(
        MetadataAppliesToType,
        to_field="id",
        db_column="metadataAppliesToType",
        on_delete=models.CASCADE,
    )
    metadataappliestoidentifier = models.CharField(
        max_length=36, blank=True, db_column="metadataAppliesToidentifier"
    )
    rightsstatementidentifiertype = models.TextField(
        db_column="rightsStatementIdentifierType", blank=True, verbose_name=_("Type")
    )
    rightsstatementidentifiervalue = models.TextField(
        db_column="rightsStatementIdentifierValue", blank=True, verbose_name=_("Value")
    )
    rightsholder = models.IntegerField(
        db_column="fkAgent", default=0, verbose_name=_("Rights holder")
    )
    RIGHTS_BASIS_CHOICES = (
        ("Copyright", _("Copyright")),
        ("Statute", _("Statute")),
        ("License", _("License")),
        ("Donor", _("Donor")),
        ("Policy", _("Policy")),
        ("Other", _("Other")),
    )
    rightsbasis = models.CharField(
        db_column="rightsBasis",
        choices=RIGHTS_BASIS_CHOICES,
        max_length=64,
        verbose_name=_("Basis"),
        default="Copyright",
    )
    status = models.CharField(
        db_column="status",
        max_length=8,
        choices=METADATA_STATUS,
        default=METADATA_STATUS_ORIGINAL,
    )

    class Meta:
        db_table = u"RightsStatement"
        verbose_name = _("Rights Statement")

    def __str__(self):
        return six.text_type(
            _("%(basis)s for %(unit)s (%(id)s)")
            % {
                "basis": self.rightsbasis,
                "unit": self.metadataappliestoidentifier,
                "id": self.id,
            }
        )


class RightsStatementCopyright(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    rightsstatement = models.ForeignKey(
        RightsStatement, db_column="fkRightsStatement", on_delete=models.CASCADE
    )
    PREMIS_COPYRIGHT_STATUSES = (
        ("copyrighted", _("copyrighted")),
        ("public domain", _("public domain")),
        ("unknown", _("unknown")),
    )
    copyrightstatus = models.TextField(
        db_column="copyrightStatus",
        blank=False,
        verbose_name=_("Copyright status"),
        choices=PREMIS_COPYRIGHT_STATUSES,
        default="unknown",
    )
    copyrightjurisdiction = models.TextField(
        db_column="copyrightJurisdiction", verbose_name=_("Copyright jurisdiction")
    )
    copyrightstatusdeterminationdate = models.TextField(
        db_column="copyrightStatusDeterminationDate",
        blank=True,
        null=True,
        verbose_name=_("Copyright determination date"),
        help_text=_("Use ISO 8061 (YYYY-MM-DD)"),
    )
    copyrightapplicablestartdate = models.TextField(
        db_column="copyrightApplicableStartDate",
        blank=True,
        null=True,
        verbose_name=_("Copyright start date"),
        help_text=_("Use ISO 8061 (YYYY-MM-DD)"),
    )
    copyrightapplicableenddate = models.TextField(
        db_column="copyrightApplicableEndDate",
        blank=True,
        null=True,
        verbose_name=_("Copyright end date"),
        help_text=_("Use ISO 8061 (YYYY-MM-DD)"),
    )
    copyrightenddateopen = models.BooleanField(
        default=False,
        db_column="copyrightApplicableEndDateOpen",
        verbose_name=_("Open End Date"),
        help_text=_("Indicate end date is open"),
    )

    class Meta:
        db_table = u"RightsStatementCopyright"
        verbose_name = _("Rights: Copyright")


class RightsStatementCopyrightDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    rightscopyright = models.ForeignKey(
        RightsStatementCopyright,
        db_column="fkRightsStatementCopyrightInformation",
        on_delete=models.CASCADE,
    )
    copyrightdocumentationidentifiertype = models.TextField(
        db_column="copyrightDocumentationIdentifierType",
        verbose_name=_("Copyright document identification type"),
    )
    copyrightdocumentationidentifiervalue = models.TextField(
        db_column="copyrightDocumentationIdentifierValue",
        verbose_name=_("Copyright document identification value"),
    )
    copyrightdocumentationidentifierrole = models.TextField(
        db_column="copyrightDocumentationIdentifierRole",
        null=True,
        blank=True,
        verbose_name=_("Copyright document identification role"),
    )

    class Meta:
        db_table = u"RightsStatementCopyrightDocumentationIdentifier"
        verbose_name = _("Rights: Copyright: Docs ID")


class RightsStatementCopyrightNote(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    rightscopyright = models.ForeignKey(
        RightsStatementCopyright,
        db_column="fkRightsStatementCopyrightInformation",
        on_delete=models.CASCADE,
    )
    copyrightnote = models.TextField(
        db_column="copyrightNote", verbose_name=_("Copyright note")
    )

    class Meta:
        db_table = u"RightsStatementCopyrightNote"
        verbose_name = _("Rights: Copyright: Note")


class RightsStatementLicense(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    rightsstatement = models.ForeignKey(
        RightsStatement, db_column="fkRightsStatement", on_delete=models.CASCADE
    )
    licenseterms = models.TextField(
        db_column="licenseTerms", blank=True, null=True, verbose_name=_("License terms")
    )
    licenseapplicablestartdate = models.TextField(
        db_column="licenseApplicableStartDate",
        blank=True,
        null=True,
        verbose_name=_("License start date"),
        help_text=_("Use ISO 8061 (YYYY-MM-DD)"),
    )
    licenseapplicableenddate = models.TextField(
        db_column="licenseApplicableEndDate",
        blank=True,
        null=True,
        verbose_name=_("License end date"),
        help_text=_("Use ISO 8061 (YYYY-MM-DD)"),
    )
    licenseenddateopen = models.BooleanField(
        default=False,
        db_column="licenseApplicableEndDateOpen",
        verbose_name=_("Open End Date"),
        help_text=_("Indicate end date is open"),
    )

    class Meta:
        db_table = u"RightsStatementLicense"
        verbose_name = _("Rights: License")


class RightsStatementLicenseDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    rightsstatementlicense = models.ForeignKey(
        RightsStatementLicense,
        db_column="fkRightsStatementLicense",
        on_delete=models.CASCADE,
    )
    licensedocumentationidentifiertype = models.TextField(
        db_column="licenseDocumentationIdentifierType",
        verbose_name=_("License documentation identification type"),
    )
    licensedocumentationidentifiervalue = models.TextField(
        db_column="licenseDocumentationIdentifierValue",
        verbose_name=_("License documentation identification value"),
    )
    licensedocumentationidentifierrole = models.TextField(
        db_column="licenseDocumentationIdentifierRole",
        blank=True,
        null=True,
        verbose_name=_("License document identification role"),
    )

    class Meta:
        db_table = u"RightsStatementLicenseDocumentationIdentifier"
        verbose_name = _("Rights: License: Docs ID")


class RightsStatementLicenseNote(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    rightsstatementlicense = models.ForeignKey(
        RightsStatementLicense,
        db_column="fkRightsStatementLicense",
        on_delete=models.CASCADE,
    )
    licensenote = models.TextField(
        db_column="licenseNote", verbose_name=_("License note")
    )

    class Meta:
        db_table = u"RightsStatementLicenseNote"
        verbose_name = _("Rights: License: Note")


class RightsStatementRightsGranted(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk")
    rightsstatement = models.ForeignKey(
        RightsStatement, db_column="fkRightsStatement", on_delete=models.CASCADE
    )
    act = models.TextField(db_column="act")
    startdate = models.TextField(
        db_column="startDate",
        verbose_name=_("Start"),
        help_text=_("Use ISO 8061 (YYYY-MM-DD)"),
        blank=True,
        null=True,
    )
    enddate = models.TextField(
        db_column="endDate",
        verbose_name=_("End"),
        help_text=_("Use ISO 8061 (YYYY-MM-DD)"),
        blank=True,
        null=True,
    )
    enddateopen = models.BooleanField(
        default=False,
        db_column="endDateOpen",
        verbose_name=_("Open End Date"),
        help_text=_("Indicate end date is open"),
    )

    class Meta:
        db_table = u"RightsStatementRightsGranted"
        verbose_name = _("Rights: Granted")


class RightsStatementRightsGrantedNote(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    rightsgranted = models.ForeignKey(
        RightsStatementRightsGranted,
        related_name="notes",
        db_column="fkRightsStatementRightsGranted",
        on_delete=models.CASCADE,
    )
    rightsgrantednote = models.TextField(
        db_column="rightsGrantedNote", verbose_name=_("Rights note")
    )

    class Meta:
        db_table = u"RightsStatementRightsGrantedNote"
        verbose_name = _("Rights: Granted: Note")


class RightsStatementRightsGrantedRestriction(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk")
    rightsgranted = models.ForeignKey(
        RightsStatementRightsGranted,
        related_name="restrictions",
        db_column="fkRightsStatementRightsGranted",
        on_delete=models.CASCADE,
    )
    restriction = models.TextField(db_column="restriction")

    class Meta:
        db_table = u"RightsStatementRightsGrantedRestriction"
        verbose_name = _("Rights: Granted: Restriction")


class RightsStatementStatuteInformation(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk")
    rightsstatement = models.ForeignKey(
        RightsStatement, db_column="fkRightsStatement", on_delete=models.CASCADE
    )
    statutejurisdiction = models.TextField(
        db_column="statuteJurisdiction", verbose_name=_("Statute jurisdiction")
    )
    statutecitation = models.TextField(
        db_column="statuteCitation", verbose_name=_("Statute citation")
    )
    statutedeterminationdate = models.TextField(
        db_column="statuteInformationDeterminationDate",
        verbose_name=_("Statute determination date"),
        help_text=_("Use ISO 8061 (YYYY-MM-DD)"),
        blank=True,
        null=True,
    )
    statuteapplicablestartdate = models.TextField(
        db_column="statuteApplicableStartDate",
        blank=True,
        null=True,
        verbose_name=_("Statute start date"),
        help_text=_("Use ISO 8061 (YYYY-MM-DD)"),
    )
    statuteapplicableenddate = models.TextField(
        db_column="statuteApplicableEndDate",
        blank=True,
        null=True,
        verbose_name=_("Statute end date"),
        help_text=_("Use ISO 8061 (YYYY-MM-DD)"),
    )
    statuteenddateopen = models.BooleanField(
        default=False,
        db_column="statuteApplicableEndDateOpen",
        verbose_name=_("Open End Date"),
        help_text=_("Indicate end date is open"),
    )

    class Meta:
        db_table = u"RightsStatementStatuteInformation"
        verbose_name = _("Rights: Statute")


class RightsStatementStatuteInformationNote(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk")
    rightsstatementstatute = models.ForeignKey(
        RightsStatementStatuteInformation,
        db_column="fkRightsStatementStatuteInformation",
        on_delete=models.CASCADE,
    )
    statutenote = models.TextField(
        db_column="statuteNote", verbose_name=_("Statute note")
    )

    class Meta:
        db_table = u"RightsStatementStatuteInformationNote"
        verbose_name = _("Rights: Statute: Note")


class RightsStatementStatuteDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    rightsstatementstatute = models.ForeignKey(
        RightsStatementStatuteInformation,
        db_column="fkRightsStatementStatuteInformation",
        on_delete=models.CASCADE,
    )
    statutedocumentationidentifiertype = models.TextField(
        db_column="statuteDocumentationIdentifierType",
        verbose_name=_("Statute document identification type"),
    )
    statutedocumentationidentifiervalue = models.TextField(
        db_column="statuteDocumentationIdentifierValue",
        verbose_name=_("Statute document identification value"),
    )
    statutedocumentationidentifierrole = models.TextField(
        db_column="statuteDocumentationIdentifierRole",
        blank=True,
        null=True,
        verbose_name=_("Statute document identification role"),
    )

    class Meta:
        db_table = u"RightsStatementStatuteDocumentationIdentifier"
        verbose_name = _("Rights: Statute: Docs ID")


class RightsStatementOtherRightsInformation(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    rightsstatement = models.ForeignKey(
        RightsStatement, db_column="fkRightsStatement", on_delete=models.CASCADE
    )
    otherrightsbasis = models.TextField(
        db_column="otherRightsBasis",
        verbose_name=_("Other rights basis"),
        default="Other",
    )
    otherrightsapplicablestartdate = models.TextField(
        db_column="otherRightsApplicableStartDate",
        blank=True,
        null=True,
        verbose_name=_("Other rights start date"),
        help_text=_("Use ISO 8061 (YYYY-MM-DD)"),
    )
    otherrightsapplicableenddate = models.TextField(
        db_column="otherRightsApplicableEndDate",
        blank=True,
        null=True,
        verbose_name=_("Other rights end date"),
        help_text=_("Use ISO 8061 (YYYY-MM-DD)"),
    )
    otherrightsenddateopen = models.BooleanField(
        default=False,
        db_column="otherRightsApplicableEndDateOpen",
        verbose_name=_("Open End Date"),
        help_text=_("Indicate end date is open"),
    )

    class Meta:
        db_table = u"RightsStatementOtherRightsInformation"
        verbose_name = _("Rights: Other")


class RightsStatementOtherRightsDocumentationIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk", editable=False)
    rightsstatementotherrights = models.ForeignKey(
        RightsStatementOtherRightsInformation,
        db_column="fkRightsStatementOtherRightsInformation",
        on_delete=models.CASCADE,
    )
    otherrightsdocumentationidentifiertype = models.TextField(
        db_column="otherRightsDocumentationIdentifierType",
        verbose_name=_("Other rights document identification type"),
    )
    otherrightsdocumentationidentifiervalue = models.TextField(
        db_column="otherRightsDocumentationIdentifierValue",
        verbose_name=_("Other right document identification value"),
    )
    otherrightsdocumentationidentifierrole = models.TextField(
        db_column="otherRightsDocumentationIdentifierRole",
        blank=True,
        null=True,
        verbose_name=_("Other rights document identification role"),
    )

    class Meta:
        db_table = u"RightsStatementOtherRightsDocumentationIdentifier"
        verbose_name = _("Rights: Other: Docs ID")


class RightsStatementOtherRightsInformationNote(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk")
    rightsstatementotherrights = models.ForeignKey(
        RightsStatementOtherRightsInformation,
        db_column="fkRightsStatementOtherRightsInformation",
        on_delete=models.CASCADE,
    )
    otherrightsnote = models.TextField(
        db_column="otherRightsNote", verbose_name=_("Other rights note")
    )

    class Meta:
        db_table = u"RightsStatementOtherRightsNote"
        verbose_name = _("Rights: Other: Note")


class RightsStatementLinkingAgentIdentifier(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk")
    rightsstatement = models.ForeignKey(
        RightsStatement, db_column="fkRightsStatement", on_delete=models.CASCADE
    )
    linkingagentidentifiertype = models.TextField(
        db_column="linkingAgentIdentifierType",
        verbose_name=_("Linking Agent"),
        blank=True,
    )
    linkingagentidentifiervalue = models.TextField(
        db_column="linkingAgentIdentifierValue",
        verbose_name=_("Linking Agent Value"),
        blank=True,
    )

    class Meta:
        db_table = u"RightsStatementLinkingAgentIdentifier"
        verbose_name = _("Rights: Agent")


class UnitVariableManager(models.Manager):
    def update_variable(self, unit_type, unit_uuid, variable, value, link_id=None):
        """Persist unit variable."""
        defaults = {"variablevalue": value, "microservicechainlink": link_id}
        return self.get_queryset().update_or_create(
            unittype=unit_type, unituuid=unit_uuid, variable=variable, defaults=defaults
        )

    def update_active_agent(self, unit_type, unit_id, user_id):
        """Persist active agent given the user ID."""
        agent_id = (
            User.objects.select_related("userprofile")
            .get(id=user_id)
            .userprofile.agent_id
        )
        return self.update_variable(unit_type, unit_id, "activeAgent", agent_id)

    def update_processing_configuration(
        self, unit_type, unit_uuid, processing_configuration
    ):
        return self.update_variable(
            unit_type, unit_uuid, "processingConfiguration", processing_configuration
        )


class UnitVariable(models.Model):
    id = UUIDPkField()
    unittype = models.CharField(
        max_length=50, null=True, blank=True, db_column="unitType"
    )
    unituuid = models.CharField(
        max_length=36,
        null=True,
        help_text=_("Semantically a foreign key to SIP or Transfer"),
        db_column="unitUUID",
    )
    variable = models.TextField(null=True, db_column="variable")
    variablevalue = models.TextField(null=True, db_column="variableValue")
    microservicechainlink = UUIDField(
        auto=False, null=True, blank=True, db_column="microServiceChainLink"
    )
    createdtime = models.DateTimeField(db_column="createdTime", auto_now_add=True)
    updatedtime = models.DateTimeField(db_column="updatedTime", auto_now=True)

    objects = UnitVariableManager()

    class Meta:
        db_table = u"UnitVariables"
        # Fields indexed via raw migration (as they are blobs):
        # ("unituuid", "unittype", "variable")


class ArchivesSpaceDIPObjectResourcePairing(models.Model):
    id = models.AutoField(primary_key=True, db_column="pk")
    # TODO these should be foreign keys?
    dipuuid = models.CharField(max_length=50, db_column="dipUUID")
    fileuuid = models.CharField(max_length=50, db_column="fileUUID")
    # This field holds URL fragments, for instance:
    # /repositories/2/archival_objects/1
    resourceid = models.CharField(max_length=150, db_column="resourceId")

    def __str__(self):
        return "ArchivesSpace Pairing<dipuuid: {s.dipuuid}, resourceid: {s.resourceid}>".format(
            s=self
        )

    class Meta:
        db_table = u"ArchivesSpaceDIPObjectResourcePairing"
        # Table name length is fine, but if the verbose name is too
        # long it can result in confusing errors when trying to
        # set up permissions: https://code.djangoproject.com/ticket/18866
        verbose_name = _("ASDIPObjectResourcePairing")


class ArchivesSpaceDigitalObject(models.Model):
    """
    Represents a digital object to be created in ArchivesSpace at the time an AIP is stored by Archivematica.
    """

    sip = models.ForeignKey("SIP", to_field="uuid", null=True, on_delete=models.CASCADE)
    resourceid = models.CharField(max_length=150)
    label = models.CharField(max_length=255, blank=True)
    title = models.TextField(blank=True)
    started = models.BooleanField(
        default=False,
        help_text=_(
            "Whether or not a SIP has been started using files in this digital object."
        ),
    )
    remoteid = models.CharField(
        max_length=150,
        blank=True,
        help_text=_(
            "ID in the remote ArchivesSpace system, after digital object has been created."
        ),
    )


class TransferMetadataSet(models.Model):
    id = UUIDPkField()
    createdtime = models.DateTimeField(db_column="createdTime", auto_now_add=True)
    createdbyuserid = models.IntegerField(db_column="createdByUserID")

    class Meta:
        db_table = u"TransferMetadataSets"


@python_2_unicode_compatible
class TransferMetadataField(models.Model):
    id = UUIDPkField()
    createdtime = models.DateTimeField(
        db_column="createdTime", auto_now_add=True, null=True
    )
    fieldlabel = models.CharField(max_length=50, blank=True, db_column="fieldLabel")
    fieldname = models.CharField(max_length=50, db_column="fieldName")
    fieldtype = models.CharField(max_length=50, db_column="fieldType")
    optiontaxonomy = models.ForeignKey(
        "Taxonomy",
        db_column="optionTaxonomyUUID",
        to_field="id",
        null=True,
        on_delete=models.CASCADE,
    )
    sortorder = models.IntegerField(default=0, db_column="sortOrder")

    class Meta:
        db_table = u"TransferMetadataFields"

    def __str__(self):
        return self.fieldlabel


class TransferMetadataFieldValue(models.Model):
    id = UUIDPkField()
    createdtime = models.DateTimeField(db_column="createdTime", auto_now_add=True)
    set = models.ForeignKey(
        "TransferMetadataSet",
        db_column="setUUID",
        to_field="id",
        on_delete=models.CASCADE,
    )
    field = models.ForeignKey(
        "TransferMetadataField",
        db_column="fieldUUID",
        to_field="id",
        on_delete=models.CASCADE,
    )
    fieldvalue = models.TextField(blank=True, db_column="fieldValue")

    class Meta:
        db_table = u"TransferMetadataFieldValues"


# Taxonomies and their field definitions are in separate tables
# to leave room for future expansion. The possible taxonomy terms are
# designed to be editable, and forms to do so exist. (Forms for editing and
# defining new fields are present in the code but currently disabled.)
@python_2_unicode_compatible
class Taxonomy(models.Model):
    id = UUIDPkField()
    createdtime = models.DateTimeField(
        db_column="createdTime", auto_now_add=True, null=True
    )
    name = models.CharField(max_length=255, blank=True, db_column="name")
    type = models.CharField(max_length=50, default="open")

    class Meta:
        db_table = u"Taxonomies"

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class TaxonomyTerm(models.Model):
    id = UUIDPkField()
    createdtime = models.DateTimeField(
        db_column="createdTime", auto_now_add=True, null=True
    )
    taxonomy = models.ForeignKey(
        "Taxonomy", db_column="taxonomyUUID", to_field="id", on_delete=models.CASCADE
    )
    term = models.CharField(max_length=255, db_column="term")

    class Meta:
        db_table = u"TaxonomyTerms"

    def __str__(self):
        return self.term


@python_2_unicode_compatible
class FPCommandOutput(models.Model):
    file = models.ForeignKey(
        "File", db_column="fileUUID", to_field="uuid", on_delete=models.CASCADE
    )
    content = models.TextField(null=True)
    rule = models.ForeignKey(
        "fpr.FPRule", db_column="ruleUUID", to_field="uuid", on_delete=models.CASCADE
    )

    # Table name is main_fpcommandoutput

    def __str__(self):
        return u"<file: {file}; rule: {rule}; content: {content}".format(
            file=self.file, rule=self.rule, content=self.content[:20]
        )


class FileID(models.Model):
    """
    This table duplicates file ID values from FPR formats. It predates the current FPR tables.

    This table may be removed in the future.
    """

    id = models.AutoField(primary_key=True, db_column="pk")
    file = models.ForeignKey(
        "File", null=True, db_column="fileUUID", blank=True, on_delete=models.CASCADE
    )
    format_name = models.TextField(db_column="formatName", blank=True)
    format_version = models.TextField(db_column="formatVersion", blank=True)
    format_registry_name = models.TextField(db_column="formatRegistryName", blank=True)
    format_registry_key = models.TextField(db_column="formatRegistryKey", blank=True)

    class Meta:
        db_table = "FilesIDs"


@python_2_unicode_compatible
class LevelOfDescription(models.Model):
    id = UUIDPkField()
    name = models.CharField(max_length=1024)  # seems long, but AtoM allows this much
    # sortorder should be unique, but is not defined so here to enable swapping
    sortorder = models.IntegerField(default=0, db_column="sortOrder")

    def __str__(self):
        return six.text_type(
            _("%(sortorder)s: %(name)s")
            % {"sortorder": self.sortorder, "name": self.name}
        )
