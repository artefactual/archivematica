from pathlib import Path

import aip_assertions
import api_helpers
import browser_helpers
from models import ArchivematicaInstance
from models import ScenarioState
from models import TransferRun
from playwright.sync_api import Page
from pytest_bdd import given
from pytest_bdd import parsers
from pytest_bdd import then
from pytest_bdd import when
from requests import Session

TRANSFER_JOB_VALID_EXIT_CODES = {
    "Assign UUIDs to directories": (0, 1),
    "Determine if transfer contains packages": (0, 1),
    "Determine if transfer still contains packages": (0, 1),
}

INGEST_JOB_VALID_EXIT_CODES = {
    "Bind PID": (0, 1),
    "Check for Access directory": (0, 179),
    "Check for manual normalized files": (0, 179),
    "Check if AIP is a file or directory": (0, 1),
    "Check if DIP should be generated": (0, 1),
    "Check if SIP is from Maildir Transfer": (0, 179),
    "Index AIP": (0, 179),
    "Is maildir AIP": (0, 179),
    "Normalize for access": (0, 1, 2),
    "Normalize for preservation": (0, 1, 2),
    "Normalize for thumbnails": (0, 1, 2),
    "Normalize service files for access": (0, 1, 2),
    "Normalize service files for thumbnails": (0, 1, 2),
    "Policy checks for access derivatives": (0, 1),
    "Policy checks for preservation derivatives": (0, 1),
    "Validate access derivatives": (0, 1),
    "Validate preservation derivatives": (0, 1),
}


def _current_ingest_uuid(transfer_run: TransferRun) -> str:
    if transfer_run.reingest_uuid is not None:
        return str(transfer_run.reingest_uuid)
    assert transfer_run.sip_uuid is not None
    return str(transfer_run.sip_uuid)


@given(
    parsers.parse(
        'a "{transfer_type}" transfer type located in "{sample_transfer_path}"'
    ),
    target_fixture="transfer_run",
)
def given_transfer_type(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
    transfer_type: str,
    sample_transfer_path: str,
) -> TransferRun:
    return browser_helpers.start_transfer_via_ui(
        authenticated_page,
        instance,
        transfer_type,
        sample_transfer_path,
        processing_config_name="automated",
    )


@given("the transfer has completed ingest successfully")
@when("the transfer has completed ingest successfully")
def when_transfer_has_completed_ingest_successfully(
    instance: ArchivematicaInstance, transfer_run: TransferRun
) -> None:
    api_helpers.wait_for_ingest_completion(instance, transfer_run)


@given("a processing configuration for metadata only reingests")
def given_processing_configuration_for_metadata_only_reingests(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
) -> None:
    browser_helpers.configure_processing_choices(
        authenticated_page,
        instance,
        {
            "Normalize": "Do not normalize",
            "Reminder: add metadata if desired": "Continue",
            "Transcribe SIP contents?": "No",
            "Store AIP": "Yes",
            "Store AIP location": "Default location",
        },
    )


@given("a processing configuration for metadata only reingests for uncompressed AIPs")
def given_processing_configuration_for_uncompressed_metadata_only_reingests(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
) -> None:
    browser_helpers.configure_processing_choices(
        authenticated_page,
        instance,
        {
            "Normalize": "Do not normalize",
            "Reminder: add metadata if desired": "Continue",
            "Transcribe SIP contents?": "No",
            "Store AIP": "Yes",
            "Store AIP location": "Default location",
            "Select compression algorithm": "Uncompressed",
        },
    )


@given("a processing configuration for partial reingests")
def given_processing_configuration_for_partial_reingests(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
) -> None:
    browser_helpers.configure_processing_choices(
        authenticated_page,
        instance,
        {
            "Normalize": "Normalize for access",
            "Approve normalization": "Yes",
            "Reminder: add metadata if desired": "Continue",
            "Transcribe SIP contents?": "No",
            "Store AIP": "Yes",
            "Store AIP location": "Default location",
            "Upload DIP": "Do not upload DIP",
            "Store DIP?": "Store DIP",
            "Store DIP location": "Default location",
        },
    )


