"""
:mod:`fpr.models`

Describes the data model for the FPR

"""
import logging
import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _

from autoslug import AutoSlugField
from django_extensions.db.fields import UUIDField

from django.core.validators import ValidationError
from django.core.exceptions import NON_FIELD_ERRORS

logger = logging.getLogger(__name__)

# ############################## API V2 MODELS ###############################

# ########### MANAGERS ############


class Enabled(models.Manager):
    """ Manager to only return enabled objects.

    Filters by enabled=True.  """
    def get_queryset(self):
        return super(Enabled, self).get_queryset().filter(enabled=True)

    def get_query_set(self):
        return super(Enabled, self).get_query_set().filter(enabled=True)


# ########### MIXINS ############

class VersionedModel(models.Model):
    replaces = models.ForeignKey('self', to_field='uuid', null=True, blank=True, verbose_name=_('the related model'))
    enabled = models.BooleanField(_('enabled'), default=True)
    lastmodified = models.DateTimeField(_('last modified'), auto_now_add=True)

    def save(self, replacing=None, *args, **kwargs):
        if replacing:
            self.replaces = replacing
            # Force it to create a new row
            self.uuid = None
            self.pk = None
            self.enabled = True  # in case the version was created using an older version
            replacing.enabled = False
            replacing.save()
        super(VersionedModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True

    objects = models.Manager()
    active = Enabled()

# ########### FORMATS ############


class Format(models.Model):
    """ User-friendly description of format.

    Collects multiple related FormatVersions to one conceptual version.

    Eg. GIF, Word file."""
    uuid = UUIDField(editable=False, unique=True, version=4, help_text=_("Unique identifier"))
    description = models.CharField(_('description'), max_length=128, help_text=_("Common name of format"))
    group = models.ForeignKey('FormatGroup', to_field='uuid', null=True, verbose_name=_('the related group'))
    slug = AutoSlugField(_('slug'), populate_from='description', unique=True)

    class Meta:
        verbose_name = _("Format")
        ordering = ['group', 'description']

    def __unicode__(self):
        return u"{}: {}".format(self.group.description, self.description)


class FormatGroup(models.Model):
    """ Group/classification for formats.  Eg. image, video, audio. """
    uuid = UUIDField(editable=False, unique=True, version=4, help_text=_("Unique identifier"))
    description = models.CharField(_('description'), max_length=128)
    slug = AutoSlugField(_('slug'), populate_from='description', unique=True)

    class Meta:
        verbose_name = _("Format group")
        ordering = ['description']

    def __unicode__(self):
        return u"{}".format(self.description)


class FormatVersion(VersionedModel, models.Model):
    """ Format that a tool identifies. """
    uuid = UUIDField(editable=False, unique=True, version=4, help_text=_("Unique identifier"))
    format = models.ForeignKey('Format', to_field='uuid', related_name='version_set', null=True, verbose_name=_('the related format'))
    version = models.CharField(_('version'), max_length=10, null=True, blank=True)
    pronom_id = models.CharField(_('pronom id'), max_length=32, null=True, blank=True)
    description = models.CharField(_('description'), max_length=128, null=True, blank=True, help_text=_('Formal name to go in the METS file.'))
    access_format = models.BooleanField(_('access format'), default=False)
    preservation_format = models.BooleanField(_('preservation format'), default=False)

    slug = AutoSlugField(populate_from='description', unique_with='format', always_update=True)

    class Meta:
        verbose_name = _("Format version")
        ordering = ['format', 'description']

    def validate_unique(self, *args, **kwargs):
        super(FormatVersion, self).validate_unique(*args, **kwargs)

        if len(self.pronom_id) > 0:
            qs = self.__class__._default_manager.filter(
                pronom_id=self.pronom_id,
                enabled=1
            )

            if not self._state.adding and self.pk is not None:
                qs = qs.exclude(pk=self.pk)

            if qs.exists():
                raise ValidationError({
                    NON_FIELD_ERRORS: [_('Unable to save, an active Format Version  with this pronom id already exists.')]
                })

    def __unicode__(self):
        return _("%(format)s: %(description)s (%(pronom_id)s)") % {'format': self.format, 'description': self.description, 'pronom_id': self.pronom_id}


# ########### ID TOOLS ############

class IDCommand(VersionedModel, models.Model):
    """ Command to run an IDToolConfig and parse the output.

    IDCommand runs 'script' (which runs an IDTool with a specific IDToolConfig)
    and parses the output. """
    uuid = UUIDField(editable=False, unique=True, version=4, help_text=_("Unique identifier"))
    description = models.CharField(_('description'), max_length=256, help_text=_("Name to identify script"))
    CONFIG_CHOICES = (
        ('PUID', _('PUID')),
        ('MIME', _('MIME type')),
        ('ext', _('File extension'))
    )
    config = models.CharField(_('configuration'), max_length=4, choices=CONFIG_CHOICES)

    script = models.TextField(_('script'), help_text=_("Script to be executed."))
    SCRIPT_TYPE_CHOICES = (
        ('bashScript', _('Bash script')),
        ('pythonScript', _('Python script')),
        ('command', _('Command line')),
        ('as_is', _('No shebang needed'))
    )
    script_type = models.CharField(_('script type'), max_length=16, choices=SCRIPT_TYPE_CHOICES)
    tool = models.ForeignKey('IDTool', to_field='uuid', null=True, blank=True, verbose_name=_('the related tool'))

    class Meta:
        verbose_name = _("Format identification command")
        ordering = ['description']

    def __unicode__(self):
        return _("%(tool)s %(config)s runs %(command)s") % {
            'tool': self.tool,
            'config': self.get_config_display(),
            'command': self.description,
        }

    def save(self, *args, **kwargs):
        super(IDCommand, self).save(*args, **kwargs)
        # If part of archivematica, create user choice replacement dict
        try:
            from main.models import MicroServiceChoiceReplacementDic
        except ImportError:
            return
        # Remove existing object
        MicroServiceChoiceReplacementDic.objects.filter(replacementdic__contains=self.uuid).delete()
        if self.enabled:
            # Add replacement to MicroServiceChoiceReplacementDic
            at_link_transfer = 'f09847c2-ee51-429a-9478-a860477f6b8d'
            at_link_ingest = '7a024896-c4f7-4808-a240-44c87c762bc5'
            at_link_submissiondocs = '087d27be-c719-47d8-9bbb-9a7d8b609c44'
            # {"%IDCommand%": self.command.uuid}
            replace = '{{"%IDCommand%":"{0}"}}'.format(self.uuid)
            for link in (at_link_transfer, at_link_ingest, at_link_submissiondocs):
                MicroServiceChoiceReplacementDic.objects.create(
                    id=str(uuid.uuid4()),
                    choiceavailableatlink_id=link,
                    description=self.description,
                    replacementdic=replace,
                )


class IDRule(VersionedModel, models.Model):
    """ Mapping between an IDCommand output and a FormatVersion. """
    uuid = UUIDField(editable=False, unique=True, version=4, help_text=_("Unique identifier"))
    command = models.ForeignKey('IDCommand', to_field='uuid', verbose_name=_('the related command'))
    format = models.ForeignKey('FormatVersion', to_field='uuid', verbose_name=_('the related format'))
    # Output from IDToolConfig.command to match on that gives the format
    command_output = models.TextField(_('command output'))

    class Meta:
        verbose_name = _("Format identification rule")

    def validate_unique(self, *args, **kwargs):
        super(IDRule, self).validate_unique(*args, **kwargs)

        qs = self.__class__._default_manager.filter(
            command=self.command,
            command_output=self.command_output,
            enabled=1
        )

        if not self._state.adding and self.pk is not None:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            raise ValidationError({
                NON_FIELD_ERRORS: [_('Unable to save, a rule with this output already exists for this command.')]
            })

    def __unicode__(self):
        return _('Format identification rule %(uuid)s') % {'uuid': self.uuid}

    def long_name(self):
        return _('%(command)s with %(output)s is %(format)s') % {
            'command': self.command,
            'output': self.command_output,
            'format': self.format,
        }


class IDTool(models.Model):
    """ Tool used to identify formats.  Eg. DROID """
    uuid = UUIDField(editable=False, unique=True, version=4, help_text=_("Unique identifier"))
    description = models.CharField(_('description'), max_length=256, help_text=_("Name of tool"))
    version = models.CharField(_('version'), max_length=64)
    enabled = models.BooleanField(_('enabled'), default=True)
    slug = AutoSlugField(_('slug'), populate_from='_slug', always_update=True, unique=True)

    class Meta:
        verbose_name = _("Format identification tool")

    objects = models.Manager()
    active = Enabled()

    def __unicode__(self):
        return _("%(description)s version %(version)s") % {'description': self.description, 'version': self.version}

    def _slug(self):
        """ Returns string to be slugified. """
        src = '{} {}'.format(self.description, self.version)
        encoded = src.encode('utf-8')[:self._meta.get_field('slug').max_length]
        return encoded.decode('utf-8', 'ignore')


# ########### NORMALIZATION ############

class FPRule(VersionedModel, models.Model):
    uuid = UUIDField(editable=False, unique=True, version=4, help_text=_("Unique identifier"))

    ACCESS = 'access'
    CHARACTERIZATION = 'characterization'
    EXTRACTION = 'extract'
    PRESERVATION = 'preservation'
    THUMBNAIL = 'thumbnail'
    TRANSCRIPTION = 'transcription'
    VALIDATION = 'validation'
    POLICY = 'policy_check'
    DEFAULT_ACCESS = 'default_access'
    DEFAULT_CHARACTERIZATION = 'default_characterization'
    DEFAULT_THUMBNAIL = 'default_thumbnail'
    USAGES = (ACCESS, CHARACTERIZATION, EXTRACTION, PRESERVATION, THUMBNAIL,
              TRANSCRIPTION, VALIDATION, POLICY, DEFAULT_ACCESS,
              DEFAULT_CHARACTERIZATION, DEFAULT_THUMBNAIL)
    DISPLAY_CHOICES = (
        (ACCESS, _('Access')),
        (CHARACTERIZATION, _('Characterization')),
        (EXTRACTION, _('Extract')),
        (PRESERVATION, _('Preservation')),
        (THUMBNAIL, _('Thumbnail')),
        (TRANSCRIPTION, _('Transcription')),
        (VALIDATION, _('Validation')),
        (POLICY, _('Validation against a policy')),
    )
    HIDDEN_CHOICES = (
        (DEFAULT_ACCESS, _('Default access')),
        (DEFAULT_CHARACTERIZATION, _('Default characterization')),
        (DEFAULT_THUMBNAIL, _('Default thumbnail')),
    )
    # There are three categories of Normalization we want to group together,
    # and 'extraction' has a different FPRule name.
    USAGE_MAP = {
        'normalization': (DEFAULT_ACCESS, ACCESS, PRESERVATION, THUMBNAIL),
        'characterization': (CHARACTERIZATION, DEFAULT_CHARACTERIZATION),
        'extraction': (EXTRACTION,),
        'validation': (VALIDATION, POLICY)
    }
    PURPOSE_CHOICES = DISPLAY_CHOICES + HIDDEN_CHOICES
    purpose = models.CharField(_('purpose'), max_length=32, choices=PURPOSE_CHOICES)
    command = models.ForeignKey('FPCommand', to_field='uuid', verbose_name=_('the related command'))
    format = models.ForeignKey('FormatVersion', to_field='uuid', verbose_name=_('the related format'))

    count_attempts = models.IntegerField(_('count attempts'), default=0)
    count_okay = models.IntegerField(_('count okay'), default=0)
    count_not_okay = models.IntegerField(_('count not okay'), default=0)

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

    def __unicode__(self):
        return _('Format policy rule %(uuid)s') % {'uuid': self.uuid}

    def long_name(self):
        return _('Normalize %(format)s for %(purpose)s via %(command)s') % {
            'format': self.format,
            'purpose': self.get_purpose_display(),
            'command': self.command,
        }


class FPCommand(VersionedModel, models.Model):
    uuid = UUIDField(editable=False, unique=True, version=4, help_text=_("Unique identifier"))
    # ManyToManyField may not be the best choice here
    tool = models.ForeignKey('FPTool', to_field='uuid', null=True, verbose_name=_('the related tool'))
    description = models.CharField(_('description'), max_length=256)
    command = models.TextField(_('command'))
    SCRIPT_TYPE_CHOICES = (
        ('bashScript', _('Bash script')),
        ('pythonScript', _('Python script')),
        ('command', _('Command line')),
        ('as_is', _('No shebang needed'))
    )
    script_type = models.CharField(_('script type'), max_length=16, choices=SCRIPT_TYPE_CHOICES)
    output_location = models.TextField(_('output location'), null=True, blank=True)
    output_format = models.ForeignKey('FormatVersion', to_field='uuid', null=True, blank=True, verbose_name=_('the related output format'))
    COMMAND_USAGE_CHOICES = (
        ('characterization', _('Characterization')),
        ('event_detail', _('Event Detail')),
        ('extraction', _('Extraction')),
        ('normalization', _('Normalization')),
        ('transcription', _('Transcription')),
        ('validation', _('Validation')),
        ('verification', _('Verification')),
    )
    command_usage = models.CharField(_('command usage'), max_length=16, choices=COMMAND_USAGE_CHOICES)
    verification_command = models.ForeignKey('self', to_field='uuid', null=True, blank=True, related_name='+', verbose_name=_('the related verification command'))
    event_detail_command = models.ForeignKey('self', to_field='uuid', null=True, blank=True, related_name='+', verbose_name=_('the related event detail command'))

    class Meta:
        verbose_name = _("Format policy command")
        ordering = ['description']

    def __unicode__(self):
        return u"{}".format(self.description)


class FPTool(models.Model):
    """ Tool used to perform normalization.  Eg. convert, ffmpeg, ps2pdf. """
    uuid = UUIDField(editable=False, unique=True, version=4, help_text=_("Unique identifier"))
    description = models.CharField(_('description'), max_length=256, help_text=_("Name of tool"))
    version = models.CharField(_('version'), max_length=64)
    enabled = models.BooleanField(_('enabled'), default=True)
    slug = AutoSlugField(_('slug'), populate_from='_slug', unique=True)
    # Many to many field is on FPCommand

    class Meta:
        verbose_name = _("Normalization tool")

    def __unicode__(self):
        return _("%(description)s version %(version)s") % {'description': self.description, 'version': self.version}

    def _slug(self):
        """ Returns string to be slugified. """
        src = '{} {}'.format(self.description, self.version)
        encoded = src.encode('utf-8')[:self._meta.get_field('slug').max_length]
        return encoded.decode('utf-8', 'ignore')


# ########################### API V1 & V2 MODELS #############################

class Agent(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True, db_column='uuid')
    agentIdentifierType = models.CharField(_('agent identifier type'), max_length=100)
    agentIdentifierValue = models.CharField(_('agent identifier value'), max_length=100)
    agentName = models.CharField(_('agent name'), max_length=100)
    agentType = models.CharField(_('agent type'), max_length=100)
    clientIP = models.CharField(_('client IP address'), max_length=100)

    class Meta:
        db_table = u'Agent'


# ############################# API V1 MODELS ###############################

class CommandType(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True, db_column='pk')
    replaces = models.CharField(_('replaces'), null=True, max_length=36, db_column='replaces')
    type = models.TextField(_('type'), db_column='type')
    lastmodified = models.DateTimeField(_('last modified'), db_column='lastModified')
    enabled = models.IntegerField(_('enabled'), null=True, db_column='enabled', default=1)

    class Meta:
        db_table = u'CommandType'


class Command(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True, db_column='pk')
    # commandType = models.ForeignKey(CommandType, db_column='commandType')
    commandUsage = models.CharField(_('command usage'), max_length=15)
    commandType = models.CharField(_('command type'), max_length=36)
    # verificationCommand = models.ForeignKey('self', null=True, related_name='+', db_column='verificationCommand')
    verificationCommand = models.CharField(_('verification command'), max_length=36, null=True)
    # eventDetailCommand = models.ForeignKey('self', null=True, related_name='+', db_column='eventDetailCommand')
    eventDetailCommand = models.CharField(_('event detail command'), max_length=36, null=True)
    # supportedBy = models.ForeignKey('self', null=True, related_name='+', db_column='supportedBy')
    supportedBy = models.CharField(_('supported by'), max_length=36, null=True, db_column='supportedBy')
    command = models.TextField(_('command'), db_column='command')
    outputLocation = models.TextField(_('output location'), db_column='outputLocation', null=True)
    description = models.TextField(_('description'), db_column='description')
    outputFileFormat = models.TextField(_('output file format'), db_column='outputFileFormat', null=True)
    # replaces = models.ForeignKey('self', related_name='+', db_column='replaces', null=True)
    replaces = models.CharField(_('replaces'), max_length=36, null=True, db_column='replaces')
    lastmodified = models.DateTimeField(_('last modified'), db_column='lastModified', null=True)
    enabled = models.IntegerField(_('enabled'), null=True, db_column='enabled', default=1)

    class Meta:
        db_table = u'Command'


class CommandsSupportedBy(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True, db_column='pk')
    description = models.TextField(_('description'), null=True, db_column='description')
    # replaces = models.ForeignKey(Command)
    replaces = models.CharField(_('replaces'), max_length=36, null=True, db_column='replaces')
    lastmodified = models.DateTimeField(_('last modified'), db_column='lastModified')
    enabled = models.IntegerField(_('enabled'), null=True, db_column='enabled', default=1)

    class Meta:
        db_table = u'CommandsSupportedBy'

    def __unicode__(self):
        return u'{}'.format(self.description)


class FileIDType(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True, db_column='pk')
    description = models.TextField(_('description'), null=True, db_column='description')
    replaces = models.CharField(_('replaces'), null=True, max_length=36, db_column='replaces')
    lastmodified = models.DateTimeField(_('last modified'), db_column='lastModified')
    enabled = models.IntegerField(_('enabled'), null=True, db_column='enabled', default=1)

    class Meta:
        db_table = u'FileIDType'


class FileID(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True, db_column='pk')
    description = models.TextField(_('description'), db_column='description')
    validpreservationformat = models.IntegerField(_('valid preservation format'), null=True, db_column='validPreservationFormat', default=0)
    validaccessformat = models.IntegerField(_('valid access format'), null=True, db_column='validAccessFormat', default=0)
    # fileidtype = models.ForeignKey(FileIDType, null=True, blank=True, default = None)
    fileidtype = models.CharField(_('file ID type'), max_length=36, null=True, db_column='fileidtype_id')
    replaces = models.CharField(_('replaces'), null=True, max_length=36, db_column='replaces')
    lastmodified = models.DateTimeField(_('last modified'), db_column='lastModified')
    enabled = models.IntegerField(_('enabled'), null=True, db_column='enabled', default=1)

    # V2 API
    format = models.ForeignKey('FormatVersion', to_field='uuid', null=True, verbose_name=_('the related format'))

    class Meta:
        db_table = u'FileID'


class CommandClassification(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True, db_column='pk')
    classification = models.TextField(_('classification'), null=True, db_column='classification')
    replaces = models.CharField(_('replaces'), null=True, max_length=36, db_column='replaces')
    lastmodified = models.DateTimeField(_('last modified'), db_column='lastModified')
    enabled = models.IntegerField(_('enabled'), null=True, db_column='enabled', default=1)

    class Meta:
        db_table = u'CommandClassification'


class CommandRelationship(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True, db_column='pk')
    # commandClassification = models.ForeignKey(CommandClassification, db_column='commandClassification')
    commandClassification = models.CharField(_('command clasification'), max_length=36)
    # command = models.ForeignKey(Command, null=True, db_column='command')
    # fileID = models.ForeignKey(FileID, db_column='fileID')
    # replaces = models.CharField(null=True, max_length=36, db_column='replaces')
    command = models.CharField(_('command'), max_length=36, null=True)
    fileID = models.CharField(_('file ID'), max_length=36, null=True)
    replaces = models.CharField(_('replaces'), max_length=36, null=True)
    lastmodified = models.DateTimeField(_('last modified'), db_column='lastModified')
    enabled = models.IntegerField(_('enabled'), null=True, db_column='enabled', default=1)

    class Meta:
        db_table = u'CommandRelationship'


class FileIDsBySingleID(models.Model):
    uuid = models.CharField(max_length=36, primary_key=True, db_column='pk')
    # fileID = models.ForeignKey(FileID, db_column='fileID')
    fileID = models.CharField(_('file ID'), max_length=36, null=True)
    id = models.TextField(db_column='id')
    tool = models.TextField(_('tool'), db_column='tool')
    toolVersion = models.TextField(_('tool version'), db_column='toolVersion', null=True)
    replaces = models.CharField(_('replaces'), null=True, max_length=36, db_column='replaces')
    lastmodified = models.DateTimeField(_('last modified'), db_column='lastModified')
    enabled = models.IntegerField(_('enabled'), null=True, db_column='enabled', default=1)

    class Meta:
        db_table = u'FileIDsBySingleID'
