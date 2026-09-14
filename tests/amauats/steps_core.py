import os
import tempfile
import zipfile
from pathlib import Path

import aip_assertions
import api_helpers
import browser_helpers
import fpr_helpers
from api_helpers import METS_NSMAP
from lxml import etree
from models import ArchivematicaInstance
from models import ScenarioState
from models import TransferRun
from playwright.sync_api import Page
from pytest_bdd import given
from pytest_bdd import parsers
from pytest_bdd import then
from pytest_bdd import when
from requests import Session


def _resolve_remote_directory_path(
    instance: ArchivematicaInstance, dir_path: str
) -> Path:
    prefix = "~/archivematica-sampledata/"
    if dir_path.startswith(prefix):
        return Path(instance.sample_data_root) / dir_path.removeprefix(prefix)
    return Path(dir_path)


def _debag(paths: list[str]) -> list[str]:
    new_paths: list[str] = []
    for path in paths:
        parts = path.split(os.path.sep)
        if len(parts) > 3 and parts[2] == "data":
            new_paths.append(os.path.sep.join([""] + parts[3:]))
    return new_paths


def _remove_common_prefix(seq: list[str]) -> list[str]:
    try:
        prefixes = {value[0] for value in seq}
    except IndexError:
        return seq
    if len(prefixes) == 1:
        return _remove_common_prefix([value[1:] for value in seq])
    return seq


def _get_subpaths_from_struct_map(
    elem: etree._Element,
    base_path: str = "",
    paths: set[str] | None = None,
) -> list[str]:
    if paths is None:
        paths = set()
    for div_el in elem.findall("mets:div", METS_NSMAP):
        path = os.path.join(base_path, div_el.get("LABEL", ""))
        if path:
            paths.add(path)
        for subpath in _get_subpaths_from_struct_map(
            div_el, base_path=path, paths=paths
        ):
            paths.add(subpath)
    return list(paths)


def _is_uuid(value: str) -> bool:
    return (
        "".join(char for char in value if char in "-abcdef0123456789") == value
    ) and ([len(part) for part in value.split("-")] == [8, 4, 4, 4, 12])


def _unit_uuid(transfer_run: TransferRun, unit_type: str) -> str:
    if unit_type == "transfer":
        return str(transfer_run.transfer_uuid)
    assert transfer_run.sip_uuid is not None
    return str(transfer_run.sip_uuid)


def _current_package_uuid(transfer_run: TransferRun) -> str:
    package_uuid = transfer_run.reingest_uuid or transfer_run.sip_uuid
    assert package_uuid is not None
    return str(package_uuid)


def _current_aip_is_extracted(transfer_run: TransferRun) -> bool:
    if transfer_run.reingest_uuid is not None:
        return (
            transfer_run.reingest_extracted_aip_dir is not None
            and transfer_run.reingest_aip_mets_location is not None
        )
    return (
        transfer_run.extracted_aip_dir is not None
        and transfer_run.aip_mets_location is not None
    )


def _ensure_current_aip_artifacts(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    download_root: Path,
) -> None:
    package_uuid = _current_package_uuid(transfer_run)
    api_helpers.wait_for_aip_to_appear_in_archival_storage(instance, package_uuid)
    if transfer_run.reingest_uuid is not None:
        if transfer_run.reingest_aip_path is None:
            api_helpers.download_current_aip(instance, transfer_run, download_root)
    elif transfer_run.aip_path is None:
        api_helpers.download_current_aip(instance, transfer_run, download_root)
    if _current_aip_is_extracted(transfer_run):
        return
    archive_path = transfer_run.reingest_aip_path or transfer_run.aip_path
    assert archive_path is not None
    extracted_dir = api_helpers.extract_package(
        archive_path,
        package_uuid,
        download_root,
    )
    mets_path = api_helpers.get_aip_mets_location(extracted_dir, package_uuid)
    assert mets_path.is_file()
    if transfer_run.reingest_uuid is not None:
        transfer_run.reingest_extracted_aip_dir = extracted_dir
        transfer_run.reingest_aip_mets_location = mets_path
    else:
        transfer_run.extracted_aip_dir = extracted_dir
        transfer_run.aip_mets_location = mets_path


def _configure_automated_processing(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
    decisions: dict[str, str],
) -> None:
    baseline = {
        "Generate transfer structure report": "No",
        "Examine contents": "Skip examine contents",
    }
    browser_helpers.configure_processing_choices(
        authenticated_page,
        instance,
        {**baseline, **decisions},
        name="automated",
        optional_labels={"Generate thumbnails"},
    )