@when("the transfer compliance is verified")
def when_transfer_compliance_is_verified(
    instance: ArchivematicaInstance, transfer_run: TransferRun
) -> None:
    api_helpers.wait_for_jobs_to_finish(
        instance,
        transfer_run.transfer_uuid,
        job_microservice="Verify transfer compliance",
    )


@when("the transfer is approved")
def when_transfer_is_approved(
    instance: ArchivematicaInstance, transfer_run: TransferRun
) -> None:
    api_helpers.assert_jobs_completed_successfully(
        instance,
        transfer_run.transfer_uuid,
        job_microservice="Approve transfer",
    )


@given("the AIP is downloaded and extracted")
@when("the AIP is downloaded and extracted")
def when_the_aip_is_downloaded_and_extracted(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    download_root: Path,
) -> None:
    api_helpers.wait_for_ingest_completion(instance, transfer_run)
    api_helpers.download_and_extract_aip(instance, transfer_run, download_root)


@when(
    parsers.parse(
        'a "{reingest_type}" reingest is started using the "{processing_config}" processing configuration'
    )
)
def when_reingest_is_started(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    reingest_type: str,
    processing_config: str,
) -> None:
    api_helpers.request_reingest(
        instance,
        transfer_run,
        reingest_type,
        processing_config,
    )


@when("the reingest is approved")
def when_the_reingest_is_approved(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
) -> None:
    api_helpers.approve_reingest(instance, transfer_run)


@when("the reingest has been processed")
def when_the_reingest_has_been_processed(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    download_root: Path,
) -> None:
    api_helpers.wait_for_reingest_completion(instance, transfer_run, download_root)


@when(parsers.parse('the "{metadata_file}" metadata file is added'))
def when_metadata_file_is_added(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    metadata_file: str,
) -> None:
    assert transfer_run.sip_uuid is not None
    api_helpers.copy_metadata_files(instance, transfer_run.sip_uuid, [metadata_file])


@then("the AIP METS can be accessed and parsed by mets-reader-writer")
def then_aip_mets_can_be_accessed_and_parsed(transfer_run: TransferRun) -> None:
    aip_assertions.assert_mets_is_accessible_and_parseable(transfer_run)


@then(
    "in the METS file the metsHdr element has a CREATEDATE attribute but no LASTMODDATE attribute"
)
def then_mets_hdr_has_create_date_only(transfer_run: TransferRun) -> None:
    aip_assertions.assert_mets_hdr_dates(transfer_run)


@then(
    "in the METS file the metsHdr element has a CREATEDATE attribute and a LASTMODDATE attribute"
)
def then_mets_hdr_has_create_and_last_modified_dates(
    transfer_run: TransferRun,
) -> None:
    aip_assertions.assert_mets_hdr_dates(transfer_run, lastmod_required=True)


@then(
    parsers.parse(
        "in the METS file the metsHdr element has {expected_count:d} dmdSec next sibling element(s)"
    )
)
def then_mets_hdr_has_expected_dmdsecs(
    transfer_run: TransferRun, expected_count: int
) -> None:
    aip_assertions.assert_dmdsec_count(transfer_run, expected_count)


@then("the AIP conforms to expected content and structure")
def then_aip_conforms_to_expected_content_and_structure(
    transfer_run: TransferRun,
) -> None:
    aip_assertions.assert_expected_content_and_structure(transfer_run)


@then("the AIP contains all files that were present in the transfer")
def then_aip_contains_all_transfer_files(transfer_run: TransferRun) -> None:
    aip_assertions.assert_transfer_files_are_present(transfer_run)


@then(parsers.parse("the AIP contains a file called {filename} in the data directory"))
def then_aip_contains_expected_file_in_data_directory(
    transfer_run: TransferRun, filename: str
) -> None:
    if filename == "METS.xml":
        aip_assertions.assert_data_directory_contains_mets_file(transfer_run)
        return
    aip_assertions.assert_data_directory_contains_file(transfer_run, f"data/{filename}")


@then(
    "the fileSec of the AIP METS will record every file in the objects and metadata directories of the AIP"
)
def then_filesec_records_every_aip_file(transfer_run: TransferRun) -> None:
    aip_assertions.assert_filesec_records_all_aip_files(transfer_run)


