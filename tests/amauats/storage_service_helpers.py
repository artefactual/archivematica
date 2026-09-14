import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import api_helpers
from lxml import html
from models import ArchivematicaInstance
from requests import Response
from requests import Session

JsonDict = dict[str, Any]

STANDARD_GPG_SPACE_PATH = "/"
STANDARD_GPG_STAGING_PATH = (
    "/var/archivematica/storage_service/storage_service_encrypted"
)
STANDARD_GPG_LOCATION_PATH = "var/archivematica/sharedDirectory/www/AIPsStoreEncrypted"
STANDARD_GPG_REPLICATOR_PATH = "var/archivematica/sharedDirectory/www/EncryptedReplicas"
PASSPHRASELESS_KEY_ID = "AAC5E07B370A2D9A"
PASSPHRASED_KEY_ID = "0F86C799E5DEDE22"


def _gpg_key_root() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "hack"
        / "submodules"
        / "archivematica-acceptance-tests"
        / "etc"
        / "gpgkeys"
    )


def get_gpg_key_path(key_name: str) -> Path:
    return _gpg_key_root() / key_name


def get_standard_gpg_location_description(space_uuid: str) -> str:
    return f"Store AIP Encrypted in standard Archivematica Directory ({space_uuid})"


def _get_document(response: Response) -> html.HtmlElement:
    response.raise_for_status()
    return html.fromstring(response.text)


def _storage_get(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    path: str,
) -> html.HtmlElement:
    response = storage_service_session.get(
        urljoin(instance.storage_service_url, path),
        timeout=30,
    )
    return _get_document(response)


def _csrf_token(document: html.HtmlElement) -> str:
    tokens = document.xpath('//input[@name="csrfmiddlewaretoken"]/@value')
    if not tokens:
        raise api_helpers.ArchivematicaAmaUatsError(
            "Missing CSRF token in storage service form"
        )
    return str(tokens[0])


def _get_json_script(document: html.HtmlElement, script_id: str) -> JsonDict:
    texts = document.xpath(f'//script[@id="{script_id}"]/text()')
    if not texts:
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Could not locate JSON payload {script_id!r}"
        )
    payload = json.loads(texts[0])
    if not isinstance(payload, dict):
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Unexpected JSON payload in {script_id!r}: {payload!r}"
        )
    return payload


def _message_text(document: html.HtmlElement) -> str:
    messages = [
        " ".join(node.text_content().split())
        for node in document.xpath(
            '//div[contains(@class, "alert-success") or contains(@class, "alert-error") or contains(@class, "alert-warning")]'
        )
    ]
    return " ".join(message for message in messages if message)


def _prompt_text(document: html.HtmlElement) -> str:
    prompts = [" ".join(node.text_content().split()) for node in document.xpath("//p")]
    return " ".join(prompt for prompt in prompts if prompt)


def _selected_values(select: html.HtmlElement) -> list[str]:
    selected = select.xpath(".//option[@selected]/@value")
    if selected:
        return [str(value) for value in selected if str(value)]
    if select.get("multiple") is not None:
        return []
    first_value = select.xpath("./option[1]/@value")
    return [str(first_value[0])] if first_value and str(first_value[0]) else []


def _build_form_payload(document: html.HtmlElement) -> dict[str, str | list[str]]:
    payload: dict[str, str | list[str]] = {}
    for element in document.xpath(
        "//input[@name] | //textarea[@name] | //select[@name]"
    ):
        name = element.get("name")
        if not name:
            continue
        if element.tag == "select":
            values = _selected_values(element)
            if element.get("multiple") is not None:
                payload[name] = values
            else:
                payload[name] = values[0] if values else ""
            continue
        if element.tag == "textarea":
            payload[name] = element.text or ""
            continue
        input_type = element.get("type", "text")
        if input_type in {"submit", "button"}:
            continue
        if input_type == "checkbox":
            if element.get("checked") is not None:
                payload[name] = element.get("value") or "on"
            continue
        payload[name] = element.get("value") or ""
    return payload


