from csp.constants import NONCE
from csp.constants import NONE
from csp.constants import REPORT_SAMPLE
from csp.constants import SELF
from csp.constants import STRICT_DYNAMIC

from archivematica.dashboard.settings.components.csp import (
    build_content_security_policy,
)


def test_build_content_security_policy_uses_nonce_enforced_defaults():
    assert build_content_security_policy() == {
        "DIRECTIVES": {
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
        }
    }


def test_build_content_security_policy_adds_report_uri():
    assert build_content_security_policy("https://example.com/csp-report/") == {
        "DIRECTIVES": {
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
            "report-uri": "https://example.com/csp-report/",
        }
    }