def _normalize_monitor_job_name(job_name: str) -> str:
    if job_name == "Approve normalization (review)":
        return (
            "Approve normalization (review)"
            "|Approve normalization Review"
            "|Approve normalization"
        )
    return job_name


@given("a processing configuration that assigns UUIDs to directories")
def given_processing_configuration_that_assigns_uuids(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
) -> None:
    browser_helpers.configure_processing_choices(
        authenticated_page,
        instance,
        {
            "Assign UUIDs to directories?": "Yes",
            "Perform file format identification (Transfer)": "Yes",
            "Create SIP(s)": "Create single SIP and continue processing",
            "Normalize": "Normalize for preservation",
            "Approve normalization": "Yes",
            "Perform file format identification (Submission documentation & metadata)": "Yes",
            "Perform policy checks on preservation derivatives": "No",
            "Perform policy checks on access derivatives": "No",
            "Perform policy checks on originals": "No",
            "Document empty directories?": "Yes",
            "Store AIP": "Yes",
            "Store AIP location": "Default location",
            "Transcribe SIP contents?": "No",
        },
        name="automated",
    )


@given("a processing configuration for testing manual normalization")
def given_processing_configuration_for_manual_normalization(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
) -> None:
    browser_helpers.configure_processing_choices(
        authenticated_page,
        instance,
        {
            "Assign UUIDs to directories?": "No",
            "Perform file format identification (Transfer)": "Yes",
            "Create SIP(s)": "Create single SIP and continue processing",
            "Normalize": "Normalize for preservation",
            "Approve normalization": "Yes",
            "Perform file format identification (Submission documentation & metadata)": "Yes",
            "Bind PIDs?": "No",
            "Store AIP": "Yes",
            "Store AIP location": "Default location",
            "Upload DIP": "Do not upload DIP",
            "Document empty directories?": "No",
            "Transcribe SIP contents?": "No",
        },
        name="automated",
    )


@given("a processing configuration for conformance checks on originals")
def given_processing_configuration_for_original_conformance_checks(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
) -> None:
    _configure_automated_processing(
        authenticated_page,
        instance,
        {
            "Assign UUIDs to directories?": "No",
            "Perform policy checks on preservation derivatives": "No",
            "Perform policy checks on access derivatives": "No",
            "Perform policy checks on originals": "No",
            "Create SIP(s)": "Create single SIP and continue processing",
            "Normalize": "Do not normalize",
            "Store AIP": "Yes",
            "Store AIP location": "Default location",
            "Transcribe SIP contents?": "No",
        },
    )


@given("automated processing with all decision points resolved")
def given_automated_processing_with_all_decision_points_resolved(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
) -> None:
    _configure_automated_processing(
        authenticated_page,
        instance,
        {
            "Assign UUIDs to directories?": "No",
            "Bind PIDs?": "No",
            "Perform file format identification (Transfer)": "Yes",
            "Create SIP(s)": "Create single SIP and continue processing",
            "Perform file format identification (Ingest)": "Yes",
            "Normalize": "Normalize for preservation and access",
            "Approve normalization": "Yes",
            "Perform file format identification (Submission documentation & metadata)": "Yes",
            "Perform policy checks on preservation derivatives": "No",
            "Perform policy checks on access derivatives": "No",
            "Perform policy checks on originals": "No",
            "Document empty directories?": "No",
            "Generate thumbnails": "No",
            "Upload DIP": "Do not upload DIP",
            "Store AIP": "Yes",
            "Store AIP location": "Default location",
            "Transcribe SIP contents?": "No",
        },
    )


@given("the reminder to add metadata is enabled")
def given_the_reminder_to_add_metadata_is_enabled(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
) -> None:
    browser_helpers.open_processing_configuration_editor(
        authenticated_page,
        instance,
        name="default",
    )
    configured = browser_helpers.set_processing_config_decision(
        authenticated_page,
        "Reminder: add metadata if desired",
        "None",
    )
    assert configured
    browser_helpers.save_processing_configuration(authenticated_page)