@then(
    "the physical structMap of the AIP METS accurately reflects the physical layout of the AIP"
)
def then_physical_struct_map_reflects_aip_layout(transfer_run: TransferRun) -> None:
    aip_assertions.assert_structmap_matches_physical_layout(transfer_run)


@then("every object in the AIP has been assigned a UUID in the AIP METS")
def then_every_object_has_uuid(transfer_run: TransferRun) -> None:
    aip_assertions.assert_every_object_has_uuid(transfer_run)


@then("every object in the objects and metadata directories has an amdSec")
def then_every_object_has_amdsec(transfer_run: TransferRun) -> None:
    aip_assertions.assert_every_object_has_amdsec(transfer_run)


@then(
    "every PREMIS event recorded in the AIP METS records the logged-in user, the organization and the software as PREMIS agents"
)
def then_every_premis_event_has_expected_agents(transfer_run: TransferRun) -> None:
    aip_assertions.assert_every_premis_event_records_expected_agents(transfer_run)


@then(parsers.parse('the "{job_name}" job completes successfully'))
def then_transfer_job_completes_successfully(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    job_name: str,
) -> None:
    api_helpers.assert_jobs_completed_successfully(
        instance,
        transfer_run.transfer_uuid,
        job_name=job_name,
        valid_exit_codes=TRANSFER_JOB_VALID_EXIT_CODES.get(job_name, (0,)),
    )


@then(parsers.parse('the "{job_name}" ingest job completes successfully'))
def then_ingest_job_completes_successfully(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    job_name: str,
) -> None:
    api_helpers.assert_jobs_completed_successfully(
        instance,
        _current_ingest_uuid(transfer_run),
        job_name=job_name,
        valid_exit_codes=INGEST_JOB_VALID_EXIT_CODES.get(job_name, (0,)),
    )


@then(parsers.parse('the "{job_name}" job fails'))
def then_transfer_job_fails(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    job_name: str,
) -> None:
    api_helpers.assert_jobs_fail(
        instance,
        transfer_run.transfer_uuid,
        job_name=job_name,
    )


@then(parsers.parse('the "{microservice_name}" microservice is executed'))
def then_microservice_is_executed(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    microservice_name: str,
) -> None:
    api_helpers.assert_microservice_executes(
        instance,
        transfer_run.transfer_uuid,
        microservice_name,
    )


@then(parsers.parse('the "{microservice_name}" microservice completes successfully'))
def then_transfer_microservice_completes_successfully(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    microservice_name: str,
) -> None:
    api_helpers.assert_jobs_completed_successfully(
        instance,
        transfer_run.transfer_uuid,
        job_microservice=microservice_name,
    )


@then(
    parsers.parse(
        'the "{microservice_name}" ingest microservice completes successfully'
    )
)
def then_ingest_microservice_completes_successfully(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    microservice_name: str,
) -> None:
    api_helpers.assert_jobs_completed_successfully(
        instance,
        _current_ingest_uuid(transfer_run),
        job_microservice=microservice_name,
    )


@then("the AIP can be successfully stored")
def then_aip_can_be_successfully_stored(transfer_run: TransferRun) -> None:
    aip_assertions.assert_mets_is_accessible_and_parseable(transfer_run)


@then(
    parsers.re(
        r"there is a.? (?P<event_type>.*) event for each original object in the AIP METS"
    )
)
def then_there_is_an_event_for_each_original_object(
    transfer_run: TransferRun, event_type: str
) -> None:
    aip_assertions.assert_event_count_per_original(transfer_run, event_type, 1)


@then(
    parsers.parse(
        "there are {event_count:d} {event_type} events for each original object in the AIP METS"
    )
)
def then_there_are_expected_events_for_each_original_object(
    transfer_run: TransferRun,
    event_count: int,
    event_type: str,
) -> None:
    aip_assertions.assert_event_count_per_original(
        transfer_run, event_type, event_count
    )


@then(
    parsers.parse(
        "there are {expected_files_count:d} original objects in the AIP METS with a {event_type} event"
    )
)
def then_there_are_expected_original_objects_with_event(
    transfer_run: TransferRun,
    expected_files_count: int,
    event_type: str,
) -> None:
    aip_assertions.assert_original_files_with_event_count(
        transfer_run,
        event_type,
        expected_files_count,
    )


