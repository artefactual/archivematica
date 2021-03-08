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
from __future__ import absolute_import, division

import os
from lxml import etree

from django import forms
from django.conf import settings
from django.forms.widgets import TextInput, Select
from django.utils.translation import ugettext_lazy as _

from contrib.mcp.client import MCPClient
from components import helpers
from installer.forms import site_url_field, load_site_url
from main.models import Agent, TaxonomyTerm

import storageService as storage_service


class AgentForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = ("identifiervalue", "name", "agenttype")
        widgets = {
            "identifiervalue": TextInput(attrs=settings.INPUT_ATTRS),
            "name": TextInput(attrs=settings.INPUT_ATTRS),
            "agenttype": TextInput(attrs=settings.INPUT_ATTRS),
        }


class SettingsForm(forms.Form):
    """Base class form to save settings to DashboardSettings."""

    def save(self, *args, **kwargs):
        """Save all the form fields to the DashboardSettings table."""
        for key in self.cleaned_data:
            # Save the value
            helpers.set_setting(key, self.cleaned_data[key])


class HandleForm(SettingsForm):
    """Form class for configuring client access to a handle server endpoint.
    This configures PIDs/handles to be requested for units (DIPs), files or
    directories, as well as the resolution of URLs based on those PIDs, i.e.,
    PURLs, to specified URLs.
    Note: the attributes of this form are (and must remain) identical to
    archivematicaCommon/bindpid::CFGABLE_PARAMS.
    """

    pid_web_service_endpoint = forms.URLField(
        required=True,
        label=_("Web service endpoint"),
        help_text=_("The URL for (POST) requests to create and resolve PIDs."),
    )

    pid_web_service_key = forms.CharField(
        required=True,
        label=_("Web service key"),
        help_text=_(
            "Web service key needed for authentication to make"
            " PID-binding requests to the PID web service endpoint."
        ),
    )

    naming_authority = forms.CharField(
        required=True,
        label=_("Naming authority"),
        help_text=_("Handle naming authority (e.g., 12345)"),
    )

    handle_resolver_url = forms.URLField(
        required=True,
        label=_("Resolver URL"),
        help_text=_(
            "The URL to append generated PIDs to in order to create"
            " (potentially qualified) PURLs (persistent URLs) that"
            " resolve to the applicable resolve URL. Note the second"
            ' "r" in "resolver"!'
        ),
    )

    AIP_PID_SOURCE_CHOICES = (("uuid", "UUID"), ("accession_no", "Accession number"))

    handle_archive_pid_source = forms.ChoiceField(
        choices=AIP_PID_SOURCE_CHOICES,
        label=_("AIP PID source"),
        help_text=_(
            "The source of the AIP's persistent identifier. The UUID "
            "of the AIP is the default since it is virtually guaranteed "
            "to be unique. However, the accession number of the "
            "transfer may be used, assuming the user can guarantee a "
            "1-to-1 relationship between the transfer and the AIP."
        ),
    )
    # If this is set to "accession number" and Archivematica cannot find a
    # unique accession number for the AIP (because it references/ was
    # constructed from multiple Transfers), then the UUID is used as the
    # fallback; see the bind_pids client script for details.

    pid_request_verify_certs = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Verify SSL certificates"),
        help_text=_("Verify SSL certificates when making requests to bind PIDs."),
    )

    resolve_url_template_archive = forms.CharField(
        required=True,
        label=_("Archive resolve URL template"),
        help_text=_(
            "Template (Django or Jinja2) for the URL that a unit's"
            ' PURL should resolve to. Has access to "pid" and'
            ' "naming_authority" variables.'
        ),
    )

    resolve_url_template_mets = forms.CharField(
        required=False,
        label=_("METS resolve URL template"),
        help_text=_(
            "Template (Django or Jinja2) for the URL that a unit's"
            ' PURL with the "mets" qualifier should resolve to. Has'
            ' access to "pid" and "naming_authority" variables.'
        ),
    )

    resolve_url_template_file = forms.CharField(
        required=True,
        label=_("File resolve URL template"),
        help_text=_(
            "Template (Django or Jinja2) for the URL that a file's"
            ' PURL should resolve to. Has access to "pid" and'
            ' "naming_authority" variables.'
        ),
    )

    resolve_url_template_file_access = forms.CharField(
        required=False,
        label=_("Access derivative resolve URL template"),
        help_text=_(
            "Template (Django or Jinja2) for the URL that a file's"
            ' PURL with the "access" qualifier should resolve to. Has'
            ' access to "pid" and "naming_authority" variables.'
        ),
    )

    resolve_url_template_file_preservation = forms.CharField(
        required=False,
        label=_("Preservation derivative resolve URL template"),
        help_text=_(
            "Template (Django or Jinja2) for the URL that a file's"
            ' PURL with the "preservation" qualifier should resolve'
            ' to. Has access to "pid" and "naming_authority"'
            " variables."
        ),
    )

    resolve_url_template_file_original = forms.CharField(
        required=False,
        label=_("Original file resolve URL template"),
        help_text=_(
            "Template (Django or Jinja2) for the URL that a file's"
            ' PURL with the "original" qualifier should resolve to. Has'
            ' access to "pid" and "naming_authority" variables.'
        ),
    )

    pid_request_body_template = forms.CharField(
        required=False,
        widget=forms.Textarea,
        label=_("PID/handle request request body template"),
        help_text=_(
            "Template (Django or Jinja2) that constructs the HTTP"
            " request body using the rendered URL templates above. Has"
            ' access to the following variables: "pid",'
            ' "naming_authority", "base_resolve_url", and'
            ' "qualified_resolve_urls", the last of which is a list of'
            ' dicts with "url" and "qualifier" keys.'
        ),
    )