@given(
    parsers.parse(
        'the processing config decision "{decision_label}" is set to "{choice_value}"'
    )
)
def given_processing_config_decision_is_set(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
    decision_label: str,
    choice_value: str,
) -> None:
    browser_helpers.open_processing_configuration_editor(
        authenticated_page,
        instance,
        name="automated",
    )
    configured = browser_helpers.set_processing_config_decision(
        authenticated_page,
        decision_label,
        choice_value,
    )
    assert configured
    browser_helpers.save_processing_configuration(authenticated_page)


@given("a processing configuration for policy checks on preservation derivatives")
def given_processing_configuration_for_policy_checks_on_preservation_derivatives(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
    dashboard_session: Session,
) -> None:
    _configure_automated_processing(
        authenticated_page,
        instance,
        {
            "Assign UUIDs to directories?": "No",
            "Perform policy checks on preservation derivatives": "Yes",
            "Perform policy checks on access derivatives": "No",
            "Perform policy checks on originals": "No",
            "Perform file format identification (Transfer)": "Yes",
            "Create SIP(s)": "Create single SIP and continue processing",
            "Normalize": "Normalize for preservation",
            "Approve normalization": "Yes",
            "Perform file format identification (Submission documentation & metadata)": "Yes",
            "Bind PIDs?": "No",
            "Store AIP": "Yes",
            "Store AIP location": "Default location",
            "Upload DIP": "Do not upload DIP",
            "Document empty directories?": "No",
            "Transcribe SIP contents?": "No",
        },
    )
    for format_label in ("Generic MKV", "Generic MOV", "MPEG-4 Video"):
        fpr_helpers.ensure_fpr_rule_enabled(
            instance,
            dashboard_session,
            purpose="Preservation",
            format_label=format_label,
            command_description="Transcoding to mkv with ffmpeg",
        )


@given("a processing configuration for conformance checks on preservation derivatives")
def given_processing_configuration_for_conformance_checks_on_preservation_derivatives(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
    dashboard_session: Session,
) -> None:
    given_processing_configuration_for_policy_checks_on_preservation_derivatives(
        authenticated_page,
        instance,
        dashboard_session,
    )
    browser_helpers.open_processing_configuration_editor(
        authenticated_page,
        instance,
        name="automated",
    )
    for decision_label, choice_value in {
        "Perform policy checks on preservation derivatives": "No",
        "Approve normalization": "None",
    }.items():
        configured = browser_helpers.set_processing_config_decision(
            authenticated_page,
            decision_label,
            choice_value,
        )
        assert configured
    browser_helpers.save_processing_configuration(authenticated_page)


@given("a processing configuration for conformance checks on access derivatives")
def given_processing_configuration_for_conformance_checks_on_access_derivatives(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
) -> None:
    _configure_automated_processing(
        authenticated_page,
        instance,
        {
            "Assign UUIDs to directories?": "No",
            "Perform policy checks on preservation derivatives": "No",
            "Perform policy checks on access derivatives": "No",
            "Perform policy checks on originals": "No",
            "Perform file format identification (Transfer)": "Yes",
            "Create SIP(s)": "Create single SIP and continue processing",
            "Normalize": "Normalize for access",
            "Approve normalization": "None",
            "Perform file format identification (Submission documentation & metadata)": "Yes",
            "Bind PIDs?": "No",
            "Store AIP": "Yes",
            "Store AIP location": "Default location",
            "Upload DIP": "Do not upload DIP",
            "Document empty directories?": "No",
            "Transcribe SIP contents?": "No",
        },
    )


@given("a processing configuration for policy checks on access derivatives")
def given_processing_configuration_for_policy_checks_on_access_derivatives(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
) -> None:
    _configure_automated_processing(
        authenticated_page,
        instance,
        {
            "Assign UUIDs to directories?": "No",
            "Perform policy checks on preservation derivatives": "No",
            "Perform policy checks on access derivatives": "Yes",
            "Perform policy checks on originals": "No",
            "Perform file format identification (Transfer)": "Yes",
            "Create SIP(s)": "Create single SIP and continue processing",
            "Normalize": "Normalize for access",
            "Approve normalization": "Yes",
            "Perform file format identification (Submission documentation & metadata)": "Yes",
            "Bind PIDs?": "No",
            "Store AIP": "Yes",
            "Store AIP location": "Default location",
            "Upload DIP": "Do not upload DIP",
            "Document empty directories?": "No",
            "Transcribe SIP contents?": "No",
        },
    )


