import base64
import csv
import re
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from lxml import etree
from lxml import html
from models import ArchivematicaInstance
from models import TransferRun

JsonDict = dict[str, Any]

METS_NSMAP = {
    "mets": "http://www.loc.gov/METS/",
    "premis": "http://www.loc.gov/premis/v3",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "xlink": "http://www.w3.org/1999/xlink",
}

TERMINAL_JOB_STATUSES = {"COMPLETE", "FAILED", "USER_INPUT"}
PROCESSING_MONITOR_ROUTES = {
    "transfer": "transfer/status/",
    "ingest": "ingest/status/",
}
PROCESSING_CONFIG_RESET_FIELDS = {
    "Generate transfer structure report": "No",
    "Perform file format identification (Transfer)": "None",
    "Extract packages": "Yes",
    "Delete packages after extraction": "Yes",
    "Examine contents": "Skip examine contents",
    "Create SIP(s)": "None",
    "Perform file format identification (Ingest)": "No, use existing data",
    "Normalize": "None",
    "Approve normalization": "None",
    "Reminder: add metadata if desired": "Continue",
    "Transcribe files (OCR)": "No",
    "Perform file format identification (Submission documentation & metadata)": "None",
    "Select compression algorithm": "7z using bzip2",
    "Select compression level": "5 - normal compression",
    "Store AIP": "None",
    "Store AIP location": "None",
    "Store DIP location": "None",
    "Perform policy checks on access derivatives": "None",
    "Perform policy checks on originals": "None",
    "Perform policy checks on preservation derivatives": "None",
    "Assign UUIDs to directories": "None",
    "Bind PIDs": "None",
    "Document empty directories": "None",
    "Generate thumbnails": "No",
}
MONITOR_STATUS_LABELS = {
    "COMPLETE": "Completed successfully",
    "FAILED": "Failed",
    "USER_INPUT": "Awaiting decision",
    "PROCESSING": "Processing",
    "UNKNOWN": "Unknown",
    "0": "Unknown",
    "1": "Awaiting decision",
    "2": "Completed successfully",
    "3": "Executing command(s)",
    "4": "Failed",
}
_CSRF_TOKEN_RE = re.compile(r'name="csrfmiddlewaretoken"\s+value="(?P<token>[^"]+)"')


class ArchivematicaAmaUatsError(Exception):
    pass


def _dashboard_auth(instance: ArchivematicaInstance) -> dict[str, str]:
    return {
        "username": instance.dashboard_username,
        "api_key": instance.dashboard_api_key,
    }


def _storage_service_auth(instance: ArchivematicaInstance) -> dict[str, str]:
    return {
        "username": instance.storage_service_username,
        "api_key": instance.storage_service_api_key,
    }


def _storage_service_basic_auth(instance: ArchivematicaInstance) -> tuple[str, str]:
    return (
        instance.storage_service_username,
        instance.storage_service_password,
    )


def _get_json(url: str, params: dict[str, str]) -> JsonDict:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ArchivematicaAmaUatsError(f"Unexpected payload from {url}: {payload!r}")
    return payload


def _get_json_or_none(
    url: str,
    params: dict[str, str],
    transient_statuses: tuple[int, ...] = (400, 404),
) -> JsonDict | None:
    response = requests.get(url, params=params, timeout=30)
    if response.status_code in transient_statuses:
        return None
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ArchivematicaAmaUatsError(f"Unexpected payload from {url}: {payload!r}")
    return payload


def _get_json_list(url: str, params: dict[str, str]) -> list[JsonDict]:
    response = requests.get(url, params=params, timeout=30)
    if response.status_code == 400:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if (
            isinstance(payload, dict)
            and payload.get("error") is True
            and isinstance(payload.get("message"), str)
            and "No jobs found for unit" in payload["message"]
        ):
            return []
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ArchivematicaAmaUatsError(f"Unexpected payload from {url}: {payload!r}")
    results: list[JsonDict] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ArchivematicaAmaUatsError(
                f"Unexpected item in payload from {url}: {item!r}"
            )
        results.append(item)
    return results


