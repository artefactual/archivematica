import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import api_helpers
from lxml import html
from models import ArchivematicaInstance
from requests import Response
from requests import Session

JsonDict = dict[str, Any]

POLICY_CHECK_CMD_TEMPLATE = """
import sys
from ammcpc import MediaConchPolicyCheckerCommand

# Valuate this constant with the text (XML) of the policy.
POLICY = \"\"\"
\"\"\".strip()

# Valuate this constant with the name of the policy.
POLICY_NAME = ''

if __name__ == '__main__':
    target = sys.argv[1]
    policy_checker = MediaConchPolicyCheckerCommand(
        policy=POLICY,
        policy_file_name=POLICY_NAME)
    sys.exit(policy_checker.check(target))
""".strip()


def _normalize_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _policy_root() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "hack"
        / "submodules"
        / "archivematica-acceptance-tests"
        / "etc"
        / "mediaconch-policies"
    )


def get_policy_file_path(policy_file: str) -> Path:
    return _policy_root() / policy_file


def _get_document(response: Response) -> html.HtmlElement:
    response.raise_for_status()
    return html.fromstring(response.text)


def _dashboard_get(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    path: str,
) -> html.HtmlElement:
    response = dashboard_session.get(urljoin(instance.dashboard_url, path), timeout=30)
    return _get_document(response)


def _csrf_token(document: html.HtmlElement) -> str:
    tokens = document.xpath('//input[@name="csrfmiddlewaretoken"]/@value')
    if not tokens:
        raise api_helpers.ArchivematicaAmaUatsError(
            "Missing CSRF token in dashboard form"
        )
    return str(tokens[0])


def _get_json_script(document: html.HtmlElement, *, prefix: str) -> JsonDict:
    scripts = document.xpath(f'//script[starts-with(@id, "{prefix}")]/text()')
    if not scripts:
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Could not find embedded JSON payload with prefix {prefix!r}"
        )
    payload = json.loads(scripts[0])
    if not isinstance(payload, dict):
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Unexpected embedded payload for {prefix!r}: {payload!r}"
        )
    return payload


def _select_option_value(
    document: html.HtmlElement,
    select_name: str,
    label_text: str,
) -> str:
    expected = _normalize_label(label_text)
    options = document.xpath(f'//select[@name="{select_name}"]/option')
    for option in options:
        option_text = " ".join(option.text_content().split())
        normalized_option = _normalize_label(option_text)
        if expected == normalized_option or expected in normalized_option:
            value = option.get("value", "")
            if value:
                return str(value)
    raise api_helpers.ArchivematicaAmaUatsError(
        f"Could not find option {label_text!r} for select {select_name!r}"
    )


def _toggle_rule_or_command(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    *,
    category: str,
    uuid: str,
) -> None:
    response = dashboard_session.get(
        urljoin(instance.dashboard_url, f"fpr/{category}/{uuid}/toggle_enabled/"),
        timeout=30,
        allow_redirects=True,
    )
    response.raise_for_status()


def list_fpr_rules(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
) -> list[JsonDict]:
    document = _dashboard_get(instance, dashboard_session, "fpr/fprule/")
    payload = _get_json_script(document, prefix="fpr-fprule-")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Unexpected FPR rules payload: {payload!r}"
        )
    return [row for row in rows if isinstance(row, dict)]


def list_fp_commands(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    *,
    usage: str = "validation",
) -> list[JsonDict]:
    document = _dashboard_get(instance, dashboard_session, f"fpr/fpcommand/{usage}/")
    payload = _get_json_script(document, prefix="fpr-fpcommand-")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Unexpected FP command payload: {payload!r}"
        )
    return [row for row in rows if isinstance(row, dict)]


def get_policy_command_description(policy_file: str) -> str:
    return f"Check against policy {policy_file} using MediaConch"


def _build_policy_check_command(policy_file: str, policy_path: Path) -> str:
    policy_lines = policy_path.read_text(encoding="utf8").splitlines()
    result: list[str] = []
    for line in POLICY_CHECK_CMD_TEMPLATE.splitlines():
        stripped = line.strip()
        if stripped.startswith('POLICY = """'):
            result.append(line)
            result.extend(policy_lines)
        elif stripped == "POLICY_NAME = ''":
            result.append(f"POLICY_NAME = '{policy_file}'")
        else:
            result.append(line)
    return "\n".join(result)


def _find_matching_rule(
    rules: list[JsonDict],
    *,
    purpose: str,
    format_label: str,
    command_description: str | None = None,
) -> JsonDict | None:
    expected_purpose = _normalize_label(purpose)
    expected_format = _normalize_label(format_label)
    expected_command = (
        _normalize_label(command_description)
        if command_description is not None
        else None
    )
    for rule in rules:
        current_purpose = rule.get("purpose")
        current_format = rule.get("format")
        current_command = rule.get("command")
        if not isinstance(current_purpose, str) or not isinstance(current_format, str):
            continue
        if _normalize_label(current_purpose) != expected_purpose:
            continue
        if _normalize_label(current_format) != expected_format:
            continue
        if expected_command is not None:
            if not isinstance(current_command, str):
                continue
            if _normalize_label(current_command) != expected_command:
                continue
        return rule
    return None


