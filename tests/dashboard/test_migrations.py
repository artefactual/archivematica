import importlib
import uuid

import pytest
from django.core.exceptions import FieldDoesNotExist

# Import package that starts with a number.
mod = importlib.import_module(
    "archivematica.dashboard.main.migrations.0066_archivesspace_base_url"
)


@pytest.mark.parametrize(
    "host_and_port, expected_result",
    [
        ((None, None), ""),
        (("", ""), ""),
        (("foobar", ""), "http://foobar"),
        (("foobar.tld", ""), "http://foobar.tld"),
        (("foobar.tld", None), "http://foobar.tld"),
        (("foobar.tld", "12345"), "http://foobar.tld:12345"),
        (("http://foobar.tld", "12345"), "http://foobar.tld"),
        (("http://foobar.tld:789/asdf", "8089"), "http://foobar.tld:789/asdf"),
    ],
)
def test_0066_get_base_url(host_and_port, expected_result):
    """Test _get_baseurl."""
    assert expected_result == mod._get_base_url(*host_and_port), (
        "Failed with args %s" % (host_and_port)
    )


@pytest.mark.parametrize(
    "url, expected_result",
    [
        (None, ("", "")),
        ("", ("", "")),
        ("foobar.tld", ("foobar.tld", "")),
        ("foobar.tld:12345", ("foobar.tld", "12345")),
        ("http://foobar.tld", ("foobar.tld", "")),
        ("http://foobar.tld:8089", ("foobar.tld", "8089")),
        ("http://foobar.tld:8089/subpath", ("foobar.tld", "8089")),
    ],
)
def test_0066_get_host_and_port(url, expected_result):
    """Test _get_host_and_port."""
    assert expected_result == mod._get_host_and_port(url), f"Failed with arg {url}"


@pytest.mark.django_db(transaction=True)
def test_0090_rejects_referenced_invalid_metadata_types(migrate_apps):
    apps = migrate_apps(("main", "0089_remove_job_subjobof"))

    MetadataAppliesToType = apps.get_model("main", "MetadataAppliesToType")
    DublinCore = apps.get_model("main", "DublinCore")
    RightsStatement = apps.get_model("main", "RightsStatement")

    invalid_type = MetadataAppliesToType.objects.create(description="Unknown Value")
    dublincore = DublinCore.objects.create(
        metadataappliestotype=invalid_type,
        metadataappliestoidentifier=str(uuid.uuid4()),
    )
    rightsstatement = RightsStatement.objects.create(
        metadataappliestotype=invalid_type,
        metadataappliestoidentifier=str(uuid.uuid4()),
    )

    with pytest.raises(
        RuntimeError,
        match="Unsupported MetadataAppliesToType rows are referenced by metadata",
    ):
        migrate_apps(("main", "0090_add_metadata_applies_to_textchoice"))

    with pytest.raises(FieldDoesNotExist):
        DublinCore._meta.get_field("metadata_applies_to")

    dublincore.delete()
    rightsstatement.delete()
    invalid_type.delete()


@pytest.mark.django_db(transaction=True)
def test_0090_backfills_metadata_applies_to(migrate_apps):
    apps = migrate_apps(("main", "0089_remove_job_subjobof"))

    MetadataAppliesToType = apps.get_model("main", "MetadataAppliesToType")
    DublinCore = apps.get_model("main", "DublinCore")
    RightsStatement = apps.get_model("main", "RightsStatement")

    identifiers_by_applies_to = {
        "sip": str(uuid.uuid4()),
        "transfer": str(uuid.uuid4()),
        "file": str(uuid.uuid4()),
    }
    types_by_applies_to = {
        "sip": MetadataAppliesToType.objects.create(description="SIP"),
        "transfer": MetadataAppliesToType.objects.create(description=" transfer "),
        "file": MetadataAppliesToType.objects.create(description="FILE"),
    }

    for applies_to, identifier in identifiers_by_applies_to.items():
        type_ = types_by_applies_to[applies_to]
        DublinCore.objects.create(
            metadataappliestotype=type_,
            metadataappliestoidentifier=identifier,
            title=f"{applies_to} dc",
        )
        RightsStatement.objects.create(
            metadataappliestotype=type_,
            metadataappliestoidentifier=identifier,
        )

    apps = migrate_apps(("main", "0090_add_metadata_applies_to_textchoice"))
    DublinCore = apps.get_model("main", "DublinCore")
    RightsStatement = apps.get_model("main", "RightsStatement")

    for applies_to, identifier in identifiers_by_applies_to.items():
        assert (
            DublinCore.objects.get(
                metadataappliestoidentifier=identifier
            ).metadata_applies_to
            == applies_to
        )
        assert (
            RightsStatement.objects.get(
                metadataappliestoidentifier=identifier
            ).metadata_applies_to
            == applies_to
        )

    apps.get_model("main", "MetadataAppliesToType")

    apps = migrate_apps(("main", "0091_remove_metadata_applies_to_type_model"))
    DublinCore = apps.get_model("main", "DublinCore")
    RightsStatement = apps.get_model("main", "RightsStatement")

    with pytest.raises(LookupError):
        apps.get_model("main", "MetadataAppliesToType")
    with pytest.raises(FieldDoesNotExist):
        DublinCore._meta.get_field("metadataappliestotype")
    with pytest.raises(FieldDoesNotExist):
        RightsStatement._meta.get_field("metadataappliestotype")


@pytest.mark.django_db(transaction=True)
def test_0091_ignores_unreferenced_invalid_metadata_types(migrate_apps):
    apps = migrate_apps(("main", "0089_remove_job_subjobof"))
    MetadataAppliesToType = apps.get_model("main", "MetadataAppliesToType")

    MetadataAppliesToType.objects.create(description="")
    MetadataAppliesToType.objects.create(description="   ")
    MetadataAppliesToType.objects.create(description="Unknown Value")

    apps = migrate_apps(("main", "0091_remove_metadata_applies_to_type_model"))

    with pytest.raises(LookupError):
        apps.get_model("main", "MetadataAppliesToType")


@pytest.mark.django_db(transaction=True)
def test_0091_reverse_restores_legacy_metadata_type_fks(migrate_apps):
    apps = migrate_apps(("main", "0089_remove_job_subjobof"))

    MetadataAppliesToType = apps.get_model("main", "MetadataAppliesToType")
    DublinCore = apps.get_model("main", "DublinCore")
    sip_type, _ = MetadataAppliesToType.objects.get_or_create(
        id="3e48343d-e2d2-4956-aaa3-b54d26eb9761",
        defaults={"description": "SIP"},
    )
    dublincore = DublinCore.objects.create(
        metadataappliestotype=sip_type,
        metadataappliestoidentifier=str(uuid.uuid4()),
    )

    migrate_apps(("main", "0091_remove_metadata_applies_to_type_model"))
    apps = migrate_apps(("main", "0090_add_metadata_applies_to_textchoice"))

    DublinCore = apps.get_model("main", "DublinCore")
    dublincore = DublinCore.objects.get(id=dublincore.id)

    assert (
        str(dublincore.metadataappliestotype_id)
        == "3e48343d-e2d2-4956-aaa3-b54d26eb9761"
    )
