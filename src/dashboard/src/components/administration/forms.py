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
    """Processing configuration form bound to the processing configuration
    fields dictated by MCPServer. Field values are populated after the contents
    of the processing configuration document.

    TODO: certain responsibilites should be handled by MCPServer, namely:
    (1) load pre-configured choices, and (2) additional RPC to save the
    configuration.
    """

    EMPTY_CHOICES = [(None, _("None"))]
    DEFAULT_FIELD_OPTS = {"required": False, "initial": None}

    LABELS = {
        # MCPServer does not extract messages.
        "virus_scanning": _("Scan for viruses?"),
        "select_format_id_tool_transfer": _(
            "Perform file format identification (Transfer)"
        ),
        "select_format_id_tool_ingest": _(
            "Perform file format identification (Ingest)"
        ),
        "select_format_id_tool_submissiondocs": _(
            "Perform file format identification (Submission documentation & metadata)"
        ),
    }

    NAME_MAX_LENGTH = 50
    NAME_URL_REGEX = r"(?P<name>\w{1,%d})" % NAME_MAX_LENGTH
    NAME_REGEX = r"^%s$" % NAME_URL_REGEX
    name = forms.RegexField(
        max_length=NAME_MAX_LENGTH,
        regex=NAME_REGEX,
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
        self.load_processing_config_fields(user)
        self.create_fields()

    def load_processing_config_fields(self, user):
        """Obtain processing fields and available choices from MCPServer."""
        client = MCPClient(user)
        self.processing_fields = client.get_processing_config_fields()

        # Override labels with translations in this form.
        for field in self.processing_fields:
            try:
                name = field["name"]
                field["label"] = self.LABELS[name]
            except KeyError:
                pass

    def create_fields(self):
        """Set up form fields with the server data."""
        for field in self.processing_fields:
            opts = self.DEFAULT_FIELD_OPTS.copy()
            opts["label"] = field["label"]
            opts["choices"] = self.EMPTY_CHOICES[:]
            for item in field["choices"]:
                opts["choices"].append((item["value"], item["label"]))
            self.fields[field["id"]] = forms.ChoiceField(
                widget=Select(attrs={"class": "form-control"}), **opts
            )

    def get_processing_config_path(self, name):
        return os.path.join(
            helpers.processing_config_path(), "{}ProcessingMCP.xml".format(name)
        )

    def load_config(self, name):
        """Populate form fields with the choices found in the XML document."""
        self.fields["name"].initial = name
        self.fields["name"].widget.attrs["readonly"] = "readonly"

        # Build a map with all pre-configuired choices for quick access.
        config_path = self.get_processing_config_path(name)
        root = etree.parse(config_path)
        choices = {
            choice.findtext("appliesTo"): choice.findtext("goToChain")
            for choice in root.findall(".//preconfiguredChoice")
        }

        for processing_field in self.processing_fields:
            link_id = processing_field["id"]
            form_field = self.fields[link_id]
            try:
                value = choices[link_id]
            except KeyError:
                continue
            form_field.initial = value

    def save_config(self):
        """Encode the configuration to XML and write it to disk."""
        # Capture the config name, then discard the form field.
        name = self.cleaned_data["name"]
        del self.cleaned_data["name"]

        config = PreconfiguredChoices()  # Configuration encoder.
        for field in self.processing_fields:
            link_id = field["id"]
            try:
                choice = self.cleaned_data[link_id]
            except KeyError:
                raise forms.ValidationError("Unknown processing field %s" % link_id)
            if not choice:
                continue  # Ignore when user chose None.
            matches = None
            for item in field["choices"]:
                if item["value"] == choice:
                    matches = item["applies_to"]
            if not matches:
                raise forms.ValidationError(
                    "Unknown value for processing field %s: %s", link_id, choice
                )
            for applies_to, go_to_chain, label in matches:
                comment = "{}: {}".format(self.fields[link_id].label, label)
                config.add_choice(applies_to, go_to_chain, comment)

        config.save(self.get_processing_config_path(name))


class PreconfiguredChoices(object):
    """
    Encode processing configuration XML documents and optionally write to disk.
    """

    def __init__(self):
        self.xml = etree.Element("processingMCP")
        self.choices = etree.SubElement(self.xml, "preconfiguredChoices")

    def add_choice(self, applies_to_text, go_to_chain_text, comment=None):
        if comment is not None:
            comment = etree.Comment(" {} ".format(comment))
            self.choices.append(comment)
        choice = etree.SubElement(self.choices, "preconfiguredChoice")
        etree.SubElement(choice, "appliesTo").text = applies_to_text
        etree.SubElement(choice, "goToChain").text = go_to_chain_text

    def save(self, config_path):
        with open(config_path, "w") as f:
            f.write(etree.tostring(self.xml, pretty_print=True, encoding="unicode"))