def _get_paginated_objects(
    url: str,
    params: dict[str, str],
) -> list[JsonDict]:
    objects: list[JsonDict] = []
    next_url: str | None = url
    next_params: dict[str, str] | None = params
    while next_url is not None:
        response = requests.get(next_url, params=next_params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ArchivematicaAmaUatsError(
                f"Unexpected paginated payload from {next_url}: {payload!r}"
            )
        page_objects = payload.get("objects")
        if not isinstance(page_objects, list):
            raise ArchivematicaAmaUatsError(
                f"Unexpected paginated object payload from {next_url}: {payload!r}"
            )
        for item in page_objects:
            if not isinstance(item, dict):
                raise ArchivematicaAmaUatsError(
                    f"Unexpected item in paginated payload from {next_url}: {item!r}"
                )
            objects.append(item)
        meta = payload.get("meta")
        next_path = meta.get("next") if isinstance(meta, dict) else None
        if isinstance(next_path, str) and next_path:
            next_url = urljoin(url, next_path)
            next_params = None
            continue
        next_url = None
    return objects


def _post_json(url: str, params: dict[str, str], data: dict[str, str]) -> JsonDict:
    response = requests.post(url, params=params, data=data, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ArchivematicaAmaUatsError(f"Unexpected payload from {url}: {payload!r}")
    return payload


def _post_json_or_raise(
    url: str,
    params: dict[str, str],
    data: dict[str, str],
    *,
    expected_message: str | None = None,
) -> JsonDict:
    payload = _post_json(url, params, data)
    if expected_message is not None and payload.get("message") != expected_message:
        raise ArchivematicaAmaUatsError(f"Unexpected response from {url}: {payload!r}")
    return payload


def _extract_csrf_token(content: str) -> str:
    match = _CSRF_TOKEN_RE.search(content)
    if match is None:
        raise ArchivematicaAmaUatsError("Unable to extract CSRF token from login page")
    return match.group("token")


def _login_session(
    login_url: str,
    username: str,
    password: str,
    next_path: str,
) -> requests.Session:
    session = requests.Session()
    response = session.get(login_url, timeout=30)
    response.raise_for_status()
    csrf_token = session.cookies.get("csrftoken") or _extract_csrf_token(response.text)
    payload = {
        "username": username,
        "password": password,
        "next": next_path,
        "csrfmiddlewaretoken": csrf_token,
    }
    post_response = session.post(
        login_url,
        data=payload,
        headers={"Referer": login_url},
        timeout=30,
        allow_redirects=True,
    )
    post_response.raise_for_status()
    if "login" in post_response.url:
        raise ArchivematicaAmaUatsError(
            f"Login failed for {login_url}: still at {post_response.url}"
        )
    return session


def login_dashboard_session(instance: ArchivematicaInstance) -> requests.Session:
    return _login_session(
        urljoin(instance.dashboard_url, "administration/accounts/login/"),
        instance.dashboard_username,
        instance.dashboard_password,
        "/transfer/",
    )


def login_storage_service_session(instance: ArchivematicaInstance) -> requests.Session:
    return _login_session(
        urljoin(instance.storage_service_url, "login/"),
        instance.storage_service_username,
        instance.storage_service_password,
        "/",
    )


def get_transfer_status(
    instance: ArchivematicaInstance, transfer_uuid: str
) -> JsonDict | None:
    url = urljoin(instance.dashboard_url, f"api/transfer/status/{transfer_uuid}")
    return _get_json_or_none(url, _dashboard_auth(instance))


def get_ingest_status(
    instance: ArchivematicaInstance, sip_uuid: str
) -> JsonDict | None:
    url = urljoin(instance.dashboard_url, f"api/ingest/status/{sip_uuid}")
    return _get_json_or_none(url, _dashboard_auth(instance))


def wait_for_transfer_completion(
    instance: ArchivematicaInstance, transfer_run: TransferRun
) -> None:
    deadline = time.monotonic() + instance.timeout_seconds
    while time.monotonic() < deadline:
        payload = get_transfer_status(instance, transfer_run.transfer_uuid)
        if payload is None:
            time.sleep(instance.poll_interval)
            continue
        status = payload.get("status")
        if status == "FAILED":
            raise ArchivematicaAmaUatsError(
                f"Transfer {transfer_run.transfer_uuid} failed: {payload}"
            )
        sip_uuid = payload.get("sip_uuid")
        if status == "COMPLETE" and isinstance(sip_uuid, str) and sip_uuid:
            transfer_run.sip_uuid = sip_uuid
            return
        time.sleep(instance.poll_interval)
    raise ArchivematicaAmaUatsError(
        f"Timed out waiting for transfer {transfer_run.transfer_uuid} to complete"
    )


def wait_for_ingest_completion(
    instance: ArchivematicaInstance, transfer_run: TransferRun
) -> None:
    if transfer_run.sip_uuid is None:
        wait_for_transfer_completion(instance, transfer_run)
    assert transfer_run.sip_uuid is not None
    deadline = time.monotonic() + instance.timeout_seconds
    while time.monotonic() < deadline:
        payload = get_ingest_status(instance, transfer_run.sip_uuid)
        if payload is None:
            time.sleep(instance.poll_interval)
            continue
        status = payload.get("status")
        if status == "FAILED":
            raise ArchivematicaAmaUatsError(
                f"Ingest {transfer_run.sip_uuid} failed: {payload}"
            )
        if status == "COMPLETE":
            return
        time.sleep(instance.poll_interval)
    raise ArchivematicaAmaUatsError(
        f"Timed out waiting for ingest {transfer_run.sip_uuid} to complete"
    )


def _save_stream_to_path(response: requests.Response, destination: Path) -> None:
    with destination.open("wb") as handle:
        for block in response.iter_content(1024):
            handle.write(block)


def _package_download_url(instance: ArchivematicaInstance, package_uuid: str) -> str:
    return str(
        urljoin(instance.storage_service_url, f"api/v2/file/{package_uuid}/download/")
    )


def _pointer_file_url(instance: ArchivematicaInstance, package_uuid: str) -> str:
    return str(
        urljoin(
            instance.storage_service_url, f"api/v2/file/{package_uuid}/pointer_file/"
        )
    )


def download_package(
    instance: ArchivematicaInstance,
    package_uuid: str,
    destination: Path,
) -> Path:
    deadline = time.monotonic() + instance.timeout_seconds
    url = _package_download_url(instance, package_uuid)
    while time.monotonic() < deadline:
        response = requests.get(
            url,
            params=_storage_service_auth(instance),
            stream=True,
            timeout=60,
        )
        if response.ok:
            _save_stream_to_path(response, destination)
            return destination
        if response.status_code not in (404, 500):
            response.raise_for_status()
        time.sleep(instance.poll_interval)
    raise ArchivematicaAmaUatsError(
        f"Timed out waiting for package {package_uuid} to become downloadable"
    )


def download_aip(
    instance: ArchivematicaInstance, transfer_run: TransferRun, download_root: Path
) -> Path:
    if transfer_run.sip_uuid is None:
        raise ArchivematicaAmaUatsError(
            "Cannot download an AIP before ingest completes"
        )
    destination = (
        download_root / f"{transfer_run.transfer_name}-{transfer_run.sip_uuid}.7z"
    )
    return download_package(instance, transfer_run.sip_uuid, destination)


def download_current_aip(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    download_root: Path,
) -> Path:
    package_uuid = transfer_run.reingest_uuid or transfer_run.sip_uuid
    if package_uuid is None:
        raise ArchivematicaAmaUatsError(
            "Cannot download an AIP before ingest or reingest completes"
        )
    destination = download_root / f"{transfer_run.transfer_name}-{package_uuid}.7z"
    package_path = download_package(instance, package_uuid, destination)
    if transfer_run.reingest_uuid is not None:
        transfer_run.reingest_aip_path = package_path
    else:
        transfer_run.aip_path = package_path
    return package_path


def _extract_package(
    package_file: Path, package_uuid: str, tmp_dir: Path, lookup_uuid: str | None = None
) -> Path:
    command = ["7z", "x", "-bd", "-y", f"-o{tmp_dir}", str(package_file)]
    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        raise ArchivematicaAmaUatsError(
            f"Could not extract package {package_file}: {error.output!r}"
        ) from error

    lookup = lookup_uuid or package_uuid
    matching_entries = [
        entry
        for entry in tmp_dir.iterdir()
        if entry != package_file and lookup in entry.name
    ]
    extracted_entry = next(
        (entry for entry in matching_entries if entry.is_dir()), None
    )
    if extracted_entry is None:
        extracted_entry = next(
            (entry for entry in matching_entries if entry.is_file()), None
        )

    if extracted_entry is None:
        raise ArchivematicaAmaUatsError(
            f"Could not find extracted package entry for {lookup} in {tmp_dir}"
        )
    if extracted_entry.is_dir():
        return extracted_entry
    return _extract_package(extracted_entry, package_uuid, tmp_dir, lookup)


def extract_package(
    package_file: Path,
    package_uuid: str,
    tmp_dir: Path,
    lookup_uuid: str | None = None,
) -> Path:
    return _extract_package(package_file, package_uuid, tmp_dir, lookup_uuid)


def get_aip_mets_location(extracted_aip_dir: Path, sip_uuid: str) -> Path:
    return extracted_aip_dir / "data" / f"METS.{sip_uuid}.xml"


def get_dip_mets_location(extracted_dip_dir: Path, sip_uuid: str) -> Path:
    return extracted_dip_dir / f"METS.{sip_uuid}.xml"


def get_aip_file_location(extracted_aip_dir: Path, relative_path: str) -> Path:
    return extracted_aip_dir / relative_path


def _set_original_aip_artifacts(
    transfer_run: TransferRun,
    aip_path: Path,
    extracted_aip_dir: Path,
    aip_mets_location: Path,
) -> None:
    transfer_run.aip_path = aip_path
    transfer_run.extracted_aip_dir = extracted_aip_dir
    transfer_run.aip_mets_location = aip_mets_location
    transfer_run.metadata_csv_files = get_metadata_csv_files(
        transfer_run.transfer_name,
        transfer_run.transfer_uuid,
        extracted_aip_dir,
    )
    transfer_run.source_metadata_files = get_source_metadata(
        transfer_run.transfer_name,
        transfer_run.transfer_uuid,
        extracted_aip_dir,
    )


def _set_reingested_aip_artifacts(
    transfer_run: TransferRun,
    aip_path: Path,
    extracted_aip_dir: Path,
    aip_mets_location: Path,
) -> None:
    transfer_run.reingest_aip_path = aip_path
    transfer_run.reingest_extracted_aip_dir = extracted_aip_dir
    transfer_run.reingest_aip_mets_location = aip_mets_location
    transfer_run.reingest_metadata_csv_files = get_metadata_csv_files(
        transfer_run.transfer_name,
        transfer_run.transfer_uuid,
        extracted_aip_dir,
    )
    transfer_run.reingest_source_metadata_files = get_source_metadata(
        transfer_run.transfer_name,
        transfer_run.transfer_uuid,
        extracted_aip_dir,
    )


def download_and_extract_aip(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    download_root: Path,
    reingested: bool = False,
) -> None:
    if reingested:
        package_uuid = transfer_run.reingest_uuid
        if package_uuid is None:
            raise ArchivematicaAmaUatsError(
                "No reingested AIP is available to download"
            )
        destination = download_root / f"{transfer_run.transfer_name}-{package_uuid}.7z"
        aip_path = download_package(instance, package_uuid, destination)
        extracted_aip_dir = _extract_package(aip_path, package_uuid, download_root)
        aip_mets_location = get_aip_mets_location(extracted_aip_dir, package_uuid)
        if not aip_mets_location.is_file():
            raise ArchivematicaAmaUatsError(
                f"Expected METS file at {aip_mets_location}, but it was not found"
            )
        _set_reingested_aip_artifacts(
            transfer_run,
            aip_path,
            extracted_aip_dir,
            aip_mets_location,
        )
        return

    aip_path = download_aip(instance, transfer_run, download_root)
    assert transfer_run.sip_uuid is not None
    extracted_aip_dir = _extract_package(aip_path, transfer_run.sip_uuid, download_root)
    aip_mets_location = get_aip_mets_location(extracted_aip_dir, transfer_run.sip_uuid)
    if not aip_mets_location.is_file():
        raise ArchivematicaAmaUatsError(
            f"Expected METS file at {aip_mets_location}, but it was not found"
        )
    _set_original_aip_artifacts(
        transfer_run, aip_path, extracted_aip_dir, aip_mets_location
    )


def list_packages(
    instance: ArchivematicaInstance, filters: dict[str, str] | None = None
) -> list[JsonDict]:
    params = _storage_service_auth(instance)
    if filters:
        params.update(filters)
    return _get_paginated_objects(
        urljoin(instance.storage_service_url, "api/v2/file/"),
        params,
    )


def get_package(
    instance: ArchivematicaInstance,
    package_uuid: str,
) -> JsonDict:
    payload = _get_json(
        urljoin(instance.storage_service_url, f"api/v2/file/{package_uuid}/"),
        _storage_service_auth(instance),
    )
    return payload


def get_package_or_none(
    instance: ArchivematicaInstance,
    package_uuid: str,
) -> JsonDict | None:
    return _get_json_or_none(
        urljoin(instance.storage_service_url, f"api/v2/file/{package_uuid}/"),
        _storage_service_auth(instance),
    )


def wait_for_package_status(
    instance: ArchivematicaInstance,
    package_uuid: str,
    *,
    expected_status: str,
) -> JsonDict:
    deadline = time.monotonic() + instance.timeout_seconds
    while time.monotonic() < deadline:
        payload = get_package(instance, package_uuid)
        status = payload.get("status")
        if status == expected_status:
            return payload
        time.sleep(instance.poll_interval)
    raise ArchivematicaAmaUatsError(
        f"Timed out waiting for package {package_uuid} to reach {expected_status!r}"
    )


def request_aip_deletion(
    instance: ArchivematicaInstance,
    package_uuid: str,
    *,
    reason: str = "AMAUAT package deletion request",
) -> int:
    response = requests.post(
        urljoin(
            instance.storage_service_url, f"api/v2/file/{package_uuid}/delete_aip/"
        ),
        auth=_storage_service_basic_auth(instance),
        json={
            "event_reason": reason,
            "pipeline": get_default_storage_service_pipeline_uuid(instance),
            "user_id": "1",
            "user_email": "test@example.com",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ArchivematicaAmaUatsError(
            f"Unexpected delete request response payload: {payload!r}"
        )
    request_id = payload.get("id")
    if not isinstance(request_id, int):
        raise ArchivematicaAmaUatsError(
            f"Delete request response missing id: {payload!r}"
        )
    return request_id


def review_aip_deletion(
    instance: ArchivematicaInstance,
    package_uuid: str,
    request_id: int,
    *,
    decision: str = "approve",
    reason: str = "AMAUAT deletion approval",
) -> JsonDict:
    response = requests.post(
        urljoin(
            instance.storage_service_url,
            f"api/v2/file/{package_uuid}/review_aip_deletion/",
        ),
        auth=_storage_service_basic_auth(instance),
        json={
            "event_id": request_id,
            "decision": decision,
            "reason": reason,
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ArchivematicaAmaUatsError(
            f"Unexpected deletion review response payload: {payload!r}"
        )
    return payload


def list_spaces(
    instance: ArchivematicaInstance,
    filters: dict[str, str] | None = None,
) -> list[JsonDict]:
    params = _storage_service_auth(instance)
    if filters:
        params.update(filters)
    return _get_paginated_objects(
        urljoin(instance.storage_service_url, "api/v2/space/"),
        params,
    )


def list_locations(
    instance: ArchivematicaInstance,
    filters: dict[str, str] | None = None,
) -> list[JsonDict]:
    params = _storage_service_auth(instance)
    if filters:
        params.update(filters)
    return _get_paginated_objects(
        urljoin(instance.storage_service_url, "api/v2/location/"),
        params,
    )


def create_space(
    instance: ArchivematicaInstance,
    *,
    access_protocol: str,
    path: str,
    staging_path: str,
    extra_fields: dict[str, str] | None = None,
) -> JsonDict:
    payload = {
        "access_protocol": access_protocol,
        "path": path,
        "staging_path": staging_path,
    }
    if extra_fields:
        payload.update(extra_fields)
    response = requests.post(
        urljoin(instance.storage_service_url, "api/v2/space/"),
        auth=_storage_service_basic_auth(instance),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict):
        raise ArchivematicaAmaUatsError(f"Unexpected space creation response: {body!r}")
    return body


def create_location(
    instance: ArchivematicaInstance,
    *,
    space_resource_uri: str,
    purpose: str,
    relative_path: str,
    description: str,
    pipeline_resource_uris: list[str],
) -> JsonDict:
    response = requests.post(
        urljoin(instance.storage_service_url, "api/v2/location/"),
        auth=_storage_service_basic_auth(instance),
        json={
            "space": space_resource_uri,
            "purpose": purpose,
            "relative_path": relative_path,
            "description": description,
            "pipeline": pipeline_resource_uris,
        },
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict):
        raise ArchivematicaAmaUatsError(
            f"Unexpected location creation response: {body!r}"
        )
    return body


def get_default_storage_service_pipeline_uuid(instance: ArchivematicaInstance) -> str:
    response = requests.get(
        urljoin(instance.storage_service_url, "api/v2/pipeline/"),
        auth=_storage_service_basic_auth(instance),
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ArchivematicaAmaUatsError(
            f"Unexpected payload from pipeline endpoint: {payload!r}"
        )
    objects = payload.get("objects")
    if not isinstance(objects, list) or not objects:
        raise ArchivematicaAmaUatsError("No Storage Service pipelines are registered")
    first = objects[0]
    if not isinstance(first, dict):
        raise ArchivematicaAmaUatsError(f"Unexpected pipeline payload entry: {first!r}")
    uuid = first.get("uuid")
    if not isinstance(uuid, str) or not uuid:
        raise ArchivematicaAmaUatsError(f"Unexpected pipeline entry: {first!r}")
    return uuid


def get_default_storage_service_pipeline_resource_uri(
    instance: ArchivematicaInstance,
) -> str:
    return f"/api/v2/pipeline/{get_default_storage_service_pipeline_uuid(instance)}/"


def _normalize_reingest_type(reingest_type: str) -> str:
    normalized = reingest_type.strip().upper().replace("-", "_")
    aliases = {
        "METADATA_ONLY": "METADATA",
        "METADATA": "METADATA",
        "OBJECTS": "OBJECTS",
        "FULL": "FULL",
    }
    return aliases.get(normalized, normalized)


def request_reingest(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    reingest_type: str,
    processing_config: str,
) -> None:
    if transfer_run.sip_uuid is None:
        wait_for_ingest_completion(instance, transfer_run)
    assert transfer_run.sip_uuid is not None
    url = urljoin(
        instance.storage_service_url, f"api/v2/file/{transfer_run.sip_uuid}/reingest/"
    )
    response = requests.post(
        url,
        auth=_storage_service_basic_auth(instance),
        json={
            "pipeline": get_default_storage_service_pipeline_uuid(instance),
            "reingest_type": _normalize_reingest_type(reingest_type),
            "processing_config": processing_config,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ArchivematicaAmaUatsError(
            f"Unexpected reingest response payload: {payload!r}"
        )
    reingest_uuid = payload.get("reingest_uuid")
    if not isinstance(reingest_uuid, str) or not reingest_uuid:
        raise ArchivematicaAmaUatsError(
            f"Unexpected reingest response payload: {payload!r}"
        )
    transfer_run.reingest_type = _normalize_reingest_type(reingest_type)
    transfer_run.reingest_processing_config = processing_config
    transfer_run.reingest_uuid = reingest_uuid


def approve_transfer(
    instance: ArchivematicaInstance,
    transfer_uuid: str,
) -> str:
    deadline = time.monotonic() + instance.timeout_seconds
    payload: JsonDict | None = None
    while time.monotonic() < deadline:
        payload = get_transfer_status(instance, transfer_uuid)
        if payload is None:
            time.sleep(instance.poll_interval)
            continue
        if payload.get("status") == "USER_INPUT":
            break
        time.sleep(instance.poll_interval)
    if payload is None or payload.get("status") != "USER_INPUT":
        raise ArchivematicaAmaUatsError(
            f"Transfer {transfer_uuid} did not reach USER_INPUT for approval"
        )
    directory = payload.get("directory")
    if not isinstance(directory, str) or not directory:
        raise ArchivematicaAmaUatsError(
            f"Transfer status did not include a directory for {transfer_uuid}: {payload!r}"
        )
    response = _post_json_or_raise(
        urljoin(instance.dashboard_url, "api/transfer/approve"),
        _dashboard_auth(instance),
        {"directory": directory, "type": "standard"},
        expected_message="Approval successful.",
    )
    approved_uuid = response.get("uuid")
    if not isinstance(approved_uuid, str) or not approved_uuid:
        raise ArchivematicaAmaUatsError(
            f"Transfer approval response missing uuid: {response!r}"
        )
    return approved_uuid


def approve_partial_reingest(
    instance: ArchivematicaInstance,
    reingest_uuid: str,
) -> str:
    deadline = time.monotonic() + instance.timeout_seconds
    payload: JsonDict | None = None
    while time.monotonic() < deadline:
        payload = get_ingest_status(instance, reingest_uuid)
        if payload is None:
            time.sleep(instance.poll_interval)
            continue
        if payload.get("status") == "USER_INPUT":
            break
        time.sleep(instance.poll_interval)
    if payload is None or payload.get("status") != "USER_INPUT":
        raise ArchivematicaAmaUatsError(
            f"Reingest {reingest_uuid} did not reach USER_INPUT for approval"
        )
    _post_json_or_raise(
        urljoin(instance.dashboard_url, "api/ingest/reingest/approve"),
        _dashboard_auth(instance),
        {"uuid": reingest_uuid},
        expected_message="Approval successful.",
    )
    approved_uuid = payload.get("uuid")
    if not isinstance(approved_uuid, str) or not approved_uuid:
        raise ArchivematicaAmaUatsError(
            f"Partial reingest approval response missing uuid: {payload!r}"
        )
    return approved_uuid


def approve_reingest(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
) -> None:
    if transfer_run.reingest_uuid is None or transfer_run.reingest_type is None:
        raise ArchivematicaAmaUatsError("No reingest has been requested")
    if transfer_run.reingest_type == "FULL":
        transfer_run.reingest_uuid = approve_transfer(
            instance, transfer_run.reingest_uuid
        )
        return
    transfer_run.reingest_uuid = approve_partial_reingest(
        instance,
        transfer_run.reingest_uuid,
    )


def wait_for_reingest_completion(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    download_root: Path | None = None,
) -> None:
    if transfer_run.reingest_uuid is None or transfer_run.reingest_type is None:
        raise ArchivematicaAmaUatsError("No reingest has been requested")
    if transfer_run.aip_mets_location is None and download_root is not None:
        download_and_extract_aip(instance, transfer_run, download_root)
    if transfer_run.reingest_type == "FULL":
        full_reingest = TransferRun(
            transfer_type="standard",
            sample_transfer_path=transfer_run.sample_transfer_path,
            transfer_name=transfer_run.transfer_name,
            transfer_source_path=transfer_run.transfer_source_path,
            transfer_uuid=transfer_run.reingest_uuid,
        )
        wait_for_transfer_completion(instance, full_reingest)
        if full_reingest.sip_uuid is None:
            raise ArchivematicaAmaUatsError(
                f"Full reingest {transfer_run.reingest_uuid} did not produce a SIP UUID"
            )
        wait_for_ingest_completion(instance, full_reingest)
        transfer_run.reingest_uuid = full_reingest.sip_uuid
    else:
        reingest_run = TransferRun(
            transfer_type="standard",
            sample_transfer_path=transfer_run.sample_transfer_path,
            transfer_name=transfer_run.transfer_name,
            transfer_source_path=transfer_run.transfer_source_path,
            transfer_uuid=transfer_run.transfer_uuid,
            sip_uuid=transfer_run.reingest_uuid,
        )
        wait_for_ingest_completion(instance, reingest_run)
        transfer_run.reingest_uuid = reingest_run.sip_uuid

    if download_root is not None:
        download_and_extract_aip(instance, transfer_run, download_root, reingested=True)


def copy_metadata_files(
    instance: ArchivematicaInstance,
    sip_uuid: str,
    relative_paths: list[str],
) -> None:
    transfer_source_uuid = get_default_transfer_source_uuid(instance)
    source_paths = []
    for path in relative_paths:
        normalized_path = str(instance.transfer_source_root / path.rstrip("/"))
        if path.endswith("/"):
            normalized_path += "/"
        source_paths.append(
            base64.b64encode(
                f"{transfer_source_uuid}:{normalized_path}".encode()
            ).decode("ascii")
        )
    url = urljoin(instance.dashboard_url, "api/ingest/copy_metadata_files/")
    deadline = time.monotonic() + instance.timeout_seconds
    last_payload: Any = None
    while time.monotonic() < deadline:
        response = requests.post(
            url,
            params=_dashboard_auth(instance),
            data=[
                ("sip_uuid", sip_uuid),
                *[("source_paths[]", value) for value in source_paths],
            ],
            timeout=30,
        )
        if response.status_code in (404, 500):
            time.sleep(instance.poll_interval)
            continue
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ArchivematicaAmaUatsError(
                f"Unexpected metadata copy response payload: {payload!r}"
            )
        last_payload = payload
        expected_message = "Metadata files added successfully."
        if payload.get("message") != expected_message:
            raise ArchivematicaAmaUatsError(
                f"Unexpected metadata copy response: {payload!r}"
            )
        return
    raise ArchivematicaAmaUatsError(
        f"Timed out copying metadata files for SIP {sip_uuid}: {last_payload!r}"
    )


def add_dummy_metadata(
    instance: ArchivematicaInstance,
    dashboard_session: requests.Session,
    sip_uuid: str,
    *,
    title: str = "Archivematica Acceptance Test",
    creator: str = "Archivematica Acceptance Test",
) -> None:
    metadata_url = urljoin(instance.dashboard_url, f"ingest/{sip_uuid}/metadata/add/")
    response = dashboard_session.get(metadata_url, timeout=30)
    response.raise_for_status()
    csrf_token = _extract_csrf_token(response.text)
    post_response = dashboard_session.post(
        metadata_url,
        data={
            "csrfmiddlewaretoken": csrf_token,
            "title": title,
            "creator": creator,
        },
        headers={
            "Referer": metadata_url,
            "X-CSRFToken": csrf_token,
        },
        timeout=30,
    )
    post_response.raise_for_status()


def download_and_extract_dip(
    instance: ArchivematicaInstance,
    transfer_run: TransferRun,
    download_root: Path,
) -> None:
    package_uuid = transfer_run.reingest_uuid or transfer_run.sip_uuid
    if package_uuid is None:
        raise ArchivematicaAmaUatsError("Cannot download a DIP before ingest completes")
    matching_dips = [
        package
        for package in list_packages(instance, {"package_type": "DIP"})
        if str(package.get("current_full_path", "")).endswith(package_uuid)
    ]
    if len(matching_dips) != 1:
        raise ArchivematicaAmaUatsError(
            f"Could not find a single DIP for {package_uuid}: {matching_dips!r}"
        )
    dip_uuid = matching_dips[0].get("uuid")
    if not isinstance(dip_uuid, str) or not dip_uuid:
        raise ArchivematicaAmaUatsError(f"Unexpected DIP payload: {matching_dips[0]!r}")
    dip_path = download_package(
        instance,
        dip_uuid,
        download_root / f"{transfer_run.transfer_name}-{dip_uuid}-dip.7z",
    )
    extracted_dip_dir = _extract_package(
        dip_path, dip_uuid, download_root, package_uuid
    )
    transfer_run.dip_path = dip_path
    transfer_run.extracted_dip_dir = extracted_dip_dir
    transfer_run.dip_mets_location = get_dip_mets_location(
        extracted_dip_dir,
        package_uuid,
    )


def download_pointer_file(
    instance: ArchivematicaInstance,
    package_uuid: str,
    destination: Path,
) -> Path:
    response = requests.get(
        _pointer_file_url(instance, package_uuid),
        params=_storage_service_auth(instance),
        stream=True,
        timeout=60,
    )
    response.raise_for_status()
    _save_stream_to_path(response, destination)
    return destination


def get_jobs(
    instance: ArchivematicaInstance,
    unit_uuid: str,
    *,
    job_name: str | None = None,
    job_link_uuid: str | None = None,
    job_microservice: str | None = None,
    detailed: bool = False,
) -> list[JsonDict]:
    params = _dashboard_auth(instance)
    if job_name is not None:
        params["name"] = job_name
    if job_link_uuid is not None:
        params["link_uuid"] = job_link_uuid
    if job_microservice is not None:
        params["microservice"] = job_microservice
    if detailed:
        params["detailed"] = "1"
    return _get_json_list(
        urljoin(instance.dashboard_url, f"api/v2beta/jobs/{unit_uuid}"),
        params,
    )


def _split_name_patterns(pattern: str) -> tuple[str, ...]:
    parts = tuple(part.strip() for part in pattern.split("|") if part.strip())
    return parts or (pattern,)


def _job_name_matches(job: JsonDict, job_name: str | None) -> bool:
    if job_name is None:
        return True
    candidates = _split_name_patterns(job_name)
    name = job.get("name")
    return isinstance(name, str) and name in candidates


def _job_microservice_matches(job: JsonDict, microservice: str | None) -> bool:
    if microservice is None:
        return True
    candidates = _split_name_patterns(microservice)
    name = job.get("microservice")
    return isinstance(name, str) and name in candidates


def wait_for_jobs_to_finish(
    instance: ArchivematicaInstance,
    unit_uuid: str,
    *,
    job_name: str | None = None,
    job_link_uuid: str | None = None,
    job_microservice: str | None = None,
    detailed: bool = False,
) -> list[JsonDict]:
    deadline = time.monotonic() + instance.timeout_seconds
    while time.monotonic() < deadline:
        jobs = get_jobs(
            instance,
            unit_uuid,
            job_name=None if "|" in (job_name or "") else job_name,
            job_link_uuid=job_link_uuid,
            job_microservice=None
            if "|" in (job_microservice or "")
            else job_microservice,
            detailed=detailed,
        )
        filtered_jobs = [
            job
            for job in jobs
            if _job_name_matches(job, job_name)
            and _job_microservice_matches(job, job_microservice)
        ]
        if filtered_jobs and all(
            str(job.get("status")) in TERMINAL_JOB_STATUSES for job in filtered_jobs
        ):
            return filtered_jobs
        time.sleep(instance.poll_interval)
    raise ArchivematicaAmaUatsError(
        f"Timed out waiting for jobs of unit {unit_uuid} "
        f"(job_name={job_name!r}, job_microservice={job_microservice!r})"
    )


def assert_jobs_completed_successfully(
    instance: ArchivematicaInstance,
    unit_uuid: str,
    *,
    job_name: str | None = None,
    job_link_uuid: str | None = None,
    job_microservice: str | None = None,
    valid_exit_codes: tuple[int, ...] = (0,),
) -> None:
    jobs = wait_for_jobs_to_finish(
        instance,
        unit_uuid,
        job_name=job_name,
        job_link_uuid=job_link_uuid,
        job_microservice=job_microservice,
        detailed=False,
    )
    if not jobs:
        raise AssertionError(f"No jobs found for unit {unit_uuid}")
    for job in jobs:
        assert job["status"] == "COMPLETE"
        for task in job["tasks"]:
            exit_code = task.get("exit_code")
            assert exit_code in valid_exit_codes


def assert_jobs_fail(
    instance: ArchivematicaInstance,
    unit_uuid: str,
    *,
    job_name: str | None = None,
    job_link_uuid: str | None = None,
    job_microservice: str | None = None,
    valid_exit_codes: tuple[int, ...] = (0,),
) -> None:
    jobs = wait_for_jobs_to_finish(
        instance,
        unit_uuid,
        job_name=job_name,
        job_link_uuid=job_link_uuid,
        job_microservice=job_microservice,
        detailed=False,
    )
    if not jobs:
        raise AssertionError(f"No jobs found for unit {unit_uuid}")
    for job in jobs:
        if job["status"] == "FAILED":
            continue
        invalid_tasks = [
            task
            for task in job["tasks"]
            if task.get("exit_code") not in valid_exit_codes
        ]
        assert invalid_tasks


def assert_microservice_executes(
    instance: ArchivematicaInstance, unit_uuid: str, microservice_name: str
) -> None:
    jobs = wait_for_jobs_to_finish(
        instance,
        unit_uuid,
        job_microservice=microservice_name,
    )
    assert jobs


def _monitor_url(instance: ArchivematicaInstance, unit_type: str) -> str:
    route = PROCESSING_MONITOR_ROUTES[unit_type]
    return str(urljoin(instance.dashboard_url, route))


def _load_monitor_statuses(
    instance: ArchivematicaInstance,
    dashboard_session: requests.Session,
    unit_type: str,
) -> list[JsonDict]:
    response = dashboard_session.get(_monitor_url(instance, unit_type), timeout=30)
    response.raise_for_status()
    payload = response.json()
    objects = payload.get("objects", [])
    if not isinstance(objects, list):
        return []
    result: list[JsonDict] = []
    for item in objects:
        if isinstance(item, dict):
            result.append(item)
    return result


def get_processing_unit(
    instance: ArchivematicaInstance,
    dashboard_session: requests.Session,
    unit_type: str,
    unit_uuid: str,
) -> JsonDict | None:
    for unit in _load_monitor_statuses(instance, dashboard_session, unit_type):
        if unit.get("uuid") == unit_uuid:
            return unit
    return None


def wait_for_processing_job(
    instance: ArchivematicaInstance,
    dashboard_session: requests.Session,
    unit_type: str,
    unit_uuid: str,
    job_name: str,
    *,
    require_choices: bool = False,
) -> JsonDict:
    names = _split_name_patterns(job_name)
    deadline = time.monotonic() + instance.timeout_seconds
    while time.monotonic() < deadline:
        unit = get_processing_unit(instance, dashboard_session, unit_type, unit_uuid)
        if unit is None:
            time.sleep(instance.poll_interval)
            continue
        jobs = unit.get("jobs", [])
        if not isinstance(jobs, list):
            time.sleep(instance.poll_interval)
            continue
        for job in jobs:
            if not isinstance(job, dict):
                continue
            current_name = job.get("type")
            if current_name not in names:
                continue
            if require_choices and not job.get("choices"):
                continue
            if require_choices:
                return job
            current_status = str(job.get("currentstep_label") or job.get("currentstep"))
            if str(job.get("currentstep_label")) in MONITOR_STATUS_LABELS.values():
                return job
            if str(job.get("currentstep")) in {"1", "2", "4"}:
                return job
            if current_status in TERMINAL_JOB_STATUSES:
                return job
        time.sleep(instance.poll_interval)
    raise ArchivematicaAmaUatsError(
        f"Timed out waiting for monitor job {job_name!r} on {unit_type} {unit_uuid}"
    )


def get_monitor_output(job: JsonDict) -> str:
    label = job.get("currentstep_label")
    if isinstance(label, str) and label:
        return label
    status = str(job.get("currentstep"))
    return MONITOR_STATUS_LABELS.get(status, status)


def execute_job_choice(
    instance: ArchivematicaInstance,
    dashboard_session: requests.Session,
    job_uuid: str,
    choice: str,
) -> None:
    csrf_token = dashboard_session.cookies.get("csrftoken", "")
    response = dashboard_session.post(
        urljoin(instance.dashboard_url, "mcp/execute/"),
        data={
            "uuid": job_uuid,
            "choice": choice,
            "csrfmiddlewaretoken": csrf_token,
        },
        headers={
            "Referer": urljoin(instance.dashboard_url, "transfer/"),
            "X-CSRFToken": csrf_token,
        },
        timeout=30,
    )
    response.raise_for_status()


def choose_processing_option(
    instance: ArchivematicaInstance,
    dashboard_session: requests.Session,
    unit_type: str,
    unit_uuid: str,
    job_name: str,
    choice_text: str,
) -> None:
    job = wait_for_processing_job(
        instance,
        dashboard_session,
        unit_type,
        unit_uuid,
        job_name,
        require_choices=True,
    )
    raw_choices = job.get("choices")
    if not isinstance(raw_choices, dict):
        raise ArchivematicaAmaUatsError(
            f"Job {job_name!r} does not expose choices: {job!r}"
        )
    normalized_expected = "".join(choice_text.lower().split())
    for code, label in raw_choices.items():
        if not isinstance(code, str) or not isinstance(label, str):
            continue
        normalized_label = "".join(label.lower().split())
        if (
            normalized_expected == normalized_label
            or normalized_expected in normalized_label
        ):
            job_uuid = job.get("uuid")
            if not isinstance(job_uuid, str) or not job_uuid:
                raise ArchivematicaAmaUatsError(
                    f"Monitor job payload missing uuid: {job!r}"
                )
            execute_job_choice(instance, dashboard_session, job_uuid, code)
            return
    raise ArchivematicaAmaUatsError(
        f"Could not find choice {choice_text!r} for monitor job {job_name!r}: {raw_choices!r}"
    )


def parse_tasks_page(
    instance: ArchivematicaInstance,
    dashboard_session: requests.Session,
    job_uuid: str,
) -> list[JsonDict]:
    tasks: list[JsonDict] = []
    page_number = 1
    while True:
        response = dashboard_session.get(
            urljoin(instance.dashboard_url, f"tasks/{job_uuid}/"),
            params={"page": str(page_number)},
            timeout=30,
        )
        response.raise_for_status()
        document = html.fromstring(response.text)
        for article in document.xpath("//article[contains(@class, 'task')]"):
            task: JsonDict = {}
            heading = article.xpath(
                ".//div[contains(@class, 'task-heading')]//h4/text()"
            )
            if heading:
                task["task_uuid"] = heading[0].replace("Task", "", 1).strip()
            for term in article.xpath(".//dl/dt"):
                key = re.sub(
                    r"[^a-z0-9]+", "_", term.text_content().strip().lower()
                ).strip("_")
                value_el = term.getnext()
                if value_el is not None:
                    task[key] = value_el.text_content().strip()
            command_text = article.xpath(
                ".//div[contains(@class, 'panel-primary')]//h3/text()"
            )
            if command_text:
                task["command"] = command_text[0].strip()
            arguments_text = article.xpath(
                ".//div[contains(@class, 'panel-primary')]//div[contains(@class, 'shell-output')]/pre/text()"
            )
            task["arguments"] = arguments_text[0].strip() if arguments_text else ""
            stdout = ""
            stderr = ""
            for panel in article.xpath(".//div[contains(@class, 'panel-info')]"):
                title = panel.xpath(".//h3/text()")
                body = panel.xpath(".//pre/text()")
                if not title or not body:
                    continue
                normalized_title = title[0].strip().lower()
                if "stdout" in normalized_title:
                    stdout = body[0].strip()
                elif "stderr" in normalized_title or "diagnostics" in normalized_title:
                    stderr = body[0].strip()
            task["stdout"] = stdout
            task["stderr"] = stderr
            tasks.append(task)
        next_page = document.xpath(
            "//a[contains(@class, 'btn') and normalize-space(text())='Next page']"
        )
        if not next_page:
            return tasks
        page_number += 1


def get_job_details(
    instance: ArchivematicaInstance,
    dashboard_session: requests.Session,
    unit_uuid: str,
    *,
    unit_type: str = "transfer",
    job_name: str,
) -> JsonDict:
    monitor_job = wait_for_processing_job(
        instance,
        dashboard_session,
        unit_type,
        unit_uuid,
        job_name,
    )
    job_uuid = monitor_job.get("uuid")
    if not isinstance(job_uuid, str) or not job_uuid:
        raise ArchivematicaAmaUatsError(
            f"Monitor job payload missing uuid for {job_name!r}: {monitor_job!r}"
        )
    return {
        "job_output": get_monitor_output(monitor_job),
        "tasks": {
            str(task["task_uuid"]): task
            for task in parse_tasks_page(instance, dashboard_session, job_uuid)
        },
    }


def get_normalization_report(
    instance: ArchivematicaInstance,
    dashboard_session: requests.Session,
    sip_uuid: str,
) -> list[JsonDict]:
    response = dashboard_session.get(
        urljoin(instance.dashboard_url, f"ingest/normalization-report/{sip_uuid}/"),
        timeout=30,
    )
    response.raise_for_status()
    document = html.fromstring(response.text)
    table = document.xpath("//table")[0:1]
    if not table:
        raise ArchivematicaAmaUatsError(
            f"No normalization report table was found for SIP {sip_uuid}"
        )
    table_el = table[0]
    keys = [
        re.sub(r"[^a-z0-9]+", "_", value.text_content().strip().lower()).strip("_")
        for value in table_el.xpath(".//thead//th")
    ]
    rows: list[JsonDict] = []
    for row_el in table_el.xpath(".//tbody/tr"):
        cells = row_el.xpath("./td")
        row: JsonDict = {}
        for index, cell in enumerate(cells):
            if index >= len(keys):
                continue
            row[keys[index]] = cell.text_content().strip()
        if row:
            rows.append(row)
    return rows


def get_default_transfer_source_uuid(instance: ArchivematicaInstance) -> str:
    params = _storage_service_auth(instance)
    payload = _get_json(
        urljoin(instance.storage_service_url, "api/v2/location/"), params
    )
    objects = payload.get("objects")
    if not isinstance(objects, list):
        raise ArchivematicaAmaUatsError(
            f"Unexpected storage location payload: {payload!r}"
        )
    for item in objects:
        if not isinstance(item, dict):
            continue
        if (
            item.get("description") == "Default transfer source"
            and item.get("enabled") is True
            and str(item.get("relative_path", "")).endswith("home")
            and item.get("purpose") == "TS"
        ):
            uuid = item.get("uuid")
            if isinstance(uuid, str) and uuid:
                return uuid
    raise ArchivematicaAmaUatsError("Could not locate the default transfer source")


def wait_for_aip_to_appear_in_archival_storage(
    instance: ArchivematicaInstance,
    package_uuid: str,
) -> None:
    deadline = time.monotonic() + instance.timeout_seconds
    while time.monotonic() < deadline:
        package = get_package_or_none(instance, package_uuid)
        if package is not None and package.get("package_type") == "AIP":
            return
        time.sleep(instance.poll_interval)
    raise ArchivematicaAmaUatsError(
        f"Timed out waiting for AIP {package_uuid} to appear in archival storage"
    )


def search_archival_storage(
    instance: ArchivematicaInstance,
    dashboard_session: requests.Session,
    *,
    aip_uuid: str,
    search_phrase: str,
) -> list[JsonDict]:
    response = dashboard_session.get(
        urljoin(instance.dashboard_url, "archival-storage/search/"),
        params=[
            ("query", aip_uuid),
            ("field", "AIPUUID"),
            ("fieldName", ""),
            ("type", "string"),
            ("op", "and"),
            ("query", f'"{search_phrase}"'),
            ("field", "transferMetadata"),
            ("fieldName", ""),
            ("type", "string"),
            ("returnAll", "true"),
        ],
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ArchivematicaAmaUatsError(
            f"Unexpected archival storage search payload: {payload!r}"
        )
    rows = payload.get("aaData")
    if not isinstance(rows, list):
        raise ArchivematicaAmaUatsError(
            f"Unexpected archival storage search rows: {payload!r}"
        )
    results: list[JsonDict] = []
    for row in rows:
        if isinstance(row, dict):
            results.append(row)
    return results


def wait_for_archival_storage_search_results(
    instance: ArchivematicaInstance,
    dashboard_session: requests.Session,
    *,
    aip_uuid: str,
    search_phrase: str,
    expected_count: int,
) -> list[JsonDict]:
    deadline = time.monotonic() + instance.timeout_seconds
    last_results: list[JsonDict] = []
    while time.monotonic() < deadline:
        last_results = search_archival_storage(
            instance,
            dashboard_session,
            aip_uuid=aip_uuid,
            search_phrase=search_phrase,
        )
        if len(last_results) == expected_count:
            return last_results
        time.sleep(instance.poll_interval)
    raise ArchivematicaAmaUatsError(
        "Timed out waiting for archival storage search results for "
        f"AIP {aip_uuid!r} and phrase {search_phrase!r}; expected {expected_count}, "
        f"got {len(last_results)}"
    )


def browse_default_transfer_source(
    instance: ArchivematicaInstance, browse_path: Path
) -> JsonDict:
    path = browse_path
    if browse_path.suffix:
        path = browse_path.parent
    location_uuid = get_default_transfer_source_uuid(instance)
    return _get_json(
        urljoin(
            instance.storage_service_url,
            f"api/v2/location/{location_uuid}/browse/",
        ),
        {
            **_storage_service_auth(instance),
            "path": str(path),
        },
    )


def get_metadata_csv_files(
    transfer_name: str,
    transfer_uuid: str,
    extracted_aip_dir: Path,
) -> list[JsonDict]:
    csv_path = extracted_aip_dir / "data" / "objects" / "metadata" / "metadata.csv"
    if not csv_path.exists():
        csv_path = (
            extracted_aip_dir
            / "data"
            / "objects"
            / "metadata"
            / "transfers"
            / f"{transfer_name}-{transfer_uuid}"
            / "metadata.csv"
        )
        if not csv_path.exists():
            return []
    with csv_path.open(newline="") as handle:
        reader = csv.reader(handle)
        column_names = next(reader)
        rows: list[JsonDict] = []
        for row in reader:
            row_dict: JsonDict = {}
            for index, column_name in enumerate(column_names):
                value = row[index].strip()
                existing = row_dict.get(column_name)
                if existing is None:
                    row_dict[column_name] = value
                    continue
                if isinstance(existing, list):
                    existing.append(value)
                    continue
                row_dict[column_name] = [existing, value]
            rows.append(row_dict)
        return rows


def get_source_metadata(
    transfer_name: str,
    transfer_uuid: str,
    extracted_aip_dir: Path,
) -> list[JsonDict]:
    csv_path = (
        extracted_aip_dir / "data" / "objects" / "metadata" / "source-metadata.csv"
    )
    if not csv_path.exists():
        csv_path = (
            extracted_aip_dir
            / "data"
            / "objects"
            / "metadata"
            / "transfers"
            / f"{transfer_name}-{transfer_uuid}"
            / "source-metadata.csv"
        )
        if not csv_path.exists():
            return []
    metadata_dir = csv_path.parent
    parser = etree.XMLParser(remove_blank_text=True)
    results: list[JsonDict] = []
    with csv_path.open(newline="") as handle:
        reader = csv.DictReader(
            handle,
            fieldnames=["original_filename", "metadata_filename", "type_id"],
        )
        rows = list(reader)[1:]
    for row in rows:
        result: JsonDict = dict(row)
        result["document"] = None
        metadata_filename = result.get("metadata_filename")
        if isinstance(metadata_filename, str) and metadata_filename:
            metadata_file = metadata_dir / metadata_filename
            if metadata_file.exists():
                with metadata_file.open("rb") as handle:
                    try:
                        result["document"] = etree.parse(
                            handle, parser=parser
                        ).getroot()
                    except etree.LxmlError:
                        result["document"] = None
        results.append(result)
    return results


def extract_document_text(document: Any) -> str:
    if document is None:
        return ""
    return str(etree.tostring(document, encoding="unicode", method="text").strip())


def is_metadata_validation_event(event_detail: dict[str, str]) -> bool:
    return (
        set(event_detail.keys())
        == {"type", "validation-source-type", "validation-source", "program", "version"}
        and event_detail["type"] == "metadata"
    )


def get_metadata_xml_namespaces(
    namespaces: dict[str, str],
) -> dict[str, str]:
    result = {
        "lido": "http://www.lido-schema.org",
        "marc21": "http://www.loc.gov/MARC21/slim",
        "mods": "http://www.loc.gov/mods/v3",
        "slubarchiv": "http://slubarchiv.slub-dresden.de/rights1",
        "alto": "http://www.loc.gov/standards/alto/ns-v2#",
    }
    result.update(namespaces)
    return result


XPATH_SELECTORS_BY_TAG = {
    "bag-info": "//SLUBArchiv-lzaId",
    "dc": "//dc:identifier",
    "lidoWrap": "//lido:lidoRecID",
    "record": "//marc21:leader",
    "mods": "//mods:identifier",
    "rightsRecord": "//slubarchiv:copyrightStatus",
    "alto": "//alto:softwareCreator",
}


def get_search_phrase_for_metadata_file(
    document: etree._Element,
    namespaces: dict[str, str],
) -> str | None:
    tag = etree.QName(document.tag).localname
    selector = XPATH_SELECTORS_BY_TAG.get(tag, "/")
    elements = document.xpath(selector, namespaces=namespaces)
    if elements:
        return getattr(elements[0], "text", None)
    return None
