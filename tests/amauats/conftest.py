import os
from pathlib import Path

import api_helpers
import browser_helpers
import pytest
from models import ArchivematicaInstance
from models import ScenarioState
from playwright.sync_api import Page
from requests import Session


def _normalize_base_url(url: str) -> str:
    return url.rstrip("/") + "/"


@pytest.fixture
def browser_context_args(
    browser_context_args: dict[str, object],
) -> dict[str, object]:
    return {
        **browser_context_args,
        "accept_downloads": True,
    }


@pytest.fixture(scope="session")
def instance() -> ArchivematicaInstance:
    return ArchivematicaInstance(
        dashboard_url=_normalize_base_url(
            os.environ.get("AMAUATS_DASHBOARD_URL", "http://nginx/")
        ),
        storage_service_url=_normalize_base_url(
            os.environ.get("AMAUATS_STORAGE_SERVICE_URL", "http://nginx:8000/")
        ),
        dashboard_username=os.environ.get("AMAUATS_DASHBOARD_USERNAME", "test"),
        dashboard_password=os.environ.get("AMAUATS_DASHBOARD_PASSWORD", "test"),
        dashboard_api_key=os.environ.get("AMAUATS_DASHBOARD_API_KEY", "test"),
        storage_service_username=os.environ.get(
            "AMAUATS_STORAGE_SERVICE_USERNAME", "test"
        ),
        storage_service_password=os.environ.get(
            "AMAUATS_STORAGE_SERVICE_PASSWORD", "test"
        ),
        storage_service_api_key=os.environ.get(
            "AMAUATS_STORAGE_SERVICE_API_KEY", "test"
        ),
        sample_data_root=Path(
            os.environ.get(
                "AMAUATS_SAMPLE_DATA_ROOT",
                "/src/hack/submodules/archivematica-sampledata",
            )
        ),
        transfer_source_root=Path(
            os.environ.get(
                "AMAUATS_TRANSFER_SOURCE_ROOT",
                "archivematica/archivematica-sampledata",
            )
        ),
        poll_interval=float(os.environ.get("AMAUATS_POLL_INTERVAL", "5")),
        timeout_seconds=float(os.environ.get("AMAUATS_TIMEOUT_SECONDS", "1800")),
    )


@pytest.fixture
def authenticated_page(page: Page, instance: ArchivematicaInstance) -> Page:
    browser_helpers.login(page, instance)
    return page


@pytest.fixture
def dashboard_session(instance: ArchivematicaInstance) -> Session:
    session: Session = api_helpers.login_dashboard_session(instance)
    return session


@pytest.fixture
def storage_service_session(instance: ArchivematicaInstance) -> Session:
    session: Session = api_helpers.login_storage_service_session(instance)
    return session


@pytest.fixture
def scenario_state() -> ScenarioState:
    return ScenarioState()


@pytest.fixture
def download_root(tmp_path: Path) -> Path:
    root = tmp_path / "amauats-downloads"
    root.mkdir()
    return root
