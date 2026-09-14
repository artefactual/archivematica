import time
from pathlib import Path

import api_helpers
import browser_helpers
import encryption_assertions
import storage_service_helpers
from models import ArchivematicaInstance
from models import ScenarioState
from models import TransferRun
from playwright.sync_api import Page
from pytest_bdd import given
from pytest_bdd import parsers
from pytest_bdd import then
from pytest_bdd import when
from requests import Session


def _current_package_uuid(transfer_run: TransferRun) -> str:
    package_uuid = transfer_run.reingest_uuid or transfer_run.sip_uuid
    assert package_uuid is not None
    return str(package_uuid)


def _aip_uuid_for_description(transfer_run: TransferRun, aip_description: str) -> str:
    normalized = aip_description.strip().lower()
    if normalized == "master":
        assert transfer_run.master_aip_uuid is not None
        return str(transfer_run.master_aip_uuid)
    if normalized == "replica":
        assert transfer_run.replica_aip_uuid is not None
        return str(transfer_run.replica_aip_uuid)
    return _current_package_uuid(transfer_run)


def _pointer_path_for_description(
    transfer_run: TransferRun,
    aip_description: str,
) -> Path:
    normalized = aip_description.strip().lower()
    if normalized == "master":
        assert transfer_run.master_aip_pointer_path is not None
        return Path(transfer_run.master_aip_pointer_path)
    if normalized == "replica":
        assert transfer_run.replica_aip_pointer_path is not None
        return Path(transfer_run.replica_aip_pointer_path)
    assert transfer_run.aip_pointer_path is not None
    return Path(transfer_run.aip_pointer_path)


def _download_path_for_description(
    transfer_run: TransferRun,
    aip_description: str,
) -> Path:
    normalized = aip_description.strip().lower()
    if normalized == "master":
        assert transfer_run.master_aip_download_path is not None
        return Path(transfer_run.master_aip_download_path)
    if normalized == "replica":
        assert transfer_run.replica_aip_download_path is not None
        return Path(transfer_run.replica_aip_download_path)
    assert transfer_run.aip_path is not None
    return Path(transfer_run.aip_path)


def _space_uuid_from_resource_uri(resource_uri: str) -> str:
    return resource_uri.rstrip("/").split("/")[-1]


@given("there is a standard GPG-encrypted space in the storage service")
def given_there_is_a_standard_gpg_encrypted_space_in_the_storage_service(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    scenario_state: ScenarioState,
) -> None:
    default_key = storage_service_helpers.get_default_gpg_key(
        instance,
        storage_service_session,
    )
    fingerprint = default_key.get("fingerprint")
    key_id = default_key.get("keyid_text")
    assert isinstance(fingerprint, str)
    assert isinstance(key_id, str)
    space = storage_service_helpers.ensure_standard_gpg_space(
        instance,
        storage_service_session,
        fingerprint,
    )
    space_uuid = space.get("uuid")
    assert isinstance(space_uuid, str)
    scenario_state.default_gpg_key_fingerprint = fingerprint
    scenario_state.default_gpg_key_id = key_id
    scenario_state.standard_gpg_space_uuid = space_uuid


@given("there is a standard GPG-encrypted AIP Storage location in the storage service")
def given_there_is_a_standard_gpg_encrypted_aip_storage_location(
    instance: ArchivematicaInstance,
    scenario_state: ScenarioState,
) -> None:
    assert scenario_state.standard_gpg_space_uuid is not None
    location = storage_service_helpers.ensure_storage_location(
        instance,
        space_uuid=scenario_state.standard_gpg_space_uuid,
        purpose="AS",
        relative_path=storage_service_helpers.STANDARD_GPG_LOCATION_PATH,
        description=storage_service_helpers.get_standard_gpg_location_description(
            scenario_state.standard_gpg_space_uuid
        ),
    )
    location_uuid = location.get("uuid")
    assert isinstance(location_uuid, str)
    scenario_state.standard_gpg_location_uuid = location_uuid


