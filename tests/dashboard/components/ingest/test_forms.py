import pytest

from archivematica.dashboard.components.ingest.forms import AICDublinCoreMetadataForm
from archivematica.dashboard.components.ingest.forms import DublinCoreMetadataForm
from archivematica.dashboard.main import models


def test_dublin_core_form_applies_expected_widget_attrs() -> None:
    form = DublinCoreMetadataForm()

    assert form.fields["title"].widget.attrs["class"] == "span11"
    assert form.fields["description"].widget.attrs["rows"] == "4"
    assert form.fields["description"].widget.attrs["class"] == "span11"

    # Widget attrs should be copied from settings, not referenced directly.
    assert form.fields["title"].widget.attrs is not form.fields["creator"].widget.attrs


def test_dublin_core_form_composes_help_text_for_contextual_and_model_help() -> None:
    form = DublinCoreMetadataForm()

    date_help = str(form.fields["date"].help_text)
    assert "A point or period of time associated" in date_help
    assert "ISO15836" in date_help
    assert "Use ISO 8601 (YYYY-MM-DD or YYYY-MM-DD/YYYY-MM-DD)" in date_help
    assert "<br />" in date_help

    is_part_of_help = str(form.fields["is_part_of"].help_text)
    assert is_part_of_help == "Optional: leave blank if unsure"


def test_dublin_core_form_uses_single_i18n_string_for_format_link() -> None:
    form = DublinCoreMetadataForm()

    format_help = str(form.fields["format"].help_text)
    assert "Internet Media Types (MIME) registry" in format_help
    assert '<a href="http://www.iana.org/assignments/media-types/"' in format_help
    assert "{mime_link}" not in format_help
    assert "{link_start}" not in format_help
    assert "{link_end}" not in format_help


def test_dublin_core_form_clean_is_part_of_prefixes_aic() -> None:
    form = DublinCoreMetadataForm(data={"is_part_of": "1234"})

    assert form.is_valid()
    assert form.cleaned_data["is_part_of"] == "AIC#1234"


def test_dublin_core_form_clean_is_part_of_does_not_double_prefix() -> None:
    form = DublinCoreMetadataForm(data={"is_part_of": "AIC#1234"})

    assert form.is_valid()
    assert form.cleaned_data["is_part_of"] == "AIC#1234"


def test_aic_dublin_core_form_requires_identifier() -> None:
    form = AICDublinCoreMetadataForm(data={"title": "My title"})

    assert not form.is_valid()
    assert form.errors["identifier"] == ["This field is required."]


def test_aic_dublin_core_form_clean_identifier_prefixes_aic() -> None:
    form = AICDublinCoreMetadataForm(data={"identifier": "9999"})

    assert form.is_valid()
    assert form.cleaned_data["identifier"] == "AIC#9999"


def test_aic_dublin_core_form_clean_identifier_does_not_double_prefix() -> None:
    form = AICDublinCoreMetadataForm(data={"identifier": "AIC#9999"})

    assert form.is_valid()
    assert form.cleaned_data["identifier"] == "AIC#9999"


@pytest.mark.django_db
def test_dublin_core_form_save_updates_reingest_status(
    metadata_applies_to_types,
) -> None:
    dublin_core = models.DublinCore.objects.create(
        metadataappliestotype=metadata_applies_to_types["sip"],
        status=models.METADATA_STATUS_REINGEST,
    )

    form = DublinCoreMetadataForm(data={"title": "Updated"}, instance=dublin_core)

    assert form.is_valid(), form.errors
    saved = form.save()

    assert saved.status == models.METADATA_STATUS_UPDATED
    dublin_core.refresh_from_db()
    assert dublin_core.status == models.METADATA_STATUS_UPDATED
