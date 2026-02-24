from __future__ import annotations

import inspect
from unittest import mock

from django.http import HttpResponse
from django.test import RequestFactory

from archivematica.dashboard.components.ingest import pair_matcher


class DummyClient:
    def get_resource_component_and_children(self, resource_id):
        return {
            "id": resource_id,
            "title": "Resource",
            "children": [],
        }

    def get_resource_component_children(self, resource_component_id):
        return {
            "id": resource_component_id,
            "title": "Component",
            "children": [],
        }


def test_build_as_matcher_payload_contains_bootstrap_data_and_match_url() -> None:
    with mock.patch.object(
        pair_matcher,
        "reverse",
        return_value="/ingest/dip-1/upload/as/match/",
    ) as mocked_reverse:
        payload = pair_matcher._build_as_matcher_payload(
            uuid="dip-1",
            object_paths=[{"uuid": "file-1", "path": "objects/a.txt"}],
            resource_data={"id": "/repositories/2/resources/1", "children": []},
            matches=[],
        )

    assert mocked_reverse.call_count == 2
    mocked_reverse.assert_any_call("ingest:ingest_upload_as_match", args=["dip-1"])
    mocked_reverse.assert_any_call("ingest:ingest_upload_as_review_matches", args=["dip-1"])
    assert payload["dipUuid"] == "dip-1"
    assert payload["urls"]["match"] == "/ingest/dip-1/upload/as/match/"
    assert payload["urls"]["review"] == "/ingest/dip-1/upload/as/match/"
    assert payload["urls"]["reset"] is None
    assert payload["objectPaths"][0]["uuid"] == "file-1"
    assert payload["labels"]["pair"]
    assert payload["labels"]["pairSelectedObjects"]
    assert payload["labels"]["reviewMatches"]
    assert payload["labels"]["deleteMatch"]


def test_match_dip_objects_to_resource_levels_renders_explicit_context() -> None:
    request = RequestFactory().get("/ingest/example/")
    client = DummyClient()
    fake_response = HttpResponse("ok")

    with mock.patch.object(
        pair_matcher,
        "ingest_upload_atk_get_dip_object_paths",
        return_value=[{"uuid": "file-1", "path": "a.txt"}],
    ), mock.patch.object(
        pair_matcher,
        "_build_as_matcher_payload",
        return_value={"boot": "payload"},
    ) as mocked_payload, mock.patch.object(
        pair_matcher,
        "render",
        return_value=fake_response,
    ) as mocked_render:
        response = pair_matcher.match_dip_objects_to_resource_levels(
            client=client,
            request=request,
            resource_id="/repositories/2/resources/1",
            match_template="ingest/as/match.html",
            parent_id="/repositories/2/resources/1",
            parent_url="ingest:ingest_upload_as_resource",
            reset_url="ingest:ingest_upload_as_reset",
            uuid="dip-1",
            matches=[{"resource_id": "r1", "file_uuid": "f1", "resource": {"id": "r1"}}],
        )

    assert response is fake_response
    mocked_payload.assert_called_once()
    mocked_render.assert_called_once()

    render_args = mocked_render.call_args.args
    assert render_args[0] is request
    assert render_args[1] == "ingest/as/match.html"
    context = render_args[2]
    assert context == {
        "parent_id": "/repositories/2/resources/1",
        "parent_url": "ingest:ingest_upload_as_resource",
        "reset_url": "ingest:ingest_upload_as_reset",
        "uuid": "dip-1",
        "matcher_payload": {"boot": "payload"},
    }


def test_pair_matcher_module_does_not_use_locals_for_render_contexts() -> None:
    source = inspect.getsource(pair_matcher)
    assert "locals()" not in source
