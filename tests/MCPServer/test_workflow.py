import importlib.resources
import pathlib
from io import StringIO
from unittest import mock

import pytest
from django.utils.translation import gettext_lazy

from archivematica.MCPServer.server import translation
from archivematica.MCPServer.server import workflow

ASSETS_DIR = importlib.resources.files("archivematica.MCPServer") / "assets"
FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"
# IDs below are durable workflow contracts shared with package bootstrap.
RETRIEVAL_CLEANUP_LINK_ID = "e781473a-0c10-431f-8ab6-5d7238b2b70b"
RETRIEVAL_MOVE_FAILED_LINK_ID = "e782473a-0c10-431f-8ab6-5d7238b2b70b"
FAILED_TERMINAL_LINK_IDS = (
    "377f8ebb-7989-4a68-9361-658079ff8138",
    "61af079f-46a2-48ff-9b8a-0c78ba3a456d",
    "828528c2-2eb9-4514-b5ca-dfd1f7cb5b8c",
    "89071669-3bb6-4e03-90a3-3c8b20c7f6fe",
    RETRIEVAL_MOVE_FAILED_LINK_ID,
    "f025f58c-d48c-4ba1-8904-a56d2a67b42f",
)
SUCCESS_TERMINAL_LINK_ID = "d5a2ef60-a757-483c-a71a-ccbffe6b80da"


@mock.patch(
    "archivematica.MCPServer.server.jobs.Job.STATUSES",
    (
        (1, gettext_lazy("Uno")),
        (2, gettext_lazy("Dos")),
        (3, gettext_lazy("Tres")),
    ),
)
def test_invert_job_statuses():
    ret = workflow._invert_job_statuses()
    assert ret == {"Uno": 1, "Dos": 2, "Tres": 3}


def test_load_invalid_document():
    blob = StringIO("""{}""")
    with pytest.raises(workflow.SchemaValidationError):
        workflow.load(blob)


def test_load_invalid_json():
    blob = StringIO("""{_}""")
    with pytest.raises(ValueError):
        workflow.load(blob)


@pytest.mark.parametrize(
    "path",
    (
        ASSETS_DIR / "workflow.json",
        FIXTURES_DIR / "workflow-sample.json",
    ),
)
def test_load_valid_document(path):
    with open(path) as fp:
        wf = workflow.load(fp)

    chains = wf.get_chains()
    assert len(chains) > 0
    first_chain = next(iter(chains.values()))
    assert isinstance(first_chain, workflow.Chain)
    assert str(first_chain) == first_chain.id
    assert repr(first_chain) == f"Chain <{first_chain.id}>"
    assert isinstance(first_chain.link, workflow.Link)
    assert isinstance(first_chain.link, workflow.BaseLink)
    assert isinstance(first_chain["description"], workflow.TranslationLabel)
    assert first_chain["description"]._src == first_chain._src["description"]._src

    links = wf.get_links()
    assert len(links) > 0
    first_link = next(iter(links.values()))
    assert repr(first_link) == f"Link <{first_link.id}>"
    assert isinstance(first_link, workflow.Link)
    assert first_link.config == first_link._src["config"]

    wdirs = wf.get_wdirs()
    assert len(wdirs) > 0
    first_wdir = wdirs[0]
    assert isinstance(first_wdir, workflow.WatchedDir)
    assert first_wdir.path == first_wdir["path"]
    assert str(first_wdir) == first_wdir["path"]
    assert repr(first_wdir) == "Watched directory <{}>".format(first_wdir["path"])
    assert isinstance(first_wdir.chain, workflow.Chain)
    assert isinstance(first_wdir.chain, workflow.BaseLink)

    # Workflow __str__ method
    assert (
        str(wf)
        == f"Chains {len(chains)}, links {len(links)}, watched directories: {len(wdirs)}"
    )

    # Test normalization of job statuses.
    link = next(iter(links.values()))
    valid_statuses = workflow._STATUSES.values()
    assert link["fallback_job_status"] in valid_statuses
    for item in link["exit_codes"].values():
        assert item["job_status"] in valid_statuses

    # Test get_label method in LinkBase.
    assert (
        first_link.get_label("description")
        == first_link._src["description"][translation.FALLBACK_LANG]
    )
    assert first_link.get_label("foobar") is None


def test_link_browse_methods(wf):
    ln = wf.get_link("1ba589db-88d1-48cf-bb1a-a5f9d2b17378")
    assert ln.get_next_link(code="0").id == "087d27be-c719-47d8-9bbb-9a7d8b609c44"
    assert ln.get_status_id(code="0") == workflow._STATUSES["Completed successfully"]
    assert ln.get_next_link(code="1").id == "7d728c39-395f-4892-8193-92f086c0546f"
    assert ln.get_status_id(code="1") == workflow._STATUSES["Failed"]


@pytest.mark.parametrize("link_id", FAILED_TERMINAL_LINK_IDS)
def test_failure_terminal_links_declare_failed_package_status(wf, link_id):
    link = wf.get_link(link_id)

    assert link.is_terminal
    assert link.package_status == workflow.TERMINAL_PACKAGE_STATUS_FAILED


def test_terminal_link_package_status_defaults_to_done(wf):
    link = wf.get_link(SUCCESS_TERMINAL_LINK_ID)

    assert link.is_terminal
    assert link.package_status == workflow.TERMINAL_PACKAGE_STATUS_DONE


def test_retrieval_failure_links_tolerate_missing_retrieval_path(wf):
    cleanup = wf.get_link(RETRIEVAL_CLEANUP_LINK_ID)
    move = wf.get_link(RETRIEVAL_MOVE_FAILED_LINK_ID)

    assert cleanup.config["arguments"].endswith("--allow-missing-path")
    assert cleanup.get_next_link(code="0") == move
    assert cleanup.get_next_link(code="1") == move
    assert move.config["arguments"].endswith("--allow-missing-source")


def test_existing_failed_transfer_move_remains_strict(wf):
    cleanup_failed_transfer = wf.get_link("e780473a-0c10-431f-bab6-5d7238b2b70b")
    move_failed_transfer = wf.get_link("377f8ebb-7989-4a68-9361-658079ff8138")

    assert "--allow-missing-path" not in cleanup_failed_transfer.config["arguments"]
    assert "--allow-missing-source" not in move_failed_transfer.config["arguments"]


def test_get_schema():
    schema = workflow._get_schema()
    assert schema["$id"] == "https://www.archivematica.org/labs/workflow/schema/v1.json"


@mock.patch(
    "archivematica.MCPServer.server.workflow._LATEST_SCHEMA", "non-existen-schema"
)
def test_get_schema_not_found():
    with pytest.raises(IOError):
        workflow._get_schema()