class GeneralSettingsForm(SettingsForm):
    site_url = site_url_field

    def __init__(self, *args, **kwargs):
        super(GeneralSettingsForm, self).__init__(*args, **kwargs)
        load_site_url(self.fields["site_url"])


class StorageSettingsForm(SettingsForm):
    class StripCharField(forms.CharField):
        """
        Strip the value of leading and trailing whitespace.

        This won't be needed in Django 1.9, see
        https://docs.djangoproject.com/en/1.9/ref/forms/fields/#django.forms.CharField.strip.
        """

        def to_python(self, value):
            return super(forms.CharField, self).to_python(value).strip()

    storage_service_url = forms.CharField(
        label=_("Storage Service URL"),
        help_text=_(
            "Full URL of the storage service. E.g. https://192.168.168.192:8000"
        ),
    )
    storage_service_user = forms.CharField(
        label=_("Storage Service User"),
        help_text=_("User in the storage service to authenticate as. E.g. test"),
    )
    storage_service_apikey = StripCharField(
        label=_("API key"),
        help_text=_(
            "API key of the storage service user. E.g. 45f7684483044809b2de045ba59dc876b11b9810"
        ),
    )
    storage_service_use_default_config = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Use default configuration"),
        help_text=_(
            "You have to manually set up a custom configuration if the default configuration is not selected."
        ),
    )


class ChecksumSettingsForm(SettingsForm):
    CHOICES = (
        ("md5", "MD5"),
        ("sha1", "SHA-1"),
        ("sha256", "SHA-256"),
        ("sha512", "SHA-512"),
    )
    checksum_type = forms.ChoiceField(choices=CHOICES, label=_("Select algorithm"))


class TaxonomyTermForm(forms.ModelForm):
    class Meta:
        model = TaxonomyTerm
        fields = ("taxonomy", "term")
        widgets = {"term": TextInput(attrs=settings.INPUT_ATTRS)}