@given("a processing configuration for policy checks on originals")
def given_processing_configuration_for_policy_checks_on_originals(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
) -> None:
    _configure_automated_processing(
        authenticated_page,
        instance,
        {
            "Assign UUIDs to directories?": "No",
            "Perform policy checks on preservation derivatives": "No",
            "Perform policy checks on access derivatives": "No",
            "Perform policy checks on originals": "Yes",
            "Perform file format identification (Transfer)": "Yes",
            "Create SIP(s)": "Create single SIP and continue processing",
            "Normalize": "Do not normalize",
            "Approve normalization": "Yes",
            "Perform file format identification (Submission documentation & metadata)": "Yes",
            "Bind PIDs?": "No",
            "Store AIP": "Yes",
            "Store AIP location": "Default location",
            "Upload DIP": "Do not upload DIP",
            "Document empty directories?": "No",
            "Transcribe SIP contents?": "No",
        },
    )


@given(
    parsers.parse(
        'remote directory "{dir_path}" contains a hierarchy of subfolders containing digital objects'
    )
)
def given_remote_directory_contains_hierarchy(
    instance: ArchivematicaInstance,
    scenario_state: ScenarioState,
    dir_path: str,
) -> None:
    local_path = _resolve_remote_directory_path(instance, dir_path)
    dir_is_zipped = local_path.suffix != ""
    dir_local_path = local_path
    if dir_is_zipped:
        extracted_dir = Path(tempfile.mkdtemp())
        with zipfile.ZipFile(local_path) as archive:
            archive.extractall(extracted_dir)
        dir_local_path = extracted_dir

    assert dir_local_path.is_dir(), f"{dir_local_path} is not a directory"
    non_root_paths: list[str] = []
    non_root_file_paths: list[str] = []
    empty_dirs: list[str] = []
    to_be_removed_files = {"Thumbs.db", "Icon", "Icon\r", ".DS_Store"}

    for path, dirs, files in os.walk(dir_local_path):
        if path == str(dir_local_path):
            continue
        relative_path = path.replace(str(dir_local_path), "", 1)
        non_root_paths.append(relative_path)
        filtered_files = [
            os.path.join(relative_path, file_name)
            for file_name in files
            if file_name not in to_be_removed_files
        ]
        non_root_file_paths.extend(filtered_files)
        if not dirs and not filtered_files:
            empty_dirs.append(relative_path)

    if dir_is_zipped:
        non_root_paths = _debag(non_root_paths)
        non_root_file_paths = _debag(non_root_file_paths)

    assert non_root_paths
    assert non_root_file_paths
    scenario_state.remote_dir_subfolders = non_root_paths
    scenario_state.remote_dir_files = non_root_file_paths
    scenario_state.remote_dir_empty_subfolders = empty_dirs


@when(
    parsers.parse(
        'a "{transfer_type}" transfer is initiated on directory "{transfer_path}"'
    ),
    target_fixture="transfer_run",
)
def when_transfer_is_initiated(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
    transfer_type: str,
    transfer_path: str,
) -> TransferRun:
    return browser_helpers.start_transfer_via_ui(
        authenticated_page,
        instance,
        transfer_type,
        transfer_path,
        processing_config_name="automated",
    )


@when(
    parsers.parse("a transfer is initiated on directory {transfer_path}"),
    target_fixture="transfer_run",
)
def when_standard_transfer_is_initiated(
    authenticated_page: Page,
    instance: ArchivematicaInstance,
    transfer_path: str,
) -> TransferRun:
    return browser_helpers.start_transfer_via_ui(
        authenticated_page,
        instance,
        "standard",
        transfer_path,
        processing_config_name="automated",
    )


@when(
    parsers.parse(
        "the user ensures there is an FPR command that uses policy file {policy_file}"
    )
)
def when_user_ensures_there_is_an_fpr_command_that_uses_policy_file(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    policy_file: str,
) -> None:
    fpr_helpers.ensure_fpr_policy_check_command(
        instance,
        dashboard_session,
        policy_file,
    )


@when(
    parsers.parse(
        "the user ensures there is an FPR rule with purpose {purpose} that validates Generic MKV files against policy file {policy_file}"
    )
)
def when_user_ensures_there_is_an_fpr_rule_for_policy_check(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    purpose: str,
    policy_file: str,
) -> None:
    fpr_helpers.ensure_fpr_rule(
        instance,
        dashboard_session,
        purpose=purpose,
        format_label="Generic MKV",
        command_description=fpr_helpers.get_policy_command_description(policy_file),
    )