@then("there is a current and a superseded techMD for each original object")
def then_there_is_current_and_superseded_techmd_for_each_original_object(
    transfer_run: TransferRun,
) -> None:
    aip_assertions.assert_current_and_superseded_techmd_per_original(transfer_run)


@then("there is a sourceMD containing a BagIt mdWrap in the AIP METS")
def then_there_is_bagit_sourcemd_in_aip(transfer_run: TransferRun) -> None:
    aip_assertions.assert_source_md_in_bagit_mets(transfer_run)


@then("there is a sourceMD containing a BagIt mdWrap in the reingested AIP METS")
def then_there_is_bagit_sourcemd_in_reingested_aip(
    transfer_run: TransferRun,
) -> None:
    aip_assertions.assert_source_md_in_bagit_mets(transfer_run, reingested=True)


@then("there is a fileSec for deleted files for objects that were re-normalized")
def then_deleted_filesec_exists_for_renormalized_objects(
    transfer_run: TransferRun,
) -> None:
    aip_assertions.assert_deleted_filesec_for_renormalized_objects(transfer_run)


@then("the METS file contains a dmdSec with DDI metadata")
def then_mets_file_contains_ddi_metadata(transfer_run: TransferRun) -> None:
    aip_assertions.assert_ddi_metadata_present(transfer_run)


@then(
    parsers.parse(
        "there are {expected_object_count:d} {object_type} in the AIP METS with a DMDSEC containing DC metadata"
    )
)
def then_aip_mets_contains_expected_dc_dmdsecs(
    transfer_run: TransferRun,
    expected_object_count: int,
    object_type: str,
) -> None:
    aip_assertions.assert_dc_dmdsec_count_for_object_type(
        transfer_run,
        object_type,
        expected_object_count,
    )


@then(
    parsers.parse(
        "there are {expected_entries_count:d} objects in the AIP METS with a rightsMD section containing PREMIS:RIGHTS"
    )
)
def then_aip_mets_contains_expected_rightsmd_objects(
    transfer_run: TransferRun, expected_entries_count: int
) -> None:
    aip_assertions.assert_rights_md_object_count(transfer_run, expected_entries_count)


@then(parsers.parse("there are {expected_entries_count:d} PREMIS:RIGHTS entries"))
def then_aip_mets_contains_expected_premis_rights_entries(
    transfer_run: TransferRun, expected_entries_count: int
) -> None:
    aip_assertions.assert_premis_rights_entries_count(
        transfer_run,
        expected_entries_count,
    )


@then(
    parsers.parse(
        "there are {expected_entries_count:d} submission documents listed in the AIP METS as submission documentation"
    )
)
def then_aip_mets_contains_expected_submission_documents(
    transfer_run: TransferRun,
    expected_entries_count: int,
) -> None:
    aip_assertions.assert_submission_document_count(
        transfer_run,
        expected_entries_count,
    )


@then(parsers.parse('the "{metadata_file}" file is in the reingest metadata directory'))
def then_file_is_in_the_reingest_metadata_directory(
    transfer_run: TransferRun, metadata_file: str
) -> None:
    aip_assertions.assert_reingest_metadata_directory_contains_file(
        transfer_run,
        metadata_file,
    )


@then("the DIP is downloaded")
def then_the_dip_is_downloaded(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    download_root: Path,
) -> None:
    api_helpers.download_and_extract_dip(instance, transfer_run, download_root)


@then("the DIP contains access copies for each original object in the transfer")
def then_the_dip_contains_access_copies_for_each_original_object(
    transfer_run: TransferRun,
) -> None:
    aip_assertions.assert_dip_contains_access_copy_for_each_original_object(
        transfer_run
    )


@then(
    "every file in the reingested metadata.csv file has two dmdSecs with the original and updated metadata"
)
def then_reingested_metadata_csv_files_have_two_dmdsecs(
    transfer_run: TransferRun,
) -> None:
    aip_assertions.assert_metadata_csv_files_have_original_and_updated_dmdsecs(
        transfer_run
    )


@then("the provided structural map will be included in the AIP METs file")
def then_provided_structural_map_is_included_in_the_aip_mets_file(
    transfer_run: TransferRun,
) -> None:
    aip_assertions.assert_structural_map_was_imported(transfer_run)


