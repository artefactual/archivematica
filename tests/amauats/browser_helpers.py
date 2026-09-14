import re
import time
import uuid
from pathlib import PurePosixPath
from urllib.parse import urljoin

from models import ArchivematicaInstance
from models import TransferRun
from playwright.sync_api import Locator
from playwright.sync_api import Page
from playwright.sync_api import expect

TRANSFER_SOURCE_PREFIX = ("archivematica", "archivematica-sampledata")


class BrowserFlowError(Exception):
    pass


def login(page: Page, instance: ArchivematicaInstance) -> None:
    page.goto(urljoin(instance.dashboard_url, "transfer/"))
    if "/administration/accounts/login" in page.url:
        page.get_by_label("Username").fill(instance.dashboard_username)
        page.get_by_label("Password").fill(instance.dashboard_password)
        page.get_by_role("button", name="Log in").click()
        page.wait_for_load_state("networkidle")
        expect(page).not_to_have_url(
            re.compile(r".*/administration/accounts/login/?$"), timeout=30_000
        )
    if not re.search(r".*/transfer/?$", page.url):
        page.goto(urljoin(instance.dashboard_url, "transfer/"))
    expect(page).to_have_url(re.compile(r".*/transfer/?$"), timeout=30_000)


def login_storage_service(page: Page, instance: ArchivematicaInstance) -> None:
    page.goto(instance.storage_service_url)
    if "/login" in page.url:
        page.get_by_label("Username").fill(instance.storage_service_username)
        page.get_by_label("Password").fill(instance.storage_service_password)
        page.get_by_role("button", name="Log in").click()
        page.wait_for_load_state("networkidle")
    expect(page).not_to_have_url(re.compile(r".*/login/?$"), timeout=30_000)


def _tree_item(page: Page, segment: str) -> Locator:
    pattern = re.compile(rf"^{re.escape(segment)}(?:$|\s|\()")
    return page.get_by_role("treeitem", name=pattern).first


def _sanitize_tree_node_id(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_-]+", "-", value)
    sanitized = re.sub(r"-+", "-", sanitized).strip("-")
    if not sanitized:
        raise BrowserFlowError(f"Could not build a tree node id from {value!r}")
    return sanitized


def _tree_item_by_path(page: Page, path_segments: tuple[str, ...]) -> Locator:
    path = "/".join(path_segments)
    node_id = _sanitize_tree_node_id(path)
    return page.locator(f"#tree-node-{node_id}").first


def _wait_for_tree_item(
    page: Page, path_segments: tuple[str, ...], timeout_ms: float = 30_000
) -> Locator:
    item = _tree_item_by_path(page, path_segments)
    expect(item).to_be_visible(timeout=timeout_ms)
    return item


