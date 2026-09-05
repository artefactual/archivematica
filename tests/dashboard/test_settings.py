import os
import subprocess
import sys


def test_cas_and_shibboleth_cannot_be_enabled_together() -> None:
    """The settings refuse CAS together with another single sign-on method."""
    env = {
        **os.environ,
        "ARCHIVEMATICA_DASHBOARD_DASHBOARD_SHIBBOLETH_AUTHENTICATION": "true",
        "ARCHIVEMATICA_DASHBOARD_DASHBOARD_CAS_AUTHENTICATION": "true",
    }

    result = subprocess.run(
        [sys.executable, "-c", "import archivematica.dashboard.settings.base"],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "CAS authentication is not supported in tandem" in result.stderr