@when("the user edits the FPR rule to transcode .mkv files to .mkv for access")
def when_user_edits_the_fpr_rule_to_transcode_mkv_files_to_mkv_for_access(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
) -> None:
    fpr_helpers.change_normalization_rule_command(
        instance,
        dashboard_session,
        purpose="Access",
        format_label="Generic MKV",
        command_description="Transcoding to mkv with ffmpeg",
    )


@when("the user edits the FPR rule to transcode .mov files to .mkv for access")
def when_user_edits_the_fpr_rule_to_transcode_mov_files_to_mkv_for_access(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
) -> None:
    fpr_helpers.change_normalization_rule_command(
        instance,
        dashboard_session,
        purpose="Access",
        format_label="Generic MOV",
        command_description="Transcoding to mkv with ffmpeg",
    )


@when(
    parsers.parse(
        'the user waits for the "{decision_point}" decision point to appear during {unit_type}'
    )
)
def when_user_waits_for_decision_point_to_appear(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    transfer_run: TransferRun,
    decision_point: str,
    unit_type: str,
) -> None:
    if unit_type != "transfer" and transfer_run.sip_uuid is None:
        api_helpers.wait_for_transfer_completion(instance, transfer_run)
    api_helpers.wait_for_processing_job(
        instance,
        dashboard_session,
        unit_type,
        _unit_uuid(transfer_run, unit_type),
        _normalize_monitor_job_name(decision_point),
        require_choices=True,
    )


@when(
    parsers.parse(
        'the user chooses "{choice}" at decision point "{decision_point}" during {unit_type}'
    )
)
def when_user_chooses_at_decision_point(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    transfer_run: TransferRun,
    choice: str,
    decision_point: str,
    unit_type: str,
) -> None:
    if unit_type != "transfer" and transfer_run.sip_uuid is None:
        api_helpers.wait_for_transfer_completion(instance, transfer_run)
    api_helpers.choose_processing_option(
        instance,
        dashboard_session,
        unit_type,
        _unit_uuid(transfer_run, unit_type),
        _normalize_monitor_job_name(decision_point),
        choice,
    )


@when("the user waits for the AIP to appear in archival storage")
@then("the user waits for the AIP to appear in archival storage")
def when_user_waits_for_the_aip_to_appear_in_archival_storage(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
) -> None:
    if (
        transfer_run.reingest_uuid is not None
        and transfer_run.reingest_type is not None
    ):
        api_helpers.wait_for_reingest_completion(instance, transfer_run)
    else:
        api_helpers.wait_for_ingest_completion(instance, transfer_run)
    api_helpers.wait_for_aip_to_appear_in_archival_storage(
        instance,
        _current_package_uuid(transfer_run),
    )


@when("the user downloads the AIP")
@then("the user downloads the AIP")
def when_user_downloads_the_aip(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    download_root: Path,
) -> None:
    api_helpers.download_current_aip(instance, transfer_run, download_root)


@when("the user decompresses the AIP")
@then("the user decompresses the AIP")
def when_user_decompresses_the_aip(
    transfer_run: TransferRun,
    download_root: Path,
) -> None:
    package_uuid = _current_package_uuid(transfer_run)
    archive_path = transfer_run.reingest_aip_path or transfer_run.aip_path
    assert archive_path is not None
    extracted_dir = api_helpers.extract_package(
        archive_path,
        package_uuid,
        download_root,
    )
    mets_path = api_helpers.get_aip_mets_location(extracted_dir, package_uuid)
    assert mets_path.is_file()
    if transfer_run.reingest_uuid is not None:
        transfer_run.reingest_extracted_aip_dir = extracted_dir
        transfer_run.reingest_aip_mets_location = mets_path
    else:
        transfer_run.extracted_aip_dir = extracted_dir
        transfer_run.aip_mets_location = mets_path


@given(
    parsers.parse(
        "transfer source {transfer_path} which contains a manually normalized file whose path is a prefix of another manually normalized file"
    )
)
def given_transfer_source_contains_manually_normalized_prefix_case(
    instance: ArchivematicaInstance,
    transfer_path: str,
) -> None:
    path = instance.sample_data_root / transfer_path
    assert path.exists()