class ProcessingConfigurationForm(forms.Form):
    """
    Build processing configuration form bounded to a processingMCP document.

    Every processing field in this form requires the following
    properties: type, name, label. In addition, these are some other
    constraints based on the type:
    """

    EMPTY_OPTION_NAME = _("None")
    EMPTY_CHOICES = [(None, EMPTY_OPTION_NAME)]
    DEFAULT_FIELD_OPTS = {"required": False, "initial": None}

    # This extends the fields defined in the processing_config module.
    # Temporary solution until workflow data can be translated.
    LABELS = {
        "bd899573-694e-4d33-8c9b-df0af802437d": _("Assign UUIDs to directories"),
        "56eebd45-5600-4768-a8c2-ec0114555a3d": _("Generate transfer structure report"),
        "f09847c2-ee51-429a-9478-a860477f6b8d": _(
            "Perform file format identification (Transfer)"
        ),
        "dec97e3c-5598-4b99-b26e-f87a435a6b7f": _("Extract packages"),
        "f19926dd-8fb5-4c79-8ade-c83f61f55b40": _("Delete packages after extraction"),
        "70fc7040-d4fb-4d19-a0e6-792387ca1006": _("Perform policy checks on originals"),
        "accea2bf-ba74-4a3a-bb97-614775c74459": _("Examine contents"),
        "bb194013-597c-4e4a-8493-b36d190f8717": _("Create SIP(s)"),
        "7a024896-c4f7-4808-a240-44c87c762bc5": _(
            "Perform file format identification (Ingest)"
        ),
        "cb8e5706-e73f-472f-ad9b-d1236af8095f": _("Normalize"),
        "de909a42-c5b5-46e1-9985-c031b50e9d30": _("Approve normalization"),
        "498f7a6d-1b8c-431a-aa5d-83f14f3c5e65": _("Generate thumbnails"),
        "153c5f41-3cfb-47ba-9150-2dd44ebc27df": _(
            "Perform policy checks on preservation derivatives"
        ),
        "8ce07e94-6130-4987-96f0-2399ad45c5c2": _(
            "Perform policy checks on access derivatives"
        ),
        "a2ba5278-459a-4638-92d9-38eb1588717d": _("Bind PIDs"),
        "d0dfa5fc-e3c2-4638-9eda-f96eea1070e0": _("Document empty directories"),
        "eeb23509-57e2-4529-8857-9d62525db048": _("Reminder: add metadata if desired"),
        "82ee9ad2-2c74-4c7c-853e-e4eaf68fc8b6": _("Transcribe files (OCR)"),
        "087d27be-c719-47d8-9bbb-9a7d8b609c44": _(
            "Perform file format identification (Submission documentation & metadata)"
        ),
        "01d64f58-8295-4b7b-9cab-8f1b153a504f": _("Select compression algorithm"),
        "01c651cb-c174-4ba4-b985-1d87a44d6754": _("Select compression level"),
        "2d32235c-02d4-4686-88a6-96f4d6c7b1c3": _("Store AIP"),
        "b320ce81-9982-408a-9502-097d0daa48fa": _("Store AIP location"),
        "92879a29-45bf-4f0b-ac43-e64474f0f2f9": _("Upload DIP"),
        "5e58066d-e113-4383-b20b-f301ed4d751c": _("Store DIP"),
        "cd844b6e-ab3c-4bc6-b34f-7103f88715de": _("Store DIP location"),
    }

    name = forms.RegexField(
        max_length=16,
        regex=r"^\w+$",
        required=True,
        error_messages={
            "invalid": _(
                "The name can contain only alphanumeric characters and the underscore character (_)."
            )
        },
    )
    name.widget.attrs["class"] = "form-control"

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(ProcessingConfigurationForm, self).__init__(*args, **kwargs)
        self._load_processing_config_fields(user)
        for choice_uuid, field in self.processing_fields.items():
            ftype = field["type"]
            opts = self.DEFAULT_FIELD_OPTS.copy()
            opts["label"] = field["label"]
            choices = opts["choices"] = list(self.EMPTY_CHOICES)
            if ftype == "boolean":
                if "yes_option" in field:
                    choices.append((field["yes_option"], _("Yes")))
                if "no_option" in field:
                    choices.append((field["no_option"], _("No")))
            elif ftype in ("chain_choice", "replace_dict"):
                choices.extend(field["options"])
            elif ftype == "storage_service":
                choices.append(
                    (
                        "/api/v2/location/default/{}/".format(field["purpose"]),
                        _("Default location"),
                    )
                )
                for loc in get_storage_locations(purpose=field["purpose"]):
                    label = loc["description"]
                    if not label:
                        label = loc["relative_path"]
                    choices.append((loc["resource_uri"], label))
            self.fields[choice_uuid] = forms.ChoiceField(
                widget=Select(attrs={"class": "form-control"}), **opts
            )

    def _load_processing_config_fields(self, user):
        client = MCPClient(user)
        self.processing_fields = client.get_processing_config_fields()
        for choice_uuid, field in self.processing_fields.items():
            field["label"] = self.LABELS[choice_uuid]

    def load_config(self, name):
        """
        Bound the choices found in the XML document to the form fields.
        """
        self.fields["name"].initial = name
        self.fields["name"].widget.attrs["readonly"] = "readonly"
        config_path = os.path.join(
            helpers.processing_config_path(), "{}ProcessingMCP.xml".format(name)
        )
        root = etree.parse(config_path)
        for choice in root.findall(".//preconfiguredChoice"):
            applies_to = choice.findtext("appliesTo")
            go_to_chain = choice.findtext("goToChain")
            fprops = self.processing_fields.get(applies_to)
            field = self.fields.get(applies_to)
            if fprops is None or go_to_chain is None or field is None:
                continue
            field.initial = go_to_chain

    def save_config(self):
        """
        Encode the configuration to XML and write it to disk.
        """
        name = self.cleaned_data["name"]
        del self.cleaned_data["name"]
        config_path = os.path.join(
            helpers.processing_config_path(), "{}ProcessingMCP.xml".format(name)
        )
        config = PreconfiguredChoices()
        for choice_uuid, value in self.cleaned_data.items():
            fprops = self.processing_fields.get(choice_uuid)
            if fprops is None or value is None:
                continue
            field = self.fields.get(choice_uuid)
            if field is None:
                continue
            if isinstance(field, forms.ChoiceField):
                if not value:  # Ignore empty string!
                    continue
            if fprops["type"] == "days":
                if value == 0:
                    continue
                delay = str(float(value) * (24 * 60 * 60))
                config.add_choice(
                    choice_uuid,
                    fprops["chain"],
                    delay_duration=delay,
                    comment=fprops["label"],
                )
            elif fprops["type"] == "chain_choice" and "duplicates" in fprops:
                # If we have more than one chain (duplicates) then we need to
                # add them all, e.g.::
                #
                #    <!-- Normalize (match 1 for "Normalize for access") -->
                #    <preconfiguredChoice>
                #      <appliesTo>...</appliesTo>
                #      <goToChain>...</goToChain>
                #    </preconfiguredChoice>
                #    <!-- Normalize (match 2 for "Normalize for access") -->
                #    <preconfiguredChoice>
                #      <appliesTo>...</appliesTo>
                #      <goToChain>...</goToChain>
                #    </preconfiguredChoice>
                #
                # Otherwise, when `KeyError` is raised, add single entry.
                try:
                    desc, matches = fprops["duplicates"][value]
                except KeyError:
                    config.add_choice(choice_uuid, value, comment=fprops["label"])
                else:
                    for i, match in enumerate(matches):
                        comment = '{} (match {} for "{}")'.format(
                            fprops["label"], i + 1, desc
                        )
                        config.add_choice(match[0], match[1], comment=comment)
            else:
                config.add_choice(choice_uuid, value, comment=fprops["label"])
        config.save(config_path)


def get_storage_locations(purpose):
    try:
        dirs = storage_service.get_location(purpose=purpose)
        if len(dirs) == 0:
            raise Exception("Storage server improperly configured.")
    except Exception:
        dirs = []
    return dirs


class PreconfiguredChoices(object):
    """
    Encode processing configuration XML documents and optionally write to disk.
    """

    def __init__(self):
        self.xml = etree.Element("processingMCP")
        self.choices = etree.SubElement(self.xml, "preconfiguredChoices")

    def add_choice(
        self, applies_to_text, go_to_chain_text, delay_duration=None, comment=None
    ):
        if comment is not None:
            comment = etree.Comment(" {} ".format(comment))
            self.choices.append(comment)
        choice = etree.SubElement(self.choices, "preconfiguredChoice")
        etree.SubElement(choice, "appliesTo").text = applies_to_text
        etree.SubElement(choice, "goToChain").text = go_to_chain_text
        if delay_duration is not None:
            etree.SubElement(
                choice, "delay", {"unitCtime": "yes"}
            ).text = delay_duration

    def save(self, config_path):
        with open(config_path, "w") as f:
            f.write(etree.tostring(self.xml, pretty_print=True, encoding="unicode"))