@given("there is a standard GPG-encrypted Replicator location in the storage service")
def given_there_is_a_standard_gpg_encrypted_replicator_location(
    instance: ArchivematicaInstance,
    scenario_state: ScenarioState,
) -> None:
    assert scenario_state.standard_gpg_space_uuid is not None
    location = storage_service_helpers.ensure_storage_location(
        instance,
        space_uuid=scenario_state.standard_gpg_space_uuid,
        purpose="RP",
        relative_path=storage_service_helpers.STANDARD_GPG_REPLICATOR_PATH,
        description="Encrypted Replicas",
    )
    location_uuid = location.get("uuid")
    assert isinstance(location_uuid, str)
    scenario_state.standard_gpg_replicator_location_uuid = location_uuid


@given(
    "the default AIP Storage location has the GPG-encrypted Replicator location as its replicator"
)
def given_the_default_aip_storage_location_has_the_gpg_encrypted_replicator(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    scenario_state: ScenarioState,
) -> None:
    assert scenario_state.standard_gpg_replicator_location_uuid is not None
    default_locations = [
        location
        for location in api_helpers.list_locations(instance)
        if location.get("description")
        == "Store AIP in standard Archivematica Directory"
        and location.get("purpose") == "AS"
    ]
    assert default_locations
    default_location = default_locations[0]
    location_uuid = default_location.get("uuid")
    space_resource = default_location.get("space")
    assert isinstance(location_uuid, str)
    assert isinstance(space_resource, str)
    storage_service_helpers.add_replicator_to_location(
        instance,
        storage_service_session,
        space_uuid=_space_uuid_from_resource_uri(space_resource),
        location_uuid=location_uuid,
        replicator_location_uuid=scenario_state.standard_gpg_replicator_location_uuid,
    )


@given(
    "automated processing configured to Store AIP Encrypted in standard Archivematica Directory"
)
def given_automated_processing_configured_to_store_aip_encrypted(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
    scenario_state: ScenarioState,
) -> None:
    assert scenario_state.standard_gpg_space_uuid is not None
    browser_helpers.open_processing_configuration_editor(
        authenticated_page,
        instance,
        name="automated",
    )
    configured = browser_helpers.set_processing_config_decision(
        authenticated_page,
        "Store AIP location",
        storage_service_helpers.get_standard_gpg_location_description(
            scenario_state.standard_gpg_space_uuid
        ),
    )
    assert configured
    browser_helpers.save_processing_configuration(authenticated_page)


@when(parsers.parse("the user attempts to import GPG key {key_fname}"))
def when_the_user_attempts_to_import_gpg_key(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    scenario_state: ScenarioState,
    key_fname: str,
) -> None:
    if key_fname == "aadams-passphraseless.key":
        storage_service_helpers.delete_gpg_key_if_exists(
            instance,
            storage_service_session,
            key_id=storage_service_helpers.PASSPHRASELESS_KEY_ID,
        )
    scenario_state.import_gpg_key_result = storage_service_helpers.import_gpg_key(
        instance,
        storage_service_session,
        storage_service_helpers.get_gpg_key_path(key_fname),
    )


@when(
    "the user creates a new GPG key and assigns it to the standard GPG-encrypted space"
)
def when_the_user_creates_a_new_gpg_key_and_assigns_it_to_the_standard_space(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    scenario_state: ScenarioState,
) -> None:
    name_real = f"GPGKey {int(time.time())}"
    name_email = f"{name_real.lower().replace(' ', '')}@example.com"
    key = storage_service_helpers.create_gpg_key(
        instance,
        storage_service_session,
        name_real=name_real,
        name_email=name_email,
    )
    fingerprint = key.get("fingerprint")
    key_id = key.get("keyid_text")
    assert isinstance(fingerprint, str)
    assert isinstance(key_id, str)
    assert scenario_state.standard_gpg_space_uuid is not None
    storage_service_helpers.change_encrypted_space_key(
        instance,
        storage_service_session,
        space_uuid=scenario_state.standard_gpg_space_uuid,
        new_key_fingerprint=fingerprint,
    )
    scenario_state.new_key_name = name_real
    scenario_state.new_key_email = name_email
    scenario_state.new_key_fingerprint = fingerprint
    scenario_state.new_key_id = key_id


