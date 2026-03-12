import os

from csp.constants import NONCE
from csp.constants import NONE
from csp.constants import REPORT_SAMPLE
from csp.constants import SELF
from csp.constants import STRICT_DYNAMIC

REPORT_URI = os.environ.get(
    "CSP_REPORT_URI",
    "http://nginx/api/csp-report/",
)

CONTENT_SECURITY_POLICY_REPORT_ONLY = {
    "DIRECTIVES": {
        "default-src": [NONE],
        "script-src": [NONCE, STRICT_DYNAMIC, SELF, REPORT_SAMPLE],
        "style-src": [SELF],
        "img-src": [SELF],
        "font-src": [SELF, "data:"],
        "connect-src": [SELF],
        "object-src": [NONE],
        "base-uri": [SELF],
        "form-action": [SELF],
        "frame-ancestors": [NONE],
        "report-uri": REPORT_URI,
    }
}