@given(
    parsers.parse(
        "directory {transfer_path} contains files that are all {file_validity} .mkv"
    )
)
@given(
    parsers.parse(
        "directory {transfer_path} contains files that will all be normalized to {file_validity} .mkv"
    )
)
def given_directory_contains_expected_mkv_files(
    instance: ArchivematicaInstance,
    transfer_path: str,
    file_validity: str,
) -> None:
    path = instance.sample_data_root / transfer_path
    assert path.exists()
    assert file_validity in {"valid", "not valid"}


@given(
    parsers.parse(
        "MediaConch policy file {policy_file} is present in the local etc/mediaconch-policies/ directory"
    )
)
def given_mediaconch_policy_file_is_present(policy_file: str) -> None:
    assert fpr_helpers.get_policy_file_path(policy_file).is_file()


@given(
    parsers.parse(
        "directory {transfer_path} contains files that, when normalized, will all {do_files_conform} to {policy_file}"
    )
)
@given(
    parsers.parse(
        "directory {transfer_path} contains files that all do {do_files_conform} to {policy_file}"
    )
)
def given_directory_contains_files_matching_policy_expectation(
    instance: ArchivematicaInstance,
    transfer_path: str,
    do_files_conform: str,
    policy_file: str,
) -> None:
    assert (instance.sample_data_root / transfer_path).exists()
    assert do_files_conform in {"conform", "not conform"}
    assert fpr_helpers.get_policy_file_path(policy_file).is_file()


@given(
    parsers.parse(
        "directory {transfer_path}/manualNormalization/preservation/ contains a file manually normalized for preservation that will {do_files_conform} to {policy_file}"
    )
)
@given(
    parsers.parse(
        "directory {transfer_path}/manualNormalization/access/ contains a file manually normalized for access that will {do_files_conform} to {policy_file}"
    )
)
def given_manual_normalization_directory_contains_policy_example(
    instance: ArchivematicaInstance,
    transfer_path: str,
    do_files_conform: str,
    policy_file: str,
) -> None:
    assert (instance.sample_data_root / transfer_path).exists()
    assert do_files_conform in {"conform", "not conform"}
    assert fpr_helpers.get_policy_file_path(policy_file).is_file()


@when(
    parsers.parse(
        'the user waits for the "{microservice_name}" micro-service to complete during {unit_type}'
    )
)
def when_user_waits_for_microservice_completion(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    scenario_state: ScenarioState,
    transfer_run: TransferRun,
    microservice_name: str,
    unit_type: str,
) -> None:
    if unit_type != "transfer" and transfer_run.sip_uuid is None:
        api_helpers.wait_for_transfer_completion(instance, transfer_run)
    scenario_state.latest_job_details = api_helpers.get_job_details(
        instance,
        dashboard_session,
        _unit_uuid(transfer_run, unit_type),
        unit_type=unit_type,
        job_name=_normalize_monitor_job_name(microservice_name),
    )


@then(
    parsers.parse(
        'the "{microservice_name}" micro-service output is "{expected_output}" during {unit_type}'
    )
)
def then_microservice_output_is_expected(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    scenario_state: ScenarioState,
    transfer_run: TransferRun,
    microservice_name: str,
    unit_type: str,
    expected_output: str,
) -> None:
    if unit_type != "transfer" and transfer_run.sip_uuid is None:
        api_helpers.wait_for_transfer_completion(instance, transfer_run)
    if scenario_state.latest_job_details is None:
        scenario_state.latest_job_details = api_helpers.get_job_details(
            instance,
            dashboard_session,
            _unit_uuid(transfer_run, unit_type),
            unit_type=unit_type,
            job_name=_normalize_monitor_job_name(microservice_name),
        )
    assert scenario_state.latest_job_details["job_output"] == expected_output


@then(
    parsers.parse(
        "policy checks for access derivatives micro-service output is {microservice_output}"
    )
)
def then_policy_checks_for_access_derivatives_output_is_expected(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    scenario_state: ScenarioState,
    transfer_run: TransferRun,
    microservice_output: str,
) -> None:
    then_microservice_output_is_expected(
        instance,
        dashboard_session,
        scenario_state,
        transfer_run,
        "Policy checks for access derivatives",
        "ingest",
        microservice_output,
    )


