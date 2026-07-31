from datetime import timedelta
from unittest import mock

import pytest

from archivematica.dashboard.main import idempotency
from archivematica.dashboard.main import models


@pytest.mark.django_db
def test_reserve_or_replay_retains_and_replays_result():
    create_result = mock.Mock(return_value={"id": "result-1"})
    kwargs = {
        "user_id": 1,
        "operation": "object.create",
        "key": "request-1",
        "request_fingerprint": idempotency.fingerprint({"name": "object"}),
        "retention": timedelta(days=1),
        "create_result": create_result,
    }

    created = idempotency.reserve_or_replay(**kwargs)
    with pytest.raises(idempotency.IdempotencyRequestInProgressError):
        idempotency.reserve_or_replay(**kwargs)

    idempotency.complete(created)
    replayed = idempotency.reserve_or_replay(**kwargs)

    assert created.result == {"id": "result-1"}
    assert created.created is True
    assert replayed.record_id == created.record_id
    assert replayed.result == {"id": "result-1"}
    assert replayed.created is False
    create_result.assert_called_once_with()


@pytest.mark.django_db
def test_reserve_or_replay_scopes_keys_to_operations():
    common = {
        "user_id": 1,
        "key": "request-1",
        "request_fingerprint": idempotency.fingerprint({"name": "object"}),
        "retention": timedelta(days=1),
    }

    first = idempotency.reserve_or_replay(
        **common,
        operation="object.create",
        create_result=lambda: {"id": "result-1"},
    )
    second = idempotency.reserve_or_replay(
        **common,
        operation="object.publish",
        create_result=lambda: {"id": "result-2"},
    )

    assert first.result == {"id": "result-1"}
    assert second.result == {"id": "result-2"}
    assert models.IdempotencyRecord.objects.count() == 2


@pytest.mark.django_db
def test_reserve_or_replay_rejects_changed_request():
    common = {
        "user_id": 1,
        "operation": "object.create",
        "key": "request-1",
        "retention": timedelta(days=1),
    }
    idempotency.reserve_or_replay(
        **common,
        request_fingerprint=idempotency.fingerprint({"name": "first"}),
        create_result=lambda: {"id": "result-1"},
    )

    with pytest.raises(idempotency.IdempotencyKeyConflictError):
        idempotency.reserve_or_replay(
            **common,
            request_fingerprint=idempotency.fingerprint({"name": "second"}),
            create_result=lambda: {"id": "result-2"},
        )


@pytest.mark.django_db
def test_reserve_or_replay_rolls_back_failed_operation():
    def fail():
        raise RuntimeError("operation failed")

    with pytest.raises(RuntimeError, match="operation failed"):
        idempotency.reserve_or_replay(
            user_id=1,
            operation="object.create",
            key="request-1",
            request_fingerprint=idempotency.fingerprint({"name": "object"}),
            retention=timedelta(days=1),
            create_result=fail,
        )

    assert not models.IdempotencyRecord.objects.exists()


@pytest.mark.django_db
def test_release_allows_a_failed_operation_to_be_retried():
    create_result = mock.Mock(side_effect=({"id": "failed"}, {"id": "retried"}))
    kwargs = {
        "user_id": 1,
        "operation": "object.create",
        "key": "request-1",
        "request_fingerprint": idempotency.fingerprint({"name": "object"}),
        "retention": timedelta(days=1),
        "create_result": create_result,
    }
    failed = idempotency.reserve_or_replay(**kwargs)

    idempotency.release(failed)
    retried = idempotency.reserve_or_replay(**kwargs)

    assert retried.record_id != failed.record_id
    assert retried.result == {"id": "retried"}
    assert retried.created is True
    assert models.IdempotencyRecord.objects.count() == 1
