# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django import forms
from django.utils.translation import ugettext_lazy as _


PREMIS_CHOICES = [("yes", _("Yes")), ("no", _("No")), ("premis", _("Base on PREMIS"))]

EAD_ACTUATE_CHOICES = [
    ("none", _("None")),
    ("onLoad", _("onLoad")),
    ("other", _("other")),
    ("onRequest", _("onRequest")),
]

EAD_SHOW_CHOICES = [
    ("embed", _("Embed")),
    ("new", _("New")),
    ("none", _("None")),
    ("other", _("Other")),
    ("replace", _("Replace")),
]


class ArchivesSpaceConfigForm(forms.Form):
    base_url = forms.CharField(
        label=_("ArchivesSpace base URL"),
        help_text=_("Example: http://aspace.test.org:8089"),
    )
    user = forms.CharField(
        label=_("ArchivesSpace administrative user"), help_text=_("Example: admin")
    )
    passwd = forms.CharField(
        required=False,
        label=_("ArchivesSpace administrative user password"),
        help_text=_(
            "Password for user set above. Re-enter this password every time changes are made."
        ),
    )
    restrictions = forms.ChoiceField(
        choices=PREMIS_CHOICES, label=_("Restrictions apply"), initial="yes"
    )
    xlink_show = forms.ChoiceField(
        choices=EAD_SHOW_CHOICES, label=_("XLink Show"), initial="embed"
    )
    xlink_actuate = forms.ChoiceField(
        choices=EAD_ACTUATE_CHOICES, label=_("XLink Actuate"), initial="none"
    )
    object_type = forms.CharField(
        required=False,
        label=_("Object type"),
        help_text=_(
            "Optional, must come from ArchivesSpace controlled list. Example: sound_recording"
        ),
    )
    use_statement = forms.CharField(
        required=False,
        label=_("Use statement"),
        help_text=_(
            "Optional, but if present should come from ArchivesSpace controlled list. Example: image-master"
        ),
    )
    uri_prefix = forms.CharField(
        label=_("URL prefix"),
        help_text=_(
            "URL of DIP object server as you wish to appear in ArchivesSpace record. Example: http://example.com"
        ),
    )
    access_conditions = forms.CharField(
        required=False,
        label=_("Conditions governing access"),
        help_text=_("Populates Conditions governing access note"),
    )
    use_conditions = forms.CharField(
        required=False,
        label=_("Conditions governing use"),
        help_text=_("Populates Conditions governing use note"),
    )
    repository = forms.IntegerField(
        label=_("ArchivesSpace repository number"),
        help_text=_("Default for single repository installation is 2"),
        initial=2,
    )
    inherit_notes = forms.BooleanField(
        required=False,
        label=_("Inherit digital object notes from the parent component"),
        initial=False,
    )


class AtomConfigForm(forms.Form):
    url = forms.CharField(
        label=_("Upload URL"),
        help_text=_(
            "URL where the AtoM/Binder index.php frontend lives, SWORD services path will be appended."
        ),
    )
    email = forms.CharField(
        label=_("Login email"),
        help_text=_("E-mail account used to log into AtoM/Binder."),
    )
    password = forms.CharField(
        label=_("Login password"), help_text=_("Password used to log into AtoM/Binder.")
    )
    version = forms.ChoiceField(
        label=_("AtoM/Binder version"), choices=((1, "1.x"), (2, "2.x"))
    )
    rsync_target = forms.CharField(
        required=False,
        label=_("Rsync target"),
        help_text=_(
            "The DIP can be sent with Rsync to a remote host before is deposited in AtoM/Binder. This is the destination value passed to Rsync (see man 1 rsync). For example: foobar.com:~/dips/."
        ),
    )
    rsync_command = forms.CharField(
        required=False,
        label=_("Rsync command"),
        help_text=_(
            "If --rsync-target is used, you can use this argument to specify the remote shell manually. For example: ssh -p 22222 -l user."
        ),
    )
    debug = forms.ChoiceField(
        required=False,
        label=_("Debug mode"),
        help_text=_("Show additional details."),
        choices=((False, _("No")), (True, _("Yes"))),
        initial=False,
    )
    key = forms.CharField(
        required=False,
        label=_("REST API key"),
        help_text=_("Used in metadata-only DIP upload."),
    )
