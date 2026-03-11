import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--markdown-out", type=Path, required=True)
    parser.add_argument("--json-out", type=Path, required=True)
    return parser.parse_args()


def extract_entries(parsed_body: Any) -> list[dict[str, Any]]:
    if isinstance(parsed_body, dict):
        csp_report = parsed_body.get("csp-report")
        if isinstance(csp_report, dict):
            return [csp_report]
        return [parsed_body]
    if isinstance(parsed_body, list):
        return [item for item in parsed_body if isinstance(item, dict)]
    return []


def classify_application(document_uri: str) -> str:
    parsed = urlparse(document_uri)
    hostname = parsed.hostname or ""
    port = parsed.port
    path = parsed.path or "/"

    if hostname == "nginx":
        if port == 8000:
            return "storage_service"
        return "dashboard"

    if port == 62080:
        return "dashboard"
    if port == 62081:
        return "storage_service"

    dashboard_prefixes = (
        "/transfer/",
        "/ingest/",
        "/archival-storage/",
        "/administration/",
        "/filesystem/",
        "/api/",
        "/installer/",
        "/mcp/",
        "/fpr/",
    )
    if path.startswith(dashboard_prefixes):
        return "dashboard"

    storage_service_prefixes = (
        "/locations/",
        "/spaces/",
        "/package/",
        "/administration/users/",
        "/administration/groups/",
        "/administration/tasks/",
        "/administration/processing/",
    )
    if path.startswith(storage_service_prefixes) or path in {
        "/",
        "/login/",
        "/logout/",
    }:
        return "storage_service"

    return "unknown"


def summarize_section(entries: list[dict[str, str]]) -> dict[str, Any]:
    directive_counts: Counter[str] = Counter()
    blocked_uri_counts: Counter[str] = Counter()
    document_uri_counts: Counter[str] = Counter()

    for entry in entries:
        directive_counts[entry["directive"]] += 1
        blocked_uri_counts[entry["blocked_uri"]] += 1
        document_uri_counts[entry["document_uri"]] += 1

    return {
        "violation_entry_count": len(entries),
        "directive_counts": directive_counts.most_common(),
        "blocked_uri_counts": blocked_uri_counts.most_common(10),
        "document_uri_counts": document_uri_counts.most_common(10),
    }


def summarize_reports(input_dir: Path) -> dict[str, Any]:
    raw_dir = input_dir / "raw"
    raw_files = sorted(raw_dir.glob("*.json"))
    parse_failures = 0
    entries_by_application: dict[str, list[dict[str, str]]] = {
        "dashboard": [],
        "storage_service": [],
        "unknown": [],
    }

    for report_file in raw_files:
        payload = json.loads(report_file.read_text())
        entries = extract_entries(payload.get("parsed_body"))
        if not entries:
            parse_failures += 1
            continue
        for entry in entries:
            directive = str(
                entry.get("effective-directive")
                or entry.get("violated-directive")
                or "unknown"
            )
            blocked_uri = str(entry.get("blocked-uri") or "unknown")
            document_uri = str(entry.get("document-uri") or "unknown")
            application = classify_application(document_uri)
            entries_by_application[application].append(
                {
                    "directive": directive,
                    "blocked_uri": blocked_uri,
                    "document_uri": document_uri,
                }
            )

    all_entries = [
        entry
        for application_entries in entries_by_application.values()
        for entry in application_entries
    ]

    return {
        "raw_file_count": len(raw_files),
        "parse_failure_count": parse_failures,
        "overall": summarize_section(all_entries),
        "dashboard": summarize_section(entries_by_application["dashboard"]),
        "storage_service": summarize_section(entries_by_application["storage_service"]),
        "unknown": summarize_section(entries_by_application["unknown"]),
    }


def render_section(title: str, summary: dict[str, Any]) -> list[str]:
    lines = [
        f"### {title}",
        "",
        (
            f"- Violation entries: {summary['violation_entry_count']}"
            " (CSP violations attributed to this application)"
        ),
        "",
        "#### Effective Directives",
        "Counts by CSP directive reported by the browser as violated.",
    ]

    directive_counts = summary["directive_counts"]
    if directive_counts:
        lines.extend(
            f"- `{directive}`: {count}" for directive, count in directive_counts
        )
    else:
        lines.append("- None")

    lines.extend(["", "#### Blocked URIs", "What source or value the browser blocked."])
    blocked_uri_counts = summary["blocked_uri_counts"]
    if blocked_uri_counts:
        lines.extend(f"- `{uri}`: {count}" for uri, count in blocked_uri_counts)
    else:
        lines.append("- None")

    lines.extend(
        ["", "#### Document URIs", "Which pages emitted the violation reports."]
    )
    document_uri_counts = summary["document_uri_counts"]
    if document_uri_counts:
        lines.extend(f"- `{uri}`: {count}" for uri, count in document_uri_counts)
    else:
        lines.append("- None")

    return lines


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "## CSP Reports",
        "",
        (
            f"- Raw report files: {summary['raw_file_count']}"
            " (JSON report files captured by the receiver)"
        ),
        (
            f"- Violation entries: {summary['overall']['violation_entry_count']}"
            " (total CSP violations extracted from those files)"
        ),
        (
            f"- Unparsed payloads: {summary['parse_failure_count']}"
            " (raw report files that did not produce any parsed violation entries)"
        ),
        "",
    ]

    lines.extend(render_section("Dashboard", summary["dashboard"]))
    lines.extend([""])
    lines.extend(render_section("Storage Service", summary["storage_service"]))

    if summary["unknown"]["violation_entry_count"]:
        lines.extend([""])
        lines.extend(render_section("Unknown", summary["unknown"]))

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    args.input_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_reports(args.input_dir)
    args.markdown_out.write_text(render_markdown(summary))
    args.json_out.write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