@then("there are 2 DSpace-specific descriptive metadata sections for each object")
def then_there_are_two_dspace_descriptive_metadata_sections_per_object(
    transfer_run: TransferRun,
) -> None:
    aip_assertions.assert_dspace_descriptive_metadata_sections(transfer_run)


@then("there is a DSpace-specific rights metadata section for each object")
def then_there_is_a_dspace_specific_rights_metadata_section_per_object(
    transfer_run: TransferRun,
) -> None:
    aip_assertions.assert_dspace_rights_metadata_sections(transfer_run)


@then("the entries in the file section of the METS are sorted by file group")
def then_filesec_entries_are_sorted_by_file_group(transfer_run: TransferRun) -> None:
    aip_assertions.assert_filesec_is_sorted_by_file_group(transfer_run)


@then(parsers.parse('{task_count:d} "{job_name}" {unit_type} tasks were executed'))
def then_expected_tasks_were_executed(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    task_count: int,
    job_name: str,
    unit_type: str,
) -> None:
    unit_uuid = (
        transfer_run.transfer_uuid
        if unit_type == "transfer"
        else _current_ingest_uuid(transfer_run)
    )
    jobs = api_helpers.wait_for_jobs_to_finish(
        instance,
        unit_uuid,
        job_name=job_name,
        detailed=True,
    )
    assert sum(len(job["tasks"]) for job in jobs) == task_count


@then(parsers.parse('{task_count:d} "{job_name}" {unit_type} tasks failed'))
def then_expected_tasks_failed(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    task_count: int,
    job_name: str,
    unit_type: str,
) -> None:
    unit_uuid = (
        transfer_run.transfer_uuid
        if unit_type == "transfer"
        else _current_ingest_uuid(transfer_run)
    )
    jobs = api_helpers.wait_for_jobs_to_finish(
        instance,
        unit_uuid,
        job_name=job_name,
        detailed=True,
    )
    failed_tasks = [
        task for job in jobs for task in job["tasks"] if task.get("exit_code") == 1
    ]
    assert len(failed_tasks) == task_count


@then(parsers.parse('{task_count:d} "{job_name}" {unit_type} tasks succeeded'))
def then_expected_tasks_succeeded(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    task_count: int,
    job_name: str,
    unit_type: str,
) -> None:
    unit_uuid = (
        transfer_run.transfer_uuid
        if unit_type == "transfer"
        else _current_ingest_uuid(transfer_run)
    )
    jobs = api_helpers.wait_for_jobs_to_finish(
        instance,
        unit_uuid,
        job_name=job_name,
        detailed=True,
    )
    successful_tasks = [
        task for job in jobs for task in job["tasks"] if task.get("exit_code") == 0
    ]
    assert len(successful_tasks) == task_count


@then(parsers.parse("{file_count:d} {file_extension} file(s) {status}"))
def then_expected_file_validation_outcomes_occurred(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    file_count: int,
    file_extension: str,
    status: str,
) -> None:
    jobs = api_helpers.wait_for_jobs_to_finish(
        instance,
        transfer_run.transfer_uuid,
        job_name="Validate formats",
        detailed=True,
    )
    expected_exit_codes = {"failed": (1, 179), "succeeded": (0,)}[status]
    total = 0
    for job in jobs:
        for task in job["tasks"]:
            file_name = str(task.get("file_name", ""))
            exit_code = task.get("exit_code")
            if (
                file_name.lower().endswith(f".{file_extension.lower()}")
                and exit_code in expected_exit_codes
            ):
                total += 1
    assert total == file_count


@then(
    "every metadata XML file in source-metadata.csv that has been validated has a PREMIS event with metadata validation details and pass outcome"
)
def then_metadata_xml_files_have_validation_events(transfer_run: TransferRun) -> None:
    aip_assertions.assert_metadata_files_have_passed_validation_events(transfer_run)


@then(
    parsers.parse(
        'every metadata XML file in source-metadata.csv has a dmdSec with STATUS "{dmdsec_status}" that has a mdWrap with the specified OTHERMDTYPE which wraps the XML content'
    )
)
def then_metadata_xml_files_have_wrapped_dmdsecs(
    transfer_run: TransferRun, dmdsec_status: str
) -> None:
    aip_assertions.assert_source_metadata_files_have_wrapped_original_dmdsecs(
        transfer_run,
        dmdsec_status,
    )