def list_gpg_keys(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
) -> list[JsonDict]:
    document = _storage_get(instance, storage_service_session, "administration/keys/")
    payload = _get_json_script(document, "tables-keys-table-payload")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Unexpected GPG key payload: {payload!r}"
        )
    results: list[JsonDict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        keyid = row.get("keyid")
        row_copy = dict(row)
        if isinstance(keyid, dict):
            row_copy["keyid_text"] = keyid.get("text")
            row_copy["keyid_href"] = keyid.get("href")
        results.append(row_copy)
    return results


def get_default_gpg_key(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
) -> JsonDict:
    keys = list_gpg_keys(instance, storage_service_session)
    for key in keys:
        keyid = key.get("keyid_text")
        if not isinstance(keyid, str):
            continue
        if keyid not in {PASSPHRASELESS_KEY_ID, PASSPHRASED_KEY_ID}:
            return key
    if keys:
        return keys[0]
    raise api_helpers.ArchivematicaAmaUatsError("No GPG keys are available")


def import_gpg_key(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    key_path: Path,
) -> str:
    document = _storage_get(
        instance, storage_service_session, "administration/keys/import/"
    )
    response = storage_service_session.post(
        urljoin(instance.storage_service_url, "administration/keys/import/"),
        data={
            "csrfmiddlewaretoken": _csrf_token(document),
            "ascii_armor": key_path.read_text(encoding="utf8"),
        },
        headers={
            "Referer": urljoin(
                instance.storage_service_url, "administration/keys/import/"
            )
        },
        timeout=30,
        allow_redirects=True,
    )
    page = _get_document(response)
    return _message_text(page)


def create_gpg_key(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    *,
    name_real: str,
    name_email: str,
) -> JsonDict:
    document = _storage_get(
        instance, storage_service_session, "administration/keys/create/"
    )
    response = storage_service_session.post(
        urljoin(instance.storage_service_url, "administration/keys/create/"),
        data={
            "csrfmiddlewaretoken": _csrf_token(document),
            "name_real": name_real,
            "name_email": name_email,
        },
        headers={
            "Referer": urljoin(
                instance.storage_service_url, "administration/keys/create/"
            )
        },
        timeout=60,
        allow_redirects=True,
    )
    response.raise_for_status()
    page = _get_document(response)
    message = _message_text(page)
    if "New key" not in message:
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Could not create GPG key: {message or response.url}"
        )
    fingerprint = message.split("New key", 1)[1].split("created.", 1)[0].strip()
    keys = list_gpg_keys(instance, storage_service_session)
    matching_key = next(
        (key for key in keys if key.get("fingerprint") == fingerprint),
        None,
    )
    if matching_key is None:
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Could not locate newly created GPG key {fingerprint}"
        )
    matching_key["name_real"] = name_real
    matching_key["name_email"] = name_email
    return matching_key


def delete_gpg_key(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    fingerprint: str,
) -> tuple[bool, str]:
    document = _storage_get(
        instance,
        storage_service_session,
        f"administration/keys/{fingerprint}/delete/",
    )
    form = document.xpath("//form")[0:1]
    if not form:
        return False, _message_text(document) or _prompt_text(document)
    submit_button = document.xpath('//form//input[@type="submit"]')[0:1]
    if not submit_button:
        return False, _message_text(document) or _prompt_text(document)
    response = storage_service_session.post(
        urljoin(
            instance.storage_service_url, f"administration/keys/{fingerprint}/delete/"
        ),
        data={
            "csrfmiddlewaretoken": _csrf_token(document),
            "__confirm__": "1",
        },
        headers={
            "Referer": urljoin(
                instance.storage_service_url,
                f"administration/keys/{fingerprint}/delete/",
            )
        },
        timeout=30,
        allow_redirects=True,
    )
    page = _get_document(response)
    message = _message_text(page)
    key_still_exists = any(
        key.get("fingerprint") == fingerprint
        for key in list_gpg_keys(instance, storage_service_session)
    )
    if not key_still_exists and not message:
        message = f"GPG key {fingerprint} successfully deleted."
    return ("successfully deleted" in message.lower() or not key_still_exists, message)


def delete_gpg_key_if_exists(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    *,
    fingerprint: str | None = None,
    key_id: str | None = None,
) -> None:
    keys = list_gpg_keys(instance, storage_service_session)
    match = next(
        (
            key
            for key in keys
            if (fingerprint is not None and key.get("fingerprint") == fingerprint)
            or (key_id is not None and key.get("keyid_text") == key_id)
        ),
        None,
    )
    if match is None:
        return
    current_fingerprint = match.get("fingerprint")
    if not isinstance(current_fingerprint, str):
        return
    delete_gpg_key(instance, storage_service_session, current_fingerprint)