@when("the user attempts to delete the new GPG key")
def when_the_user_attempts_to_delete_the_new_gpg_key(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    scenario_state: ScenarioState,
) -> None:
    assert scenario_state.new_key_fingerprint is not None
    (
        scenario_state.delete_gpg_key_success,
        scenario_state.delete_gpg_key_msg,
    ) = storage_service_helpers.delete_gpg_key(
        instance,
        storage_service_session,
        scenario_state.new_key_fingerprint,
    )


@when("the user assigns a different GPG key to the standard GPG-encrypted space")
def when_the_user_assigns_a_different_gpg_key_to_the_standard_space(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    scenario_state: ScenarioState,
) -> None:
    assert scenario_state.standard_gpg_space_uuid is not None
    target_fingerprint = scenario_state.default_gpg_key_fingerprint
    assert isinstance(target_fingerprint, str)
    if target_fingerprint == scenario_state.new_key_fingerprint:
        keys = storage_service_helpers.list_gpg_keys(instance, storage_service_session)
        replacement = next(
            (
                key
                for key in keys
                if key.get("fingerprint") != scenario_state.new_key_fingerprint
            ),
            None,
        )
        assert replacement is not None
        replacement_fingerprint = replacement.get("fingerprint")
        assert isinstance(replacement_fingerprint, str)
        target_fingerprint = replacement_fingerprint
    storage_service_helpers.change_encrypted_space_key(
        instance,
        storage_service_session,
        space_uuid=scenario_state.standard_gpg_space_uuid,
        new_key_fingerprint=target_fingerprint,
    )


@when("the user downloads the AIP pointer file")
def when_the_user_downloads_the_aip_pointer_file(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    download_root: Path,
) -> None:
    pointer_path = api_helpers.download_pointer_file(
        instance,
        _current_package_uuid(transfer_run),
        download_root / f"{transfer_run.transfer_name}-pointer.xml",
    )
    transfer_run.aip_pointer_path = pointer_path


@when(parsers.parse("the user downloads the {aip_description} AIP pointer file"))
def when_the_user_downloads_the_described_aip_pointer_file(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    download_root: Path,
    aip_description: str,
) -> None:
    package_uuid = _aip_uuid_for_description(transfer_run, aip_description)
    pointer_path = api_helpers.download_pointer_file(
        instance,
        package_uuid,
        download_root
        / f"{transfer_run.transfer_name}-{aip_description.strip()}-pointer.xml",
    )
    if aip_description.strip().lower() == "master":
        transfer_run.master_aip_pointer_path = pointer_path
    else:
        transfer_run.replica_aip_pointer_path = pointer_path


@when("the user searches for the AIP UUID in the Storage Service")
def when_the_user_searches_for_the_aip_uuid_in_the_storage_service(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    scenario_state: ScenarioState,
) -> None:
    assert transfer_run.sip_uuid is not None
    scenario_state.aip_search_results = storage_service_helpers.wait_for_multiple_aips(
        instance,
        aip_uuid=transfer_run.sip_uuid,
        expected_count=2,
    )


@when(parsers.parse("the user downloads the {aip_description} AIP"))
def when_the_user_downloads_the_described_aip(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    download_root: Path,
    aip_description: str,
) -> None:
    package_uuid = _aip_uuid_for_description(transfer_run, aip_description)
    archive_path = api_helpers.download_package(
        instance,
        package_uuid,
        download_root
        / f"{transfer_run.transfer_name}-{aip_description.strip()}-{package_uuid}.7z",
    )
    normalized = aip_description.strip().lower()
    if normalized == "master":
        transfer_run.master_aip_download_path = archive_path
    elif normalized == "replica":
        transfer_run.replica_aip_download_path = archive_path
    else:
        transfer_run.aip_path = archive_path


