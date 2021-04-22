# -*- coding: utf-8 -*-
"""
:mod:`fpr.models`

Describes the data model for the FPR

"""
from __future__ import absolute_import

import logging

from django.db import connection, models
from django.utils.translation import ugettext_lazy as _
from django.utils.six import python_2_unicode_compatible

from autoslug import AutoSlugField
from django_extensions.db.fields import UUIDField

from django.core.validators import ValidationError
from django.core.exceptions import NON_FIELD_ERRORS

logger = logging.getLogger(__name__)

# ############################## API V2 MODELS ###############################

# ########### MANAGERS ############


class Enabled(models.Manager):
    """Manager to only return enabled objects.

    Filters by enabled=True."""

    def get_queryset(self):
        return super(Enabled, self).get_queryset().filter(enabled=True)

    def get_query_set(self):
        return super(Enabled, self).get_query_set().filter(enabled=True)


# ########### MIXINS ############


class VersionedModel(models.Model):
    replaces = models.ForeignKey(
        "self",
        to_field="uuid",
        null=True,
        blank=True,
        verbose_name=_("the related model"),
        on_delete=models.CASCADE,
    )
    enabled = models.BooleanField(_("enabled"), default=True)
    lastmodified = models.DateTimeField(_("last modified"), auto_now_add=True)

    def save(self, replacing=None, *args, **kwargs):
        if replacing:
            self.replaces = replacing
            # Force it to create a new row
            self.uuid = None
            self.pk = None
            self.enabled = (
                True  # in case the version was created using an older version
            )
            replacing.enabled = False
            replacing.save()
        super(VersionedModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True

    objects = models.Manager()
    active = Enabled()


# ########### FORMATS ############


class FormatManager(models.Manager):
    def get_full_list(self):
        """Detailed list of formats including PRONOM IDs.

        This is used by ``views.format_list`` so we can return the full list of
        formats making a single query to the database. Using our initial
        dataset, we were making more than 2k queries. Looking up the PRONOM IDs
        on each result added other 2k queries.

        This approach is not ideal and it should be revisited once ``fpr``
        becomes part of the Dashboard. In the future, we could use a paginator
        or DataTables + XHR (e.g. via ``django-datatables_view``). Currently,
        it is hard to make changes like this because of they way that templates
        and JavaScript code is arranged. This is a temporary fix!
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    fpr_format.id,
                    fpr_format.uuid,
                    fpr_format.description,
                    fpr_format.slug,
                    fpr_formatgroup.slug AS group_slug,
                    fpr_formatgroup.description AS group_name,
                    group_concat(fpr_formatversion.pronom_id) AS pronom_ids
                FROM fpr_format
                LEFT JOIN fpr_formatgroup
                    ON (fpr_format.group_id = fpr_formatgroup.uuid)
                LEFT JOIN fpr_formatversion
                    ON (fpr_format.uuid = fpr_formatversion.format_id
                        AND fpr_formatversion.pronom_id != "")
                GROUP BY fpr_format.id;
            """
            )
            ret = []
            for row in cursor.fetchall():
                # Include PRONOM IDs (up to three) in the format description.
                description = row[2]
                pronom_ids = row[6]
                if pronom_ids:
                    pronom_ids = pronom_ids.split(",")
                    if len(pronom_ids) > 3:
                        pronom_ids = pronom_ids[:3]
                        pronom_ids.append("...")
                    description = "{} ({})".format(description, ", ".join(pronom_ids))
                # Hydrate model.
                m = self.model(
                    id=row[0], uuid=row[1], description=description, slug=row[3]
                )
                m.group_slug = row[4]
                m.group_name = row[5]
                ret.append(m)
            return ret


@python_2_unicode_compatible
class Format(models.Model):
    """User-friendly description of format.

    Collects multiple related FormatVersions to one conceptual version.

    Eg. GIF, Word file."""

    uuid = UUIDField(
        editable=False, unique=True, version=4, help_text=_("Unique identifier")
    )
    description = models.CharField(
        _("description"), max_length=128, help_text=_("Common name of format")
    )
    group = models.ForeignKey(
        "FormatGroup",
        to_field="uuid",
        null=True,
        verbose_name=_("the related group"),
        on_delete=models.CASCADE,
    )
    slug = AutoSlugField(_("slug"), populate_from="description", unique=True)

    objects = FormatManager()

    class Meta:
        verbose_name = _("Format")
        ordering = ["group", "description"]

    def __str__(self):
        return u"{}: {}".format(self.group.description, self.description)