def _expand_tree_item(
    page: Page,
    item: Locator,
    next_item: Locator,
    timeout_seconds: float = 30.0,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if item.get_attribute("aria-expanded") == "true":
            if next_item.count() > 0 and next_item.first.is_visible():
                return
        item.locator(":scope > .tree-node-content").click()
        if item.get_attribute("aria-expanded") != "true":
            item.focus()
            page.keyboard.press("ArrowRight")
        page.wait_for_timeout(250)
        if item.get_attribute("aria-expanded") == "true":
            if next_item.count() > 0 and next_item.first.is_visible():
                return
    expect(next_item).to_be_visible(timeout=1_000)


def _ensure_source_location_selected(page: Page) -> None:
    location_select = page.locator("#source-location-select")
    expect(location_select).to_be_visible()
    current_value = location_select.input_value()
    if current_value:
        return
    first_option_value = location_select.locator("option").first.get_attribute("value")
    if first_option_value is None:
        raise BrowserFlowError("No transfer source locations are available")
    location_select.select_option(first_option_value)


def _add_transfer_path(page: Page, sample_transfer_path: str) -> None:
    _ensure_source_location_selected(page)
    segments = [*TRANSFER_SOURCE_PREFIX, *PurePosixPath(sample_transfer_path).parts]
    for index, _segment in enumerate(segments):
        current_path = tuple(segments[: index + 1])
        item = _wait_for_tree_item(page, current_path)
        item.locator(":scope > .tree-node-content").click()
        if index == len(segments) - 1:
            add_button = page.get_by_role("button", name="Add")
            expect(add_button).to_be_enabled()
            add_button.click()
            return
        next_path = tuple(segments[: index + 2])
        _expand_tree_item(page, item, _tree_item_by_path(page, next_path))


def open_processing_configuration_editor(
    page: Page,
    instance: ArchivematicaInstance,
    name: str = "default",
) -> None:
    login(page, instance)
    page.goto(
        urljoin(instance.dashboard_url, f"administration/processing/edit/{name}/")
    )
    expect(page.get_by_role("heading", name="Processing configuration")).to_be_visible()


def reset_processing_configuration(
    page: Page,
    instance: ArchivematicaInstance,
    name: str = "default",
) -> None:
    login(page, instance)
    page.goto(
        urljoin(instance.dashboard_url, f"administration/processing/reset/{name}/")
    )
    expect(page).to_have_url(re.compile(r".*/administration/processing/?$"))


def set_processing_config_decision(
    page: Page,
    decision_label: str,
    choice_value: str,
) -> bool:
    label = page.locator(
        "label", has_text=re.compile(re.escape(decision_label), re.I)
    ).first
    if label.count() == 0:
        return False
    expect(label).to_be_visible()
    field_id = label.get_attribute("for")
    if field_id is None:
        raise BrowserFlowError(
            f'Unable to determine field id for processing decision "{decision_label}"'
        )
    field = page.locator(f"#{field_id}")
    tag_name = field.evaluate("element => element.tagName.toLowerCase()")
    if not isinstance(tag_name, str):
        raise BrowserFlowError(
            f'Unable to determine tag name for processing decision "{decision_label}"'
        )
    if tag_name == "select":
        field.select_option(label=choice_value)
        return True
    field.fill(choice_value)
    return True


def save_processing_configuration(page: Page) -> None:
    page.get_by_role("button", name="Save").click()
    expect(page).to_have_url(re.compile(r".*/administration/processing/?$"))


def configure_processing_choices(
    page: Page,
    instance: ArchivematicaInstance,
    decisions: dict[str, str],
    *,
    name: str = "default",
    optional_labels: set[str] | None = None,
    reset: bool = True,
) -> None:
    if reset:
        reset_processing_configuration(page, instance, name)
    open_processing_configuration_editor(page, instance, name)
    for decision_label, choice_value in decisions.items():
        configured = set_processing_config_decision(page, decision_label, choice_value)
        if not configured and (
            optional_labels is None or decision_label not in optional_labels
        ):
            raise BrowserFlowError(
                f'Unable to locate processing decision "{decision_label}"'
            )
    save_processing_configuration(page)


def _start_with_processing_configuration(
    page: Page, processing_config_name: str
) -> None:
    if processing_config_name == "default":
        start_button = page.locator(".btn-group.dropdown button.btn-success").first
        expect(start_button).to_be_enabled()
        start_button.click()
        return
    page.get_by_role("button", name="Show processing configuration options").click()
    page.get_by_role(
        "menuitem",
        name=f'Start with "{processing_config_name}" configuration',
    ).click()


def start_transfer_via_ui(
    page: Page,
    instance: ArchivematicaInstance,
    transfer_type: str,
    sample_transfer_path: str,
    *,
    processing_config_name: str = "default",
    transfer_name: str | None = None,
) -> TransferRun:
    login(page, instance)
    page.goto(urljoin(instance.dashboard_url, "transfer/"))
    expect(page.get_by_role("button", name="Browse")).to_be_visible()

    resolved_transfer_name = (
        transfer_name or f"amauats-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    )
    page.locator("#transfer-type").select_option(transfer_type)
    transfer_name_input = page.locator("#transfer-name")
    transfer_name_input_is_visible = (
        transfer_name_input.count() > 0 and transfer_name_input.is_visible()
    )
    if transfer_name_input_is_visible:
        transfer_name_input.fill(resolved_transfer_name)
    else:
        transfer_path = PurePosixPath(sample_transfer_path)
        resolved_transfer_name = (
            transfer_path.stem if transfer_path.suffix else transfer_path.name
        )
    page.get_by_role("button", name="Browse").click()
    _add_transfer_path(page, sample_transfer_path)

    with page.expect_response(
        lambda response: (
            response.request.method == "POST"
            and response.url.endswith("/api/v2beta/package/")
        )
    ) as response_info:
        _start_with_processing_configuration(page, processing_config_name)

    response = response_info.value
    if response.status != 202:
        raise BrowserFlowError(
            f"Unexpected transfer creation response: {response.status} {response.text()}"
        )
    payload = response.json()
    transfer_uuid = payload.get("id")
    if not isinstance(transfer_uuid, str) or not transfer_uuid:
        raise BrowserFlowError(f"Transfer creation payload missing id: {payload}")
    success_alert = page.locator(".alert-info")
    expect(success_alert).to_be_visible()
    if transfer_name_input_is_visible:
        expect(success_alert).to_contain_text(resolved_transfer_name)

    return TransferRun(
        transfer_type=transfer_type,
        sample_transfer_path=sample_transfer_path,
        transfer_name=resolved_transfer_name,
        transfer_source_path=instance.sample_data_root / sample_transfer_path,
        transfer_uuid=transfer_uuid,
        processing_config=processing_config_name,
    )


def add_dummy_metadata(
    page: Page,
    instance: ArchivematicaInstance,
    sip_uuid: str,
    *,
    value: str = "Archivematica Acceptance Test",
) -> None:
    login(page, instance)
    page.goto(urljoin(instance.dashboard_url, f"ingest/{sip_uuid}/metadata/add/"))
    expect(page.locator("#id_title")).to_be_visible()
    page.locator("#id_title").fill(value)
    page.locator("#id_creator").fill(value)
    submit = page.locator("input[value='Create'], input[value='Save']").first
    expect(submit).to_be_visible()
    submit.click()
    page.wait_for_load_state("networkidle")