def _assert_policy_check_task_outcomes(
    scenario_state: ScenarioState,
    *,
    event_outcome: str,
) -> None:
    assert scenario_state.latest_job_details is not None
    policy_tasks = [
        task
        for task in scenario_state.latest_job_details["tasks"].values()
        if str(task.get("stdout", "")).startswith("Running Check against policy ")
    ]
    assert policy_tasks
    if event_outcome == "pass":
        for task in policy_tasks:
            stdout = str(task.get("stdout", ""))
            assert "All policy checks passed:" in stdout
            assert str(task.get("exit_code")) == "0"
        return
    for task in policy_tasks:
        assert '"eventOutcomeInformation": "fail"' in str(task.get("stdout", ""))


@then(
    parsers.parse(
        "all policy check for access derivatives tasks indicate {event_outcome}"
    )
)
def then_all_policy_check_for_access_derivatives_tasks_indicate_outcome(
    scenario_state: ScenarioState,
    event_outcome: str,
) -> None:
    _assert_policy_check_task_outcomes(
        scenario_state,
        event_outcome=event_outcome,
    )


@then(parsers.parse("all policy check for originals tasks indicate {event_outcome}"))
def then_all_policy_check_for_originals_tasks_indicate_outcome(
    scenario_state: ScenarioState,
    event_outcome: str,
) -> None:
    _assert_policy_check_task_outcomes(
        scenario_state,
        event_outcome=event_outcome,
    )


@then("the METS file includes the original directory structure")
def then_mets_includes_original_directory_structure(
    transfer_run: TransferRun,
    scenario_state: ScenarioState,
) -> None:
    assert transfer_run.aip_mets_location is not None
    mets = etree.parse(str(transfer_run.aip_mets_location))
    for struct_map_type, xpath in (
        ("physical", './/mets:structMap[@TYPE="physical"]'),
        ("logical", './/mets:structMap[@LABEL="Normative Directory Structure"]'),
    ):
        struct_map = mets.find(xpath, METS_NSMAP)
        assert struct_map is not None
        subpaths = _get_subpaths_from_struct_map(struct_map)
        subpaths = [
            path.replace("/objects", "", 1)
            for path in filter(None, _remove_common_prefix(subpaths))
        ]
        for dir_path in scenario_state.remote_dir_subfolders:
            if (
                struct_map_type == "physical"
                and dir_path in scenario_state.remote_dir_empty_subfolders
            ):
                continue
            assert dir_path in subpaths
        if struct_map_type == "physical":
            for file_path in scenario_state.remote_dir_files:
                if Path(file_path).name == ".gitignore":
                    continue
                assert file_path in subpaths


@then("the UUIDs for the subfolders and digital objects are written to the METS file")
def then_uuids_for_subfolders_and_objects_are_in_mets(
    transfer_run: TransferRun,
    scenario_state: ScenarioState,
) -> None:
    assert transfer_run.aip_mets_location is not None
    mets = etree.parse(str(transfer_run.aip_mets_location))
    for struct_map_type, xpath in (
        ("physical", './/mets:structMap[@TYPE="physical"]'),
        ("logical", './/mets:structMap[@LABEL="Normative Directory Structure"]'),
    ):
        struct_map = mets.find(xpath, METS_NSMAP)
        assert struct_map is not None
        for dir_path in scenario_state.remote_dir_subfolders:
            if (
                struct_map_type == "physical"
                and dir_path in scenario_state.remote_dir_empty_subfolders
            ):
                continue
            dirname = Path(dir_path).name
            mets_div = struct_map.find(f'.//mets:div[@LABEL="{dirname}"]', METS_NSMAP)
            assert mets_div is not None
            if (
                struct_map_type == "logical"
                and dir_path not in scenario_state.remote_dir_empty_subfolders
            ):
                continue
            dmd_id = mets_div.get("DMDID")
            assert dmd_id is not None
            dmd_sec = mets.find(f'.//mets:dmdSec[@ID="{dmd_id}"]', METS_NSMAP)
            assert dmd_sec is not None
            id_type = dmd_sec.findtext(
                ".//premis:objectIdentifierType", namespaces=METS_NSMAP
            )
            id_value = dmd_sec.findtext(
                ".//premis:objectIdentifierValue", namespaces=METS_NSMAP
            )
            assert id_type == "UUID"
            assert id_value is not None and _is_uuid(id_value.strip())


@then("all preservation tasks recognize the manually normalized derivatives")
def then_preservation_tasks_recognize_manually_normalized_derivatives(
    scenario_state: ScenarioState,
) -> None:
    assert scenario_state.latest_job_details is not None
    skipping_message = (
        "is file group usage manualNormalization instead of  original  - skipping"
    )
    already_normalized_message = "was already manually normalized into"
    for task in scenario_state.latest_job_details["tasks"].values():
        stdout = str(task["stdout"])
        assert skipping_message in stdout or already_normalized_message in stdout