@python_2_unicode_compatible
class FormatGroup(models.Model):
    """ Group/classification for formats.  Eg. image, video, audio. """

    uuid = UUIDField(
        editable=False, unique=True, version=4, help_text=_("Unique identifier")
    )
    description = models.CharField(_("description"), max_length=128)
    slug = AutoSlugField(_("slug"), populate_from="description", unique=True)

    class Meta:
        verbose_name = _("Format group")
        ordering = ["description"]

    def __str__(self):
        return u"{}".format(self.description)


@python_2_unicode_compatible
class FormatVersion(VersionedModel, models.Model):
    """ Format that a tool identifies. """

    uuid = UUIDField(
        editable=False, unique=True, version=4, help_text=_("Unique identifier")
    )
    format = models.ForeignKey(
        "Format",
        to_field="uuid",
        related_name="version_set",
        null=True,
        verbose_name=_("the related format"),
        on_delete=models.CASCADE,
    )
    version = models.CharField(_("version"), max_length=10, null=True, blank=True)
    pronom_id = models.CharField(_("pronom id"), max_length=32, null=True, blank=True)
    description = models.CharField(
        _("description"),
        max_length=128,
        null=True,
        blank=True,
        help_text=_("Formal name to go in the METS file."),
    )
    access_format = models.BooleanField(_("access format"), default=False)
    preservation_format = models.BooleanField(_("preservation format"), default=False)

    slug = AutoSlugField(
        populate_from="description", unique_with="format", always_update=True
    )

    class Meta:
        verbose_name = _("Format version")
        ordering = ["format", "description"]

    def validate_unique(self, *args, **kwargs):
        super(FormatVersion, self).validate_unique(*args, **kwargs)

        if len(self.pronom_id) > 0:
            qs = self.__class__._default_manager.filter(
                pronom_id=self.pronom_id, enabled=1
            )

            if not self._state.adding and self.pk is not None:
                qs = qs.exclude(pk=self.pk)

            if qs.exists():
                raise ValidationError(
                    {
                        NON_FIELD_ERRORS: [
                            _(
                                "Unable to save, an active Format Version  with this pronom id already exists."
                            )
                        ]
                    }
                )

    def __str__(self):
        return _("%(format)s: %(description)s (%(pronom_id)s)") % {
            "format": self.format,
            "description": self.description,
            "pronom_id": self.pronom_id,
        }


# ########### ID TOOLS ############