@when("the AIP is deleted")
def when_the_aip_is_deleted(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    scenario_state: ScenarioState,
) -> None:
    package_uuid = _current_package_uuid(transfer_run)
    request_id = api_helpers.request_aip_deletion(instance, package_uuid)
    scenario_state.aip_deletion_request_id = request_id
    api_helpers.review_aip_deletion(instance, package_uuid, request_id)
    api_helpers.wait_for_package_status(
        instance,
        package_uuid,
        expected_status="DELETED",
    )


@when("the user performs a metadata-only re-ingest on the AIP")
def when_the_user_performs_a_metadata_only_reingest_on_the_aip(
    instance: ArchivematicaInstance,
    authenticated_page: Page,
    scenario_state: ScenarioState,
    transfer_run: TransferRun,
) -> None:
    assert scenario_state.standard_gpg_space_uuid is not None
    browser_helpers.configure_processing_choices(
        authenticated_page,
        instance,
        {
            "Normalize": "Do not normalize",
            "Reminder: add metadata if desired": "None",
            "Transcribe SIP contents?": "No",
            "Store AIP": "Yes",
            "Store AIP location": storage_service_helpers.get_standard_gpg_location_description(
                scenario_state.standard_gpg_space_uuid
            ),
        },
    )
    api_helpers.request_reingest(
        instance,
        transfer_run,
        "METADATA_ONLY",
        "default",
    )
    assert transfer_run.reingest_uuid is not None
    reingest_session = api_helpers.login_dashboard_session(instance)
    api_helpers.choose_processing_option(
        instance,
        reingest_session,
        "ingest",
        transfer_run.reingest_uuid,
        "Approve AIP reingest|Reingest AIP",
        "Approve AIP reingest",
    )
    api_helpers.wait_for_processing_job(
        instance,
        reingest_session,
        "ingest",
        transfer_run.reingest_uuid,
        "Reminder: add metadata if desired",
        require_choices=True,
    )
    api_helpers.add_dummy_metadata(
        instance,
        reingest_session,
        transfer_run.sip_uuid or transfer_run.reingest_uuid,
    )
    api_helpers.choose_processing_option(
        instance,
        reingest_session,
        "ingest",
        transfer_run.reingest_uuid,
        "Reminder: add metadata if desired",
        "Continue",
    )
    api_helpers.wait_for_reingest_completion(instance, transfer_run)


@when("the user queries the API until the AIP has been stored")
def when_the_user_queries_the_api_until_the_aip_has_been_stored(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
) -> None:
    api_helpers.wait_for_package_status(
        instance,
        _current_package_uuid(transfer_run),
        expected_status="UPLOADED",
    )


@then("the pointer file contains a PREMIS:EVENT element for the encryption event")
def then_the_pointer_file_contains_a_premis_event_for_the_encryption_event(
    transfer_run: TransferRun,
) -> None:
    assert transfer_run.aip_pointer_path is not None
    encryption_assertions.assert_pointer_has_encryption_event(
        transfer_run.aip_pointer_path
    )


@then("the pointer file contains a mets:transformFile element for the encryption event")
def then_the_pointer_file_contains_a_transform_file_for_the_encryption_event(
    transfer_run: TransferRun,
) -> None:
    assert transfer_run.aip_pointer_path is not None
    encryption_assertions.assert_pointer_has_encryption_transform(
        transfer_run.aip_pointer_path
    )


@then(
    parsers.parse(
        "the {aip_description} pointer file contains a mets:transformFile element for the encryption event"
    )
)
def then_the_described_pointer_file_contains_a_transform_file_for_the_encryption_event(
    transfer_run: TransferRun,
    aip_description: str,
) -> None:
    encryption_assertions.assert_pointer_has_encryption_transform(
        _pointer_path_for_description(transfer_run, aip_description)
    )