@then("each manually normalized file is matched to an original")
def then_each_manually_normalized_file_is_matched_to_original(
    scenario_state: ScenarioState,
) -> None:
    assert scenario_state.latest_job_details is not None
    for task in scenario_state.latest_job_details["tasks"].values():
        stdout = str(task["stdout"])
        assert "Matched original file" in stdout
        assert "to  preservation file" in stdout


@then(
    parsers.parse(
        "all PREMIS implementation-check-type validation events have eventOutcome = {event_outcome}"
    )
)
def then_all_implementation_check_events_have_expected_outcome(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    download_root: Path,
    event_outcome: str,
) -> None:
    _ensure_current_aip_artifacts(instance, transfer_run, download_root)
    aip_assertions.assert_all_mediaconch_validation_events_have_outcome(
        transfer_run,
        outcome_detail_prefix=aip_assertions.MC_IMPLEMENTATION_CHECK_PREFIX,
        expected_outcome=event_outcome,
    )


@then(
    parsers.parse(
        "all PREMIS policy-check-type validation events have eventOutcome = {event_outcome}"
    )
)
def then_all_policy_check_events_have_expected_outcome(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    download_root: Path,
    event_outcome: str,
) -> None:
    _ensure_current_aip_artifacts(instance, transfer_run, download_root)
    aip_assertions.assert_all_mediaconch_validation_events_have_outcome(
        transfer_run,
        outcome_detail_prefix=aip_assertions.MC_POLICY_CHECK_PREFIX,
        expected_outcome=event_outcome,
    )


@then(
    parsers.parse(
        "all preservation conformance checks in the normalization report have value {validation_result}"
    )
)
def then_all_preservation_conformance_checks_have_expected_value(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    transfer_run: TransferRun,
    validation_result: str,
) -> None:
    if transfer_run.sip_uuid is None:
        api_helpers.wait_for_transfer_completion(instance, transfer_run)
    assert transfer_run.sip_uuid is not None
    report = api_helpers.get_normalization_report(
        instance,
        dashboard_session,
        transfer_run.sip_uuid,
    )
    aip_assertions.assert_normalization_report_column_values(
        report,
        column="preservation_conformance_check",
        expected_value=validation_result,
    )


@then(
    parsers.parse(
        "all access conformance checks in the normalization report have value {validation_result}"
    )
)
def then_all_access_conformance_checks_have_expected_value(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    transfer_run: TransferRun,
    validation_result: str,
) -> None:
    if transfer_run.sip_uuid is None:
        api_helpers.wait_for_transfer_completion(instance, transfer_run)
    assert transfer_run.sip_uuid is not None
    report = api_helpers.get_normalization_report(
        instance,
        dashboard_session,
        transfer_run.sip_uuid,
    )
    aip_assertions.assert_normalization_report_column_values(
        report,
        column="access_conformance_check",
        expected_value=validation_result,
    )


@then(
    parsers.parse(
        "the submissionDocumentation directory of the AIP {contains} a copy of the MediaConch policy file {policy_file}"
    )
)
def then_submission_documentation_contains_media_conch_policy_file(
    transfer_run: TransferRun,
    contains: str,
    policy_file: str,
) -> None:
    aip_assertions.assert_submission_documentation_policy_file(
        transfer_run,
        policy_file,
        should_exist=contains in {"contains", "does contain"},
    )


@then(
    parsers.parse(
        "the transfer logs directory of the AIP contains a MediaConch policy check output file for each policy file tested against {policy_file}"
    )
)
def then_transfer_logs_directory_contains_media_conch_policy_outputs(
    transfer_run: TransferRun,
    policy_file: str,
) -> None:
    aip_assertions.assert_transfer_logs_contain_policy_outputs(
        transfer_run,
        policy_file,
    )


@then(
    parsers.parse(
        "the logs directory of the AIP contains a MediaConch policy check output file for each policy file tested against {policy_file}"
    )
)
def then_logs_directory_contains_media_conch_policy_outputs(
    transfer_run: TransferRun,
    policy_file: str,
) -> None:
    aip_assertions.assert_logs_contain_policy_outputs(
        transfer_run,
        policy_file,
    )