@python_2_unicode_compatible
class IDCommand(VersionedModel, models.Model):
    """Command to run an IDToolConfig and parse the output.

    IDCommand runs 'script' (which runs an IDTool with a specific IDToolConfig)
    and parses the output."""

    uuid = UUIDField(
        editable=False, unique=True, version=4, help_text=_("Unique identifier")
    )
    description = models.CharField(
        _("description"), max_length=256, help_text=_("Name to identify script")
    )
    CONFIG_CHOICES = (
        ("PUID", _("PUID")),
        ("MIME", _("MIME type")),
        ("ext", _("File extension")),
    )
    config = models.CharField(_("configuration"), max_length=4, choices=CONFIG_CHOICES)

    script = models.TextField(_("script"), help_text=_("Script to be executed."))
    SCRIPT_TYPE_CHOICES = (
        ("bashScript", _("Bash script")),
        ("pythonScript", _("Python script")),
        ("command", _("Command line")),
        ("as_is", _("No shebang needed")),
    )
    script_type = models.CharField(
        _("script type"), max_length=16, choices=SCRIPT_TYPE_CHOICES
    )
    tool = models.ForeignKey(
        "IDTool",
        to_field="uuid",
        null=True,
        verbose_name=_("the related tool"),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Format identification command")
        ordering = ["description"]

    def __str__(self):
        return _("%(tool)s %(config)s runs %(command)s") % {
            "tool": self.tool,
            "config": self.get_config_display(),
            "command": self.description,
        }

    def save(self, *args, **kwargs):
        """Override save() to ensure that only one command is enabled."""
        if self.enabled:
            try:
                cmd = IDCommand.objects.get(enabled=True)
            except IDCommand.DoesNotExist:
                pass
            else:
                if cmd != self:
                    cmd.enabled = False
                    cmd.save()
        super(IDCommand, self).save(*args, **kwargs)


@python_2_unicode_compatible
class IDRule(VersionedModel, models.Model):
    """ Mapping between an IDCommand output and a FormatVersion. """

    uuid = UUIDField(
        editable=False, unique=True, version=4, help_text=_("Unique identifier")
    )
    command = models.ForeignKey(
        "IDCommand",
        to_field="uuid",
        verbose_name=_("the related command"),
        on_delete=models.CASCADE,
    )
    format = models.ForeignKey(
        "FormatVersion",
        to_field="uuid",
        verbose_name=_("the related format"),
        on_delete=models.CASCADE,
    )
    # Output from IDToolConfig.command to match on that gives the format
    command_output = models.TextField(_("command output"))

    class Meta:
        verbose_name = _("Format identification rule")

    def validate_unique(self, *args, **kwargs):
        super(IDRule, self).validate_unique(*args, **kwargs)

        qs = self.__class__._default_manager.filter(
            command=self.command, command_output=self.command_output, enabled=1
        )

        if not self._state.adding and self.pk is not None:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            raise ValidationError(
                {
                    NON_FIELD_ERRORS: [
                        _(
                            "Unable to save, a rule with this output already exists for this command."
                        )
                    ]
                }
            )

    def __str__(self):
        return _("Format identification rule %(uuid)s") % {"uuid": self.uuid}

    def long_name(self):
        return _("%(command)s with %(output)s is %(format)s") % {
            "command": self.command,
            "output": self.command_output,
            "format": self.format,
        }


@python_2_unicode_compatible
class IDTool(models.Model):
    """ Tool used to identify formats.  Eg. DROID """

    uuid = UUIDField(
        editable=False, unique=True, version=4, help_text=_("Unique identifier")
    )
    description = models.CharField(
        _("description"), max_length=256, help_text=_("Name of tool")
    )
    version = models.CharField(_("version"), max_length=64)
    enabled = models.BooleanField(_("enabled"), default=True)
    slug = AutoSlugField(
        _("slug"), populate_from="_slug", always_update=True, unique=True
    )

    class Meta:
        verbose_name = _("Format identification tool")

    objects = models.Manager()
    active = Enabled()

    def __str__(self):
        return _("%(description)s") % {"description": self.description}

    def _slug(self):
        """ Returns string to be slugified. """
        src = "{} {}".format(self.description, self.version)
        encoded = src.encode("utf-8")[: self._meta.get_field("slug").max_length]
        return encoded.decode("utf-8", "ignore")


# ########### NORMALIZATION ############


@python_2_unicode_compatible
class FPRule(VersionedModel, models.Model):
    uuid = UUIDField(
        editable=False, unique=True, version=4, help_text=_("Unique identifier")
    )

    ACCESS = "access"
    CHARACTERIZATION = "characterization"
    EXTRACTION = "extract"
    PRESERVATION = "preservation"
    THUMBNAIL = "thumbnail"
    TRANSCRIPTION = "transcription"
    VALIDATION = "validation"
    POLICY = "policy_check"
    DEFAULT_ACCESS = "default_access"
    DEFAULT_CHARACTERIZATION = "default_characterization"
    DEFAULT_THUMBNAIL = "default_thumbnail"
    USAGES = (
        ACCESS,
        CHARACTERIZATION,
        EXTRACTION,
        PRESERVATION,
        THUMBNAIL,
        TRANSCRIPTION,
        VALIDATION,
        POLICY,
        DEFAULT_ACCESS,
        DEFAULT_CHARACTERIZATION,
        DEFAULT_THUMBNAIL,
    )
    DISPLAY_CHOICES = (
        (ACCESS, _("Access")),
        (CHARACTERIZATION, _("Characterization")),
        (EXTRACTION, _("Extract")),
        (PRESERVATION, _("Preservation")),
        (THUMBNAIL, _("Thumbnail")),
        (TRANSCRIPTION, _("Transcription")),
        (VALIDATION, _("Validation")),
        (POLICY, _("Validation against a policy")),
    )
    HIDDEN_CHOICES = (
        (DEFAULT_ACCESS, _("Default access")),
        (DEFAULT_CHARACTERIZATION, _("Default characterization")),
        (DEFAULT_THUMBNAIL, _("Default thumbnail")),
    )
    # There are three categories of Normalization we want to group together,
    # and 'extraction' has a different FPRule name.
    USAGE_MAP = {
        "normalization": (DEFAULT_ACCESS, ACCESS, PRESERVATION, THUMBNAIL),
        "characterization": (CHARACTERIZATION, DEFAULT_CHARACTERIZATION),
        "extraction": (EXTRACTION,),
        "validation": (VALIDATION, POLICY),
    }
    PURPOSE_CHOICES = DISPLAY_CHOICES + HIDDEN_CHOICES
    purpose = models.CharField(_("purpose"), max_length=32, choices=PURPOSE_CHOICES)
    command = models.ForeignKey(
        "FPCommand",
        to_field="uuid",
        verbose_name=_("the related command"),
        on_delete=models.CASCADE,
    )
    format = models.ForeignKey(
        "FormatVersion",
        to_field="uuid",
        verbose_name=_("the related format"),
        on_delete=models.CASCADE,
    )

    count_attempts = models.IntegerField(_("count attempts"), default=0)
    count_okay = models.IntegerField(_("count okay"), default=0)
    count_not_okay = models.IntegerField(_("count not okay"), default=0)

    class Meta:
        verbose_name = _("Format policy rule")

    # def validate_unique(self, *args, **kwargs):
    #     super(FPRule, self).validate_unique(*args, **kwargs)

    #     qs = self.__class__._default_manager.filter(
    #         purpose=self.purpose,
    #         command=self.command,
    #         format=self.format,
    #         enabled=1
    #     )

    #     if not self._state.adding and self.pk is not None:
    #         qs = qs.exclude(pk=self.pk)

    #     if qs.exists():
    #         raise ValidationError( {
    #             NON_FIELD_ERRORS:('Unable to save, an active Rule for this purpose and format and command already exists.',)})

    def __str__(self):
        return _("Format policy rule %(uuid)s") % {"uuid": self.uuid}

    def long_name(self):
        return _("Normalize %(format)s for %(purpose)s via %(command)s") % {
            "format": self.format,
            "purpose": self.get_purpose_display(),
            "command": self.command,
        }


@python_2_unicode_compatible
class FPCommand(VersionedModel, models.Model):
    uuid = UUIDField(
        editable=False, unique=True, version=4, help_text=_("Unique identifier")
    )
    # ManyToManyField may not be the best choice here
    tool = models.ForeignKey(
        "FPTool",
        limit_choices_to={"enabled": True},
        to_field="uuid",
        null=True,
        verbose_name=_("the related tool"),
        on_delete=models.CASCADE,
    )
    description = models.CharField(_("description"), max_length=256)
    command = models.TextField(_("command"))
    SCRIPT_TYPE_CHOICES = (
        ("bashScript", _("Bash script")),
        ("pythonScript", _("Python script")),
        ("command", _("Command line")),
        ("as_is", _("No shebang needed")),
    )
    script_type = models.CharField(
        _("script type"), max_length=16, choices=SCRIPT_TYPE_CHOICES
    )
    output_location = models.TextField(_("output location"), null=True, blank=True)
    output_format = models.ForeignKey(
        "FormatVersion",
        to_field="uuid",
        null=True,
        blank=True,
        verbose_name=_("the related output format"),
        on_delete=models.CASCADE,
    )
    COMMAND_USAGE_CHOICES = (
        ("characterization", _("Characterization")),
        ("event_detail", _("Event Detail")),
        ("extraction", _("Extraction")),
        ("normalization", _("Normalization")),
        ("transcription", _("Transcription")),
        ("validation", _("Validation")),
        ("verification", _("Verification")),
    )
    command_usage = models.CharField(
        _("command usage"), max_length=16, choices=COMMAND_USAGE_CHOICES
    )
    verification_command = models.ForeignKey(
        "self",
        to_field="uuid",
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("the related verification command"),
        on_delete=models.CASCADE,
    )
    event_detail_command = models.ForeignKey(
        "self",
        to_field="uuid",
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("the related event detail command"),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Format policy command")
        ordering = ["description"]

    def __str__(self):
        return u"{}".format(self.description)


@python_2_unicode_compatible
class FPTool(models.Model):
    """ Tool used to perform normalization.  Eg. convert, ffmpeg, ps2pdf. """

    uuid = UUIDField(
        editable=False, unique=True, version=4, help_text=_("Unique identifier")
    )
    description = models.CharField(
        _("description"), max_length=256, help_text=_("Name of tool")
    )
    version = models.CharField(_("version"), max_length=64)
    enabled = models.BooleanField(_("enabled"), default=True)
    slug = AutoSlugField(_("slug"), populate_from="_slug", unique=True)
    # Many to many field is on FPCommand

    class Meta:
        verbose_name = _("Normalization tool")

    def __str__(self):
        return _("%(description)s") % {"description": self.description}

    def _slug(self):
        """ Returns string to be slugified. """
        src = "{} {}".format(self.description, self.version)
        encoded = src.encode("utf-8")[: self._meta.get_field("slug").max_length]
        return encoded.decode("utf-8", "ignore")
