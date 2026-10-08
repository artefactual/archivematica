import pytest
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from archivematica.dashboard.components.administration.views_dip_upload import (
    _AS_DICTNAME,
)
from archivematica.dashboard.components.administration.views_dip_upload import (
    _ATOM_DICTNAME,
)
from archivematica.dashboard.main.models import DashboardSetting

pytestmark = pytest.mark.usefixtures("dashboard_uuid")


# ArchivesSpace DIP upload configuration


def test_dips_as_get(admin_client: Client) -> None:
    response = admin_client.get(reverse("administration:dips_as"))

    assert response.request["PATH_INFO"] == "/administration/dips/as/"
    assertTemplateUsed(response, "administration/dips_as_edit.html")
    assert not response.context["form"].is_valid()


def test_dips_as_post_minimum_required(admin_client: Client) -> None:
    response = admin_client.post(
        reverse("administration:dips_as"),
        {
            "base_url": "http://aspace.test.org:8089",
            "user": "admin",
            "xlink_show": "embed",
            "xlink_actuate": "none",
            "uri_prefix": "http://example.com",
            "repository": 2,
            "restrictions": "yes",
        },
    )
    form = response.context["form"]
    config = DashboardSetting.objects.get_dict(_AS_DICTNAME)

    assert form.is_valid()
    assert not form.errors
    assert [
        (message.message, message.tags) for message in response.context["messages"]
    ] == [("Saved.", "info")]
    assert isinstance(config, dict)
    assert config["base_url"] == "http://aspace.test.org:8089"
    assert config["repository"] == "2"
    assert len(config) == len(form.fields)


def test_dips_as_post_missing_fields(admin_client: Client) -> None:
    response = admin_client.post(
        reverse("administration:dips_as"), {"base_url": "http://aspace.test.org:8089"}
    )
    form = response.context["form"]
    config = DashboardSetting.objects.get_dict(_AS_DICTNAME)

    assert not form.is_valid()
    assert form.errors == {
        "user": ["This field is required."],
        "xlink_show": ["This field is required."],
        "xlink_actuate": ["This field is required."],
        "uri_prefix": ["This field is required."],
        "repository": ["This field is required."],
        "restrictions": ["This field is required."],
    }
    assert isinstance(config, dict)


# AtoM DIP upload configuration


def test_dips_atom_get(admin_client: Client) -> None:
    response = admin_client.get(reverse("administration:dips_atom_index"))

    assert response.request["PATH_INFO"] == "/administration/dips/atom/"
    assertTemplateUsed(response, "administration/dips_atom_edit.html")
    assert not response.context["form"].is_valid()


def test_dips_atom_post_minimum_required(admin_client: Client) -> None:
    response = admin_client.post(
        reverse("administration:dips_atom_index"),
        {
            "url": "https://search.efimm.org",
            "email": "demo@example.com",
            "password": "demo",
            "version": 2,
        },
    )
    form = response.context["form"]
    config = DashboardSetting.objects.get_dict(_ATOM_DICTNAME)

    assert form.is_valid()
    assert not form.errors
    assert [
        (message.message, message.tags) for message in response.context["messages"]
    ] == [("Saved.", "info")]
    assert isinstance(config, dict)
    assert config["url"] == "https://search.efimm.org"
    assert config["email"] == "demo@example.com"
    assert config["password"] == "demo"
    assert config["version"] == "2"
    assert config["key"] == ""
    assert len(config) == len(form.fields)


def test_dips_atom_post_missing_fields(admin_client: Client) -> None:
    response = admin_client.post(
        reverse("administration:dips_atom_index"), {"url": "https://search.efimm.org"}
    )
    form = response.context["form"]
    config = DashboardSetting.objects.get_dict(_ATOM_DICTNAME)

    assert not form.is_valid()
    assert form.errors == {
        "email": ["This field is required."],
        "password": ["This field is required."],
        "version": ["This field is required."],
    }
    assert isinstance(config, dict)
