from csp.constants import NONE
from csp.constants import SELF
from csp.constants import UNSAFE_EVAL
from csp.constants import UNSAFE_INLINE
from csp.constants import NONCE

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [NONE],
        "script-src": [SELF, UNSAFE_INLINE, UNSAFE_EVAL],
        "style-src": [SELF, UNSAFE_INLINE],
        "img-src": [SELF, "data:"],
        "font-src": [SELF, "data:"],
        # for preview file pane in the appraisal tab
        "frame-src": [SELF],
        # for /status
        "connect-src": [SELF],
    }
}


CONTENT_SECURITY_POLICY_REPORT_ONLY = {
    "DIRECTIVES": {
        "default-src": [NONE],
        "script-src": [SELF, NONCE],
        "style-src": [SELF, NONCE],
        "img-src": [SELF, "data:"],
        "font-src": [SELF, "data:"],
        # for preview file pane in the appraisal tab
        "frame-src": [SELF],
        # for /status
        "connect-src": [SELF],
        # Newly added directives for testing
        "form-action": [SELF],
        "frame-ancestors": [SELF],

        # "upgrade-insecure-requests": True,
        # "report-uri": "/csp-report/",
    },
}
