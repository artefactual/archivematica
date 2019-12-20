# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os

from django.utils.six.moves import StringIO
from django.utils.six import next, itervalues
from django.utils.translation import ugettext_lazy
import pytest

from server import translation, workflow


ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir))), "lib", "assets"
)

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def test_invert_job_statuses(mocker):
    mocker.patch(
        "server.jobs.Job.STATUSES",
        (
            (1, ugettext_lazy("Uno")),
            (2, ugettext_lazy("Dos")),
            (3, ugettext_lazy("Tres")),
        ),
    )
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
        os.path.join(ASSETS_DIR, "workflow.json"),
        os.path.join(FIXTURES_DIR, "workflow-sample.json"),
    ),
)
def test_load_valid_document(path):
    with open(path) as fp:
        wf = workflow.load(fp)

    chains = wf.get_chains()
    assert len(chains) > 0
    first_chain = next(itervalues(chains))
    assert isinstance(first_chain, workflow.Chain)
    assert str(first_chain) == first_chain.id
    assert repr(first_chain) == "Chain <{}>".format(first_chain.id)
    assert isinstance(first_chain.link, workflow.Link)
    assert isinstance(first_chain.link, workflow.BaseLink)
    assert isinstance(first_chain["description"], workflow.TranslationLabel)
    assert first_chain["description"]._src == first_chain._src["description"]._src

    links = wf.get_links()
    assert len(links) > 0
    first_link = next(itervalues(links))
    assert repr(first_link) == "Link <{}>".format(first_link.id)
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
    assert str(wf) == "Chains {}, links {}, watched directories: {}".format(
        len(chains), len(links), len(wdirs)
    )

    # Test normalization of job statuses.
    link = next(itervalues(links))
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


def test_link_browse_methods(mocker):
    with open(os.path.join(ASSETS_DIR, "workflow.json")) as fp:
        wf = workflow.load(fp)
    ln = wf.get_link("1ba589db-88d1-48cf-bb1a-a5f9d2b17378")
    assert ln.get_next_link(code="0").id == "087d27be-c719-47d8-9bbb-9a7d8b609c44"
    assert ln.get_status_id(code="0") == workflow._STATUSES["Completed successfully"]
    assert ln.get_next_link(code="1").id == "7d728c39-395f-4892-8193-92f086c0546f"
    assert ln.get_status_id(code="1") == workflow._STATUSES["Failed"]


def test_get_schema():
    schema = workflow._get_schema()
    assert schema["$id"] == "https://www.archivematica.org/labs/workflow/schema/v1.json"


def test_get_schema_not_found(mocker):
    mocker.patch("server.workflow._LATEST_SCHEMA", "non-existen-schema")
    with pytest.raises(IOError):
        workflow._get_schema()