@then("the AIP on disk is encrypted")
@then(parsers.parse("the {aip_description} AIP on disk is encrypted"))
def then_the_described_aip_on_disk_is_encrypted(
    transfer_run: TransferRun,
    aip_description: str = "",
) -> None:
    pointer_path = _pointer_path_for_description(transfer_run, aip_description)
    encryption_assertions.assert_on_disk_package_encrypted(pointer_path)


@then("the AIP on disk is not encrypted")
@then(parsers.parse("the {aip_description} AIP on disk is not encrypted"))
def then_the_described_aip_on_disk_is_not_encrypted(
    transfer_run: TransferRun,
    aip_description: str = "",
) -> None:
    pointer_path = _pointer_path_for_description(transfer_run, aip_description)
    encryption_assertions.assert_on_disk_package_not_encrypted(pointer_path)


@then("the downloaded AIP is not encrypted")
@then(parsers.parse("the downloaded {aip_description} AIP is not encrypted"))
def then_the_downloaded_described_aip_is_not_encrypted(
    transfer_run: TransferRun,
    aip_description: str = "",
) -> None:
    encryption_assertions.assert_downloaded_aip_is_not_encrypted(
        _download_path_for_description(transfer_run, aip_description)
    )


@then(parsers.parse("the user succeeds in importing the GPG key {key_name}"))
def then_the_user_succeeds_in_importing_the_gpg_key(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    scenario_state: ScenarioState,
    key_name: str,
) -> None:
    assert scenario_state.import_gpg_key_result is not None
    assert scenario_state.import_gpg_key_result.startswith("New key")
    assert scenario_state.import_gpg_key_result.endswith("created.")
    keys = storage_service_helpers.list_gpg_keys(instance, storage_service_session)
    assert any(key.get("keyid_text") == key_name for key in keys)


@then(
    parsers.parse(
        "the user fails to import the GPG key {key_name} because it requires a passphrase"
    )
)
def then_the_user_fails_to_import_the_gpg_key_because_it_requires_a_passphrase(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    scenario_state: ScenarioState,
    key_name: str,
) -> None:
    assert scenario_state.import_gpg_key_result == (
        "Import failed. The GPG key provided requires a passphrase. "
        "GPG keys with passphrases cannot be imported"
    )
    keys = storage_service_helpers.list_gpg_keys(instance, storage_service_session)
    assert all(key.get("keyid_text") != key_name for key in keys)


@then(parsers.parse("the uncompressed AIP on disk at {aips_store_path} is encrypted"))
def then_the_uncompressed_aip_on_disk_is_encrypted(
    transfer_run: TransferRun,
    aips_store_path: str,
) -> None:
    package_uuid = _current_package_uuid(transfer_run).replace("-", "")
    parts = [
        package_uuid[index : index + 4] for index in range(0, len(package_uuid), 4)
    ]
    package_path = (
        Path(aips_store_path)
        / Path(*parts)
        / f"{transfer_run.transfer_name}-{_current_package_uuid(transfer_run)}"
    )
    encryption_assertions.assert_on_disk_path_encrypted(package_path)


@then("the downloaded uncompressed AIP is an unencrypted tarfile")
def then_the_downloaded_uncompressed_aip_is_an_unencrypted_tarfile(
    transfer_run: TransferRun,
) -> None:
    assert transfer_run.aip_path is not None
    encryption_assertions.assert_downloaded_uncompressed_aip_is_tarfile(
        transfer_run.aip_path
    )


@then("the AIP pointer file references the fingerprint of the new GPG key")
def then_the_aip_pointer_file_references_the_fingerprint_of_the_new_gpg_key(
    transfer_run: TransferRun,
    scenario_state: ScenarioState,
) -> None:
    assert transfer_run.aip_pointer_path is not None
    assert scenario_state.new_key_fingerprint is not None
    encryption_assertions.assert_pointer_has_encryption_transform(
        transfer_run.aip_pointer_path,
        fingerprint=scenario_state.new_key_fingerprint,
    )