def ensure_standard_gpg_space(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    key_fingerprint: str,
) -> JsonDict:
    gpg_spaces = [
        space
        for space in api_helpers.list_spaces(instance, {"access_protocol": "GPG"})
        if space.get("path") == STANDARD_GPG_SPACE_PATH
        and space.get("staging_path") == STANDARD_GPG_STAGING_PATH
    ]
    if not gpg_spaces:
        created = api_helpers.create_space(
            instance,
            access_protocol="GPG",
            path=STANDARD_GPG_SPACE_PATH,
            staging_path=STANDARD_GPG_STAGING_PATH,
            extra_fields={"key": key_fingerprint},
        )
        return dict(created)

    space = gpg_spaces[0]
    if space.get("key") != key_fingerprint:
        space_uuid = space.get("uuid")
        if not isinstance(space_uuid, str):
            raise api_helpers.ArchivematicaAmaUatsError(
                f"Unexpected GPG space payload: {space!r}"
            )
        change_encrypted_space_key(
            instance,
            storage_service_session,
            space_uuid=space_uuid,
            new_key_fingerprint=key_fingerprint,
        )
        refreshed = [
            item
            for item in api_helpers.list_spaces(instance, {"access_protocol": "GPG"})
            if item.get("uuid") == space_uuid
        ]
        if refreshed:
            return dict(refreshed[0])
    return dict(space)


def ensure_storage_location(
    instance: ArchivematicaInstance,
    *,
    space_uuid: str,
    purpose: str,
    relative_path: str,
    description: str,
) -> JsonDict:
    matches = [
        location
        for location in api_helpers.list_locations(instance)
        if location.get("space") == f"/api/v2/space/{space_uuid}/"
        and location.get("purpose") == purpose
        and location.get("relative_path") == relative_path
        and location.get("description") == description
    ]
    if matches:
        return dict(matches[0])
    created = api_helpers.create_location(
        instance,
        space_resource_uri=f"/api/v2/space/{space_uuid}/",
        purpose=purpose,
        relative_path=relative_path,
        description=description,
        pipeline_resource_uris=[
            api_helpers.get_default_storage_service_pipeline_resource_uri(instance)
        ],
    )
    return dict(created)


def change_encrypted_space_key(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    *,
    space_uuid: str,
    new_key_fingerprint: str,
) -> None:
    path = f"spaces/{space_uuid}/edit/"
    document = _storage_get(instance, storage_service_session, path)
    payload = _build_form_payload(document)
    payload["csrfmiddlewaretoken"] = _csrf_token(document)
    payload["protocol-key"] = new_key_fingerprint
    response = storage_service_session.post(
        urljoin(instance.storage_service_url, path),
        data=payload,
        headers={"Referer": urljoin(instance.storage_service_url, path)},
        timeout=60,
        allow_redirects=True,
    )
    page = _get_document(response)
    message = _message_text(page)
    if "Space saved." not in message:
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Could not update GPG space {space_uuid}: {message or response.url}"
        )


def add_replicator_to_location(
    instance: ArchivematicaInstance,
    storage_service_session: Session,
    *,
    space_uuid: str,
    location_uuid: str,
    replicator_location_uuid: str,
) -> None:
    path = f"spaces/{space_uuid}/location/{location_uuid}/edit/"
    document = _storage_get(instance, storage_service_session, path)
    replicator_select = document.xpath('//select[@name="replicators"]')[0:1]
    if not replicator_select:
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Location {location_uuid} does not expose a replicators field"
        )
    desired_option = None
    for option in replicator_select[0].xpath("./option"):
        option_text = " ".join(option.text_content().split())
        if replicator_location_uuid in option_text:
            desired_option = option.get("value")
            break
    if desired_option is None:
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Could not find replicator option for {replicator_location_uuid}"
        )

    payload = _build_form_payload(document)
    payload["csrfmiddlewaretoken"] = _csrf_token(document)
    existing_values = payload.get("replicators", [])
    if isinstance(existing_values, str):
        values = [existing_values] if existing_values else []
    else:
        values = list(existing_values)
    if desired_option not in values:
        values.append(desired_option)
    payload["replicators"] = values
    response = storage_service_session.post(
        urljoin(instance.storage_service_url, path),
        data=payload,
        headers={"Referer": urljoin(instance.storage_service_url, path)},
        timeout=60,
        allow_redirects=True,
    )
    page = _get_document(response)
    message = _message_text(page)
    if "Location saved." not in message:
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Could not update location {location_uuid}: {message or response.url}"
        )


def wait_for_multiple_aips(
    instance: ArchivematicaInstance,
    *,
    aip_uuid: str,
    expected_count: int,
) -> list[JsonDict]:
    deadline = time.monotonic() + instance.timeout_seconds
    replica_uri = f"/api/v2/file/{aip_uuid}/"
    while time.monotonic() < deadline:
        packages = [
            package
            for package in api_helpers.list_packages(instance, {"package_type": "AIP"})
            if package.get("uuid") == aip_uuid
            or package.get("replicated_package") == replica_uri
        ]
        if len(packages) == expected_count:
            return packages
        time.sleep(instance.poll_interval)
    raise api_helpers.ArchivematicaAmaUatsError(
        f"Timed out waiting for {expected_count} AIP packages linked to {aip_uuid}"
    )
