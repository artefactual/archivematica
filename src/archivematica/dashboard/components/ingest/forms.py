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
from django import forms
from django.conf import settings
from django.utils.html import format_html
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from archivematica.dashboard.main import models


class DublinCoreMetadataForm(forms.ModelForm):
    CONTEXTUAL_HELP_TEXT = {
        "title": _("A name given to the resource. ({iso15836})"),
        "creator": _(
            "An entity primarily responsible for making the resource. ({iso15836})"
        ),
        "subject": _("The topic of the resource. ({iso15836})"),
        "description": _("An account of the resource. ({iso15836})"),
        "publisher": _(
            "An entity responsible for making the resource available. ({iso15836})"
        ),
        "contributor": _(
            "An entity responsible for making contributions to the resource. "
            "({iso15836})"
        ),
        "date": _(
            "A point or period of time associated with an event in the "
            "lifecycle of the resource. ({iso15836})"
        ),
        "format": _(
            "The file format, physical medium, or dimensions of the resource. "
            "({iso15836}) Best practice is to use a controlled vocabulary "
            "such as the {mime_link}."
        ),
        "identifier": _(
            "An unambiguous reference to the resource within a given context. "
            "({iso15836})"
        ),
        "source": _(
            "A related resource from which the described resource is derived. "
            "({iso15836})"
        ),
        "relation": _("A related resource. ({iso15836})"),
        "language": _("A language of the resource. ({iso15836})"),
        "coverage": _(
            "The spatial or temporal topic of the resource, the spatial "
            "applicability of the resource, or the jurisdiction under which "
            "the resource is relevant. ({iso15836})"
        ),
        "rights": _(
            "Information about rights held in and over the resource. ({iso15836})"
        ),
    }

    class Meta:
        model = models.DublinCore
        fields = (
            "title",
            "is_part_of",
            "creator",
            "subject",
            "description",
            "publisher",
            "contributor",
            "date",
            "format",
            "identifier",
            "source",
            "relation",
            "language",
            "coverage",
            "rights",
        )
        widgets = {
            "title": forms.TextInput,
            "is_part_of": forms.TextInput,
            "creator": forms.TextInput,
            "subject": forms.TextInput,
            "publisher": forms.TextInput,
            "contributor": forms.TextInput,
            "date": forms.TextInput,
            "format": forms.TextInput,
            "identifier": forms.TextInput,
            "source": forms.TextInput,
            "relation": forms.TextInput,
            "language": forms.TextInput,
            "coverage": forms.TextInput,
        }

    aic_prefix = "AIC#"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        links = self._build_contextual_links()
        for field_name, field in self.fields.items():
            self._apply_widget_attrs(field)
            self._compose_help_text(field_name, field, links)

    def _build_contextual_links(self):
        return {
            "iso15836": mark_safe(
                '<a href="http://dublincore.org/documents/dces/" target="_blank">ISO15836</a>'
            ),
            "mime_link": format_html(
                '<a href="http://www.iana.org/assignments/media-types/" target="_blank">{}</a>',
                _("Internet Media Types (MIME) registry"),
            ),
        }

    def _apply_widget_attrs(self, field):
        if isinstance(field.widget, forms.widgets.TextInput):
            field.widget.attrs = settings.INPUT_ATTRS.copy()
        elif isinstance(field.widget, forms.widgets.Textarea):
            field.widget.attrs = settings.TEXTAREA_ATTRS.copy()

    def _compose_help_text(self, field_name, field, links):
        help_parts = []
        model_help_text = field.help_text
        contextual_help = self.CONTEXTUAL_HELP_TEXT.get(field_name)

        if contextual_help:
            help_parts.append(format_html(contextual_help, **links))

        if model_help_text:
            help_parts.append(model_help_text)

        if help_parts:
            field.help_text = format_html_join(
                mark_safe("<br />"),
                "{}",
                ((help_part,) for help_part in help_parts),
            )

    def save(self, *args, **kwargs):
        # Status is set to REINGEST when metadata is parsed into the DB. If it
        # is being saved through this form, then the user has modified it, and
        # it should not be written out to the METS file. Set the status to
        # UPDATED to indicate this.
        if self.instance.status == models.METADATA_STATUS_REINGEST:
            self.instance.status = models.METADATA_STATUS_UPDATED
        return super().save(*args, **kwargs)

    def clean_is_part_of(self):
        data = self.cleaned_data["is_part_of"]
        if data and not data.startswith(self.aic_prefix):
            data = self.aic_prefix + data
        return data


class AICDublinCoreMetadataForm(DublinCoreMetadataForm):
    class Meta:
        model = models.DublinCore
        fields = (
            "title",
            "is_part_of",
            "identifier",
            "creator",
            "subject",
            "description",
            "publisher",
            "contributor",
            "date",
            "format",
            "source",
            "relation",
            "language",
            "coverage",
            "rights",
        )
        widgets = DublinCoreMetadataForm.Meta.widgets.copy()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["identifier"].required = True

    def clean_identifier(self):
        data = self.cleaned_data["identifier"]
        if data and not data.startswith(self.aic_prefix):
            data = self.aic_prefix + data
        return data