def ensure_fpr_policy_check_command(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    policy_file: str,
) -> None:
    description = get_policy_command_description(policy_file)
    existing = next(
        (
            row
            for row in list_fp_commands(instance, dashboard_session)
            if isinstance(row.get("description"), str)
            and row["description"] == description
        ),
        None,
    )
    if existing is not None:
        if existing.get("enabled") is False:
            uuid = existing.get("id")
            if isinstance(uuid, str):
                _toggle_rule_or_command(
                    instance,
                    dashboard_session,
                    category="fpcommand",
                    uuid=uuid,
                )
        return

    policy_path = get_policy_file_path(policy_file)
    if not policy_path.is_file():
        raise api_helpers.ArchivematicaAmaUatsError(
            f"MediaConch policy file does not exist: {policy_path}"
        )

    document = _dashboard_get(instance, dashboard_session, "fpr/fpcommand/create/")
    data = {
        "csrfmiddlewaretoken": _csrf_token(document),
        "tool": _select_option_value(document, "tool", "MediaConch"),
        "description": description,
        "command": _build_policy_check_command(policy_file, policy_path),
        "script_type": _select_option_value(document, "script_type", "Python script"),
        "output_format": "",
        "output_location": "",
        "command_usage": _select_option_value(document, "command_usage", "Validation"),
        "verification_command": "",
        "event_detail_command": "",
    }
    response = dashboard_session.post(
        urljoin(instance.dashboard_url, "fpr/fpcommand/create/"),
        data=data,
        headers={"Referer": urljoin(instance.dashboard_url, "fpr/fpcommand/create/")},
        timeout=30,
        allow_redirects=True,
    )
    response.raise_for_status()
    created = next(
        (
            row
            for row in list_fp_commands(instance, dashboard_session)
            if isinstance(row.get("description"), str)
            and row["description"] == description
        ),
        None,
    )
    if created is None:
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Could not create FP command for policy {policy_file}: {response.url}"
        )


def ensure_fpr_rule(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    *,
    purpose: str,
    format_label: str,
    command_description: str,
) -> None:
    document = _dashboard_get(instance, dashboard_session, "fpr/fprule/create/")
    purpose_value = _select_option_value(document, "f-purpose", purpose)
    rules = list_fpr_rules(instance, dashboard_session)
    existing = _find_matching_rule(
        rules,
        purpose=purpose_value,
        format_label=format_label,
        command_description=command_description,
    )
    if existing is not None:
        if existing.get("enabled") is False:
            uuid = existing.get("id")
            if isinstance(uuid, str):
                _toggle_rule_or_command(
                    instance,
                    dashboard_session,
                    category="fprule",
                    uuid=uuid,
                )
        return

    data = {
        "csrfmiddlewaretoken": _csrf_token(document),
        "f-purpose": purpose_value,
        "f-format": _select_option_value(document, "f-format", format_label),
        "f-command": _select_option_value(document, "f-command", command_description),
    }
    response = dashboard_session.post(
        urljoin(instance.dashboard_url, "fpr/fprule/create/"),
        data=data,
        headers={"Referer": urljoin(instance.dashboard_url, "fpr/fprule/create/")},
        timeout=30,
        allow_redirects=True,
    )
    response.raise_for_status()
    created = _find_matching_rule(
        list_fpr_rules(instance, dashboard_session),
        purpose=purpose_value,
        format_label=format_label,
        command_description=command_description,
    )
    if created is None:
        raise api_helpers.ArchivematicaAmaUatsError(
            "Could not create the requested FPR rule"
        )


def ensure_fpr_rule_enabled(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    *,
    purpose: str,
    format_label: str,
    command_description: str,
) -> None:
    ensure_fpr_rule(
        instance,
        dashboard_session,
        purpose=purpose,
        format_label=format_label,
        command_description=command_description,
    )


def change_normalization_rule_command(
    instance: ArchivematicaInstance,
    dashboard_session: Session,
    *,
    purpose: str,
    format_label: str,
    command_description: str,
) -> None:
    document = _dashboard_get(instance, dashboard_session, "fpr/fprule/create/")
    purpose_value = _select_option_value(document, "f-purpose", purpose)
    rules = list_fpr_rules(instance, dashboard_session)
    matching_rule = _find_matching_rule(
        rules,
        purpose=purpose_value,
        format_label=format_label,
        command_description=command_description,
    )
    if matching_rule is not None and matching_rule.get("enabled") is True:
        return

    current_rule = _find_matching_rule(
        rules,
        purpose=purpose_value,
        format_label=format_label,
    )
    if current_rule is None:
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Could not locate an existing FPR rule for {purpose!r} / {format_label!r}"
        )
    rule_uuid = current_rule.get("id")
    if not isinstance(rule_uuid, str):
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Unexpected FPR rule payload: {current_rule!r}"
        )

    document = _dashboard_get(
        instance,
        dashboard_session,
        f"fpr/fprule/{rule_uuid}/edit/",
    )
    data = {
        "csrfmiddlewaretoken": _csrf_token(document),
        "f-purpose": _select_option_value(document, "f-purpose", purpose),
        "f-format": _select_option_value(document, "f-format", format_label),
        "f-command": _select_option_value(document, "f-command", command_description),
    }
    response = dashboard_session.post(
        urljoin(instance.dashboard_url, f"fpr/fprule/{rule_uuid}/edit/"),
        data=data,
        headers={
            "Referer": urljoin(instance.dashboard_url, f"fpr/fprule/{rule_uuid}/edit/")
        },
        timeout=30,
        allow_redirects=True,
    )
    response.raise_for_status()
    updated_rule = _find_matching_rule(
        list_fpr_rules(instance, dashboard_session),
        purpose=purpose_value,
        format_label=format_label,
        command_description=command_description,
    )
    if updated_rule is None or updated_rule.get("enabled") is not True:
        raise api_helpers.ArchivematicaAmaUatsError(
            f"Failed to replace FPR rule for {purpose!r} / {format_label!r}"
        )