@then(
    "every existing metadata XML file in the reingested source-metadata.csv has two dmdSecs with the same GROUPID, one with the original XML content which has been superseded by a new one that contains the updated XML content"
)
def then_existing_metadata_xml_files_are_superseded_and_updated(
    transfer_run: TransferRun,
) -> None:
    aip_assertions.assert_existing_source_metadata_files_are_superseded_and_updated(
        transfer_run
    )


@then(
    parsers.parse(
        'every new metadata XML file in the reingested source-metadata.csv has a dmdSec with STATUS "{dmdsec_status}" that has a mdWrap with the specified OTHERMDTYPE which wraps the XML content'
    )
)
def then_new_metadata_xml_files_have_expected_dmdsecs(
    transfer_run: TransferRun, dmdsec_status: str
) -> None:
    aip_assertions.assert_new_source_metadata_files_have_update_dmdsecs(
        transfer_run,
        dmdsec_status,
    )


@then(
    parsers.parse(
        'every deleted metadata XML file in the reingested source-metadata.csv has a dmdSec with STATUS "{dmdsec_status}" that has a mdWrap with the specified OTHERMDTYPE which wraps the original XML content'
    )
)
def then_deleted_metadata_xml_files_have_deleted_dmdsecs(
    transfer_run: TransferRun, dmdsec_status: str
) -> None:
    aip_assertions.assert_deleted_source_metadata_files_have_deleted_dmdsecs(
        transfer_run,
        dmdsec_status,
    )


@then(
    "the AIP can be found in the Archival storage tab by searching the contents of its latest metadata files"
)
def then_aip_can_be_found_by_latest_metadata_files(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    scenario_state: ScenarioState,
    transfer_run: TransferRun,
) -> None:
    rows = (
        transfer_run.reingest_source_metadata_files
        if transfer_run.reingest_source_metadata_files
        else transfer_run.source_metadata_files
    )
    ignored_files = {"metadata.txt.xml"}
    current_aip_uuid = _current_ingest_uuid(transfer_run)
    namespaces = api_helpers.get_metadata_xml_namespaces(api_helpers.METS_NSMAP)
    search_results = []
    for row in rows:
        metadata_filename = row.get("metadata_filename")
        document = row.get("document")
        if metadata_filename in ignored_files or document is None:
            continue
        search_phrase = api_helpers.get_search_phrase_for_metadata_file(
            document,
            namespaces,
        )
        assert search_phrase is not None
        results = api_helpers.wait_for_archival_storage_search_results(
            instance,
            dashboard_session,
            aip_uuid=current_aip_uuid,
            search_phrase=search_phrase,
            expected_count=1,
        )
        search_results.extend(results)
    scenario_state.aip_search_results = search_results


@then(
    "the AIP can not be found in the Archival storage tab by searching the original contents of the deleted metadata files"
)
def then_aip_cannot_be_found_by_deleted_metadata_files(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    transfer_run: TransferRun,
) -> None:
    assert transfer_run.reingest_source_metadata_files
    original_source_metadata_by_type_id = {
        str(row["type_id"]): row for row in transfer_run.source_metadata_files
    }
    rows = [
        row
        for row in transfer_run.reingest_source_metadata_files
        if row.get("document") is None
        and str(row.get("type_id")) in original_source_metadata_by_type_id
        and original_source_metadata_by_type_id[str(row["type_id"])].get(
            "metadata_filename"
        )
        != "metadata.txt.xml"
    ]
    current_aip_uuid = _current_ingest_uuid(transfer_run)
    namespaces = api_helpers.get_metadata_xml_namespaces(api_helpers.METS_NSMAP)
    for row in rows:
        original_row = original_source_metadata_by_type_id[str(row["type_id"])]
        document = original_row.get("document")
        assert document is not None
        search_phrase = api_helpers.get_search_phrase_for_metadata_file(
            document,
            namespaces,
        )
        assert search_phrase is not None
        api_helpers.wait_for_archival_storage_search_results(
            instance,
            dashboard_session,
            aip_uuid=current_aip_uuid,
            search_phrase=search_phrase,
            expected_count=0,
        )
