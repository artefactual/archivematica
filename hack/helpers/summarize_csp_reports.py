import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


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


def summarize_reports(input_dir: Path) -> dict[str, Any]:
    raw_dir = input_dir / "raw"
    directive_counts: Counter[str] = Counter()
    blocked_uri_counts: Counter[str] = Counter()
    document_uri_counts: Counter[str] = Counter()
    raw_files = sorted(raw_dir.glob("*.json"))
    violation_entries = 0
    parse_failures = 0

    for report_file in raw_files:
        payload = json.loads(report_file.read_text())
        entries = extract_entries(payload.get("parsed_body"))
        if not entries:
            parse_failures += 1
            continue
        for entry in entries:
            violation_entries += 1
            directive = str(
                entry.get("effective-directive")
                or entry.get("violated-directive")
                or "unknown"
            )
            blocked_uri = str(entry.get("blocked-uri") or "unknown")
            document_uri = str(entry.get("document-uri") or "unknown")
            directive_counts[directive] += 1
            blocked_uri_counts[blocked_uri] += 1
            document_uri_counts[document_uri] += 1

    return {
        "raw_file_count": len(raw_files),
        "violation_entry_count": violation_entries,
        "parse_failure_count": parse_failures,
        "directive_counts": directive_counts.most_common(),
        "blocked_uri_counts": blocked_uri_counts.most_common(10),
        "document_uri_counts": document_uri_counts.most_common(10),
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "## CSP Reports",
        "",
        f"- Raw report files: {summary['raw_file_count']}",
        f"- Violation entries: {summary['violation_entry_count']}",
        f"- Unparsed payloads: {summary['parse_failure_count']}",
        "",
        "### Effective Directives",
    ]

    directive_counts = summary["directive_counts"]
    if directive_counts:
        lines.extend(
            f"- `{directive}`: {count}" for directive, count in directive_counts
        )
    else:
        lines.append("- None")

    lines.extend(["", "### Blocked URIs"])
    blocked_uri_counts = summary["blocked_uri_counts"]
    if blocked_uri_counts:
        lines.extend(f"- `{uri}`: {count}" for uri, count in blocked_uri_counts)
    else:
        lines.append("- None")

    lines.extend(["", "### Document URIs"])
    document_uri_counts = summary["document_uri_counts"]
    if document_uri_counts:
        lines.extend(f"- `{uri}`: {count}" for uri, count in document_uri_counts)
    else:
        lines.append("- None")

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
