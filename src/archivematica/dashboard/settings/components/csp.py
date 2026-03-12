import os
from typing import Any

from csp.constants import NONCE
from csp.constants import NONE
from csp.constants import REPORT_SAMPLE
from csp.constants import SELF
from csp.constants import STRICT_DYNAMIC


def build_content_security_policy(
    report_uri: str | None = None,
) -> dict[str, dict[str, Any]]:
    directives: dict[str, Any] = {
        "default-src": [NONE],
        "script-src": [NONCE, STRICT_DYNAMIC, REPORT_SAMPLE],
        "style-src": [SELF],
        "img-src": [SELF, "data:"],
        "font-src": [SELF, "data:"],
        "connect-src": [SELF],
        "object-src": [NONE],
        "base-uri": [SELF],
        "form-action": [SELF],
        "frame-ancestors": [NONE],
        "require-trusted-types-for": ["'script'"],
    }
    if report_uri:
        directives["report-uri"] = report_uri
    return {"DIRECTIVES": directives}


CONTENT_SECURITY_POLICY = build_content_security_policy(
    report_uri=os.environ.get("CSP_REPORT_URI") or None,
)