@then(parsers.parse("the user is prevented from deleting the key because {reason}"))
def then_the_user_is_prevented_from_deleting_the_key_because(
    scenario_state: ScenarioState,
    reason: str,
) -> None:
    assert scenario_state.delete_gpg_key_success is False
    assert scenario_state.delete_gpg_key_msg is not None
    if reason == "it is attached to a space":
        assert (
            "cannot be deleted because at least one GPG Space is using it"
            in scenario_state.delete_gpg_key_msg
        )
        return
    assert (
        "cannot be deleted because at least one package (AIP, transfer) needs it in order to be decrypted."
        in scenario_state.delete_gpg_key_msg
    )


@then("the user succeeds in deleting the GPG key")
def then_the_user_succeeds_in_deleting_the_gpg_key(
    scenario_state: ScenarioState,
) -> None:
    assert scenario_state.delete_gpg_key_success is True
    assert scenario_state.delete_gpg_key_msg is not None
    assert "successfully deleted" in scenario_state.delete_gpg_key_msg


@then("the master AIP and its replica are returned by the search")
def then_the_master_aip_and_its_replica_are_returned_by_the_search(
    transfer_run: TransferRun,
    scenario_state: ScenarioState,
) -> None:
    assert transfer_run.sip_uuid is not None
    assert len(scenario_state.aip_search_results) == 2
    master = next(
        (
            package
            for package in scenario_state.aip_search_results
            if package.get("uuid") == transfer_run.sip_uuid
        ),
        None,
    )
    replica = next(
        (
            package
            for package in scenario_state.aip_search_results
            if package.get("uuid") != transfer_run.sip_uuid
        ),
        None,
    )
    assert master is not None
    assert replica is not None
    assert replica.get("replicated_package") == f"/api/v2/file/{transfer_run.sip_uuid}/"
    replica_uuid = replica.get("uuid")
    assert isinstance(replica_uuid, str)
    transfer_run.master_aip_uuid = transfer_run.sip_uuid
    transfer_run.replica_aip_uuid = replica_uuid


@then(
    parsers.parse(
        "the {aip_description} pointer file contains a(n) {event_type} PREMIS:EVENT"
    )
)
def then_the_described_pointer_file_contains_a_named_premis_event(
    transfer_run: TransferRun,
    scenario_state: ScenarioState,
    aip_description: str,
    event_type: str,
) -> None:
    pointer_path = _pointer_path_for_description(transfer_run, aip_description)
    event_uuid = encryption_assertions.assert_pointer_has_event(
        pointer_path,
        event_type=event_type,
        outcome_contains=("success",) if event_type != "replication" else (),
    )
    scenario_state.pointer_event_uuids[
        f"{aip_description.strip().lower()}_{event_type.lower()}"
    ] = event_uuid


@then(
    parsers.parse(
        "the {aip_description} pointer file contains a PREMIS:OBJECT with a derivation relationship pointing to the {second_aip_description} and the {event_type} PREMIS:EVENT"
    )
)
def then_the_described_pointer_file_contains_a_derivation_relationship(
    transfer_run: TransferRun,
    scenario_state: ScenarioState,
    aip_description: str,
    second_aip_description: str,
    event_type: str,
) -> None:
    pointer_path = _pointer_path_for_description(transfer_run, aip_description)
    related_uuid = _aip_uuid_for_description(transfer_run, second_aip_description)
    event_uuid = scenario_state.pointer_event_uuids[
        f"{aip_description.strip().lower()}_{event_type.lower()}"
    ]
    encryption_assertions.assert_pointer_derivation_relationship(
        pointer_path,
        related_object_uuid=related_uuid,
        event_uuid=event_uuid,
    )


@then("the master and replica AIPs are byte-for-byte identical")
def then_the_master_and_replica_aips_are_byte_for_byte_identical(
    transfer_run: TransferRun,
) -> None:
    assert transfer_run.master_aip_download_path is not None
    assert transfer_run.replica_aip_download_path is not None
    encryption_assertions.assert_archives_are_identical(
        transfer_run.master_aip_download_path,
        transfer_run.replica_aip_download_path,
    )
