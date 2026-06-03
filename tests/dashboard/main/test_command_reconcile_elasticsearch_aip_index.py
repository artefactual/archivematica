import uuid

import elasticSearchFunctions as es
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.fixture
def search_enabled(settings):
    settings.SEARCH_ENABLED = [es.AIPS_INDEX]


@pytest.fixture
def es_client(mocker):
    return mocker.Mock()


@pytest.fixture
def package():
    return {
        "uuid": str(uuid.uuid4()),
        "package_type": "AIP",
        "status": es.STATUS_UPLOADED,
        "current_path": "objects/package-uuid",
        "current_full_path": "/var/archivematica/sharedDirectory/www/AIPsStore/package-uuid",
        "current_location": "/api/v2/location/11111111-1111-1111-1111-111111111111/",
        "origin_pipeline": "/api/v2/pipeline/22222222-2222-2222-2222-222222222222/",
    }


@pytest.fixture
def expected_source(package):
    return {
        "filePath": "/var/archivematica/sharedDirectory/www/AIPsStore/old-path",
        "location": "Old location",
        "origin": "33333333-3333-3333-3333-333333333333",
        "uuid": package["uuid"],
    }


def _patch_command(mocker, es_client, packages, indexed_source):
    mocker.patch(
        "main.management.commands.reconcile_elasticsearch_aip_index.setup_es_for_aip_reindexing",
        return_value=es_client,
    )
    mocker.patch(
        "main.management.commands.reconcile_elasticsearch_aip_index.storageService.get_file_info",
        return_value=packages,
    )
    mocker.patch(
        "main.management.commands.reconcile_elasticsearch_aip_index.storageService.location_description_from_slug",
        return_value={"description": "New location"},
    )
    mocker.patch(
        "main.management.commands.reconcile_elasticsearch_aip_index.es.search_all_results",
        return_value={"hits": {"hits": [{"_id": "doc-id", "_source": indexed_source}]}},
    )


@pytest.mark.django_db
def test_command_updates_changed_fields(search_enabled, mocker, es_client, package, expected_source, capsys):
    _patch_command(mocker, es_client, [package], expected_source)

    call_command("reconcile_elasticsearch_aip_index")

    es_client.update.assert_called_once_with(
        body={
            "doc": {
                "filePath": package["current_full_path"],
                "location": "New location",
                "origin": "22222222-2222-2222-2222-222222222222",
            }
        },
        index=es.AIPS_INDEX,
        doc_type=es.DOC_TYPE,
        id="doc-id",
        refresh=False,
    )
    captured = capsys.readouterr()
    assert package["uuid"] in captured.out
    assert "updated" in captured.out


@pytest.mark.django_db
def test_command_dry_run_does_not_update(search_enabled, mocker, es_client, package, expected_source, capsys):
    _patch_command(mocker, es_client, [package], expected_source)

    call_command("reconcile_elasticsearch_aip_index", "--dry-run")

    es_client.update.assert_not_called()
    captured = capsys.readouterr()
    assert "would update" in captured.out


@pytest.mark.django_db
def test_command_reports_no_changes(search_enabled, mocker, es_client, package, capsys):
    matching_source = {
        "filePath": package["current_full_path"],
        "location": "New location",
        "origin": "22222222-2222-2222-2222-222222222222",
        "uuid": package["uuid"],
    }
    _patch_command(mocker, es_client, [package], matching_source)

    call_command("reconcile_elasticsearch_aip_index")

    es_client.update.assert_not_called()
    captured = capsys.readouterr()
    assert "already matched" in captured.out


@pytest.mark.django_db
def test_command_rejects_invalid_uuid(search_enabled):
    with pytest.raises(CommandError):
        call_command("reconcile_elasticsearch_aip_index", "--uuid", "not-a-uuid")
