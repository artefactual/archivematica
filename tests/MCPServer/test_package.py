import threading
import uuid
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

import archivematica.MCPServer.server.packages as packages
from archivematica.dashboard.main import models
from archivematica.dashboard.main.idempotency import IdempotencyKeyConflictError
from archivematica.dashboard.main.idempotency import IdempotencyRequestInProgressError
from archivematica.MCPServer.server.jobs import Job as WorkflowJob
from archivematica.MCPServer.server.packages import DIP
from archivematica.MCPServer.server.packages import PACKAGE_CREATE_OPERATION
from archivematica.MCPServer.server.packages import PACKAGE_TYPE_STARTING_POINTS
from archivematica.MCPServer.server.packages import RETRIEVE_TRANSFER_SOURCE_CHAIN_ID
from archivematica.MCPServer.server.packages import SIP
from archivematica.MCPServer.server.packages import Package
from archivematica.MCPServer.server.packages import Transfer
from archivematica.MCPServer.server.packages import _capture_transfer_failure
from archivematica.MCPServer.server.packages import _determine_transfer_paths
from archivematica.MCPServer.server.packages import _move_to_internal_shared_dir
from archivematica.MCPServer.server.packages import _start_package_transfer
from archivematica.MCPServer.server.packages import (
    _start_package_transfer_with_auto_approval,
)
from archivematica.MCPServer.server.packages import create_package
from archivematica.MCPServer.server.queues import PackageQueue
from archivematica.MCPServer.server.tasks import Task as WorkflowTask
from archivematica.MCPServer.server.workflow import Workflow

# Static workflow contract asserted by package bootstrap tests.
RETRIEVAL_LINK_ID = "b3843201-3c52-4124-a7ee-16faaccf24b9"


@pytest.mark.parametrize(
    "name,path,tmpdir,expected",
    [
        (
            "TransferName",
            "a00a29b6-7530-4f09-b3df-fd88d9e478b1:home/username/archive.zip",
            "/tmp/tmp.WXA9V7LCy1",
            (
                # copy_to
                "/tmp/tmp.WXA9V7LCy1",
                # final_location
                "/tmp/tmp.WXA9V7LCy1/archive.zip",
                # copy_from
                "a00a29b6-7530-4f09-b3df-fd88d9e478b1:home/username/archive.zip",
            ),
        ),
        (
            "TransferName",
            "a00a29b6-7530-4f09-b3df-fd88d9e478b2:home/username/dir",
            "/tmp/tmp.WXA9V7LCy2",
            (
                # copy_to
                "/tmp/tmp.WXA9V7LCy2/TransferName",
                # final_location
                "/tmp/tmp.WXA9V7LCy2/TransferName",
                # copy_from
                "a00a29b6-7530-4f09-b3df-fd88d9e478b2:home/username/dir/.",
            ),
        ),
    ],
)
@pytest.mark.django_db
def test__determine_transfer_paths(name, path, tmpdir, expected):
    results = _determine_transfer_paths(name, path, tmpdir)
    assert results[0] == expected[0], "name mismatch"
    assert results[1] == expected[1], "path mismatch"
    assert results[2] == expected[2], "tmpdir mismatch"


@pytest.mark.django_db(transaction=True)
def test_dip_get_or_create_from_db_path_without_uuid(tmp_path):
    dip_path = tmp_path / "test-dip"

    dip = DIP.get_or_create_from_db_by_path(str(dip_path))

    assert dip.current_path == str(dip_path)
    try:
        models.SIP.objects.get(uuid=dip.uuid)
    except (models.SIP.DoesNotExist, ValidationError):
        pytest.fail("DIP.get_or_create_from_db_by_path didn't create a SIP model")


@pytest.mark.django_db(transaction=True)
def test_dip_get_or_create_from_db_path_with_uuid(tmp_path):
    dip_uuid = uuid.uuid4()
    dip_path = tmp_path / f"test-dip-{dip_uuid}"

    dip = DIP.get_or_create_from_db_by_path(str(dip_path))

    assert dip.uuid == dip_uuid
    assert dip.current_path == str(dip_path)
    try:
        models.SIP.objects.get(uuid=dip_uuid)
    except (models.SIP.DoesNotExist, ValidationError):
        pytest.fail("DIP.get_or_create_from_db_by_path didn't create a SIP model")


@pytest.mark.django_db(transaction=True)
def test_transfer_get_or_create_from_db_path_without_uuid(tmp_path):
    transfer_path = tmp_path / "test-transfer"

    assert not models.Transfer.objects.filter(
        currentlocation=str(transfer_path)
    ).count()

    transfer = Transfer.get_or_create_from_db_by_path(str(transfer_path))

    assert transfer.current_path == str(transfer_path)
    try:
        models.Transfer.objects.get(currentlocation=str(transfer_path))
    except models.Transfer.DoesNotExist:
        pytest.fail(
            "Transfer.get_or_create_from_db_by_path didn't create a Transfer model"
        )


@pytest.mark.django_db(transaction=True)
def test_transfer_get_or_create_from_db_path_with_uuid(tmp_path):
    transfer_uuid = uuid.uuid4()
    transfer_path = tmp_path / f"test-transfer-{transfer_uuid}"

    transfer = Transfer.get_or_create_from_db_by_path(str(transfer_path))

    assert transfer.uuid == transfer_uuid
    assert transfer.current_path == str(transfer_path)
    try:
        models.Transfer.objects.get(uuid=transfer_uuid)
    except (models.Transfer.DoesNotExist, ValidationError):
        pytest.fail(
            "Transfer.get_or_create_from_db_by_path didn't create a Transfer model"
        )


@pytest.mark.parametrize(
    "package_class, model, loc_attribute",
    [(Transfer, models.Transfer, "currentlocation"), (SIP, models.SIP, "currentpath")],
)
@pytest.mark.django_db(transaction=True)
def test_package_get_or_create_from_db_by_path_updates_model(
    tmp_path, settings, package_class, model, loc_attribute
):
    settings.SHARED_DIRECTORY = "custom-shared-path"
    package_id = uuid.uuid4()
    path_src = tmp_path / r"%sharedPath%" / "src" / f"test-transfer-{package_id}"
    path_dst = tmp_path / r"%sharedPath%" / "dst" / f"test-transfer-{package_id}"

    package_obj_src = package_class.get_or_create_from_db_by_path(str(path_src))
    package_obj_dst = package_class.get_or_create_from_db_by_path(str(path_dst))

    assert package_id == package_obj_src.uuid == package_obj_dst.uuid
    assert package_obj_src.current_path == str(path_src).replace(
        r"%sharedPath%", settings.SHARED_DIRECTORY
    )
    assert package_obj_dst.current_path == str(path_dst).replace(
        r"%sharedPath%", settings.SHARED_DIRECTORY
    )
    try:
        model.objects.get(**{"uuid": package_id, loc_attribute: path_dst})
    except (models.Transfer.DoesNotExist, ValidationError):
        pytest.fail(
            f"Method {package_class.__name__}.get_or_create_from_db_by_path didn't update {model.__name__} model"
        )


@pytest.mark.django_db(transaction=True)
def test_reload_file_list(tmp_path):
    # Create a transfer that will be updated through time to simulate
    # Archivematica's processing.
    transfer_uuid = uuid.uuid4()
    transfer_path = tmp_path / f"test-transfer-{transfer_uuid}"
    transfer = Transfer.get_or_create_from_db_by_path(str(transfer_path))

    # Add files to the transfer to simulate a transfer existing on disk.
    transfer_path.mkdir()
    objects_path = transfer_path / "objects"
    objects_path.mkdir()
    first_file = objects_path / "file.txt"
    first_file.touch()

    current_location = Path(transfer.REPLACEMENT_PATH_STRING, "objects", "file.txt")
    kwargs = {
        "uuid": uuid.uuid4(),
        "currentlocation": bytes(current_location),
        "filegrpuse": "original",
        "transfer_id": transfer_uuid,
    }
    models.File.objects.create(**kwargs)
    assert models.File.objects.filter(transfer_id=str(transfer_uuid)).count() == 1

    # Add a new file to the file-system, e.g. to simulate normalization for
    # preservation adding a new object.
    new_file = objects_path / "new_file.txt"
    new_file.touch()

    # One file will be returned from the database  with a UUID, another from
    # the filesystem without a UUID.
    for _file_count, file_info in enumerate(transfer.files(None, "/objects"), 1):
        assert "%fileUUID%" in file_info
        assert "%fileGrpUse%" in file_info
        assert "%relativeLocation%" in file_info
        if file_info.get("%fileUUID%") != "None":
            continue
        assert file_info.get("%relativeLocation%") == str(new_file)
        file_path = Path(
            transfer.REPLACEMENT_PATH_STRING,
            "objects",
            Path(file_info.get("%relativeLocation%")).relative_to(objects_path),
        )
        kwargs = {
            "uuid": uuid.uuid4(),
            "currentlocation": bytes(file_path),
            "filegrpuse": "original",
            "transfer_id": transfer_uuid,
        }
        models.File.objects.create(**kwargs)
    assert _file_count == 2, (
        "Database and file objects were not returned by the generator"
    )
    assert models.File.objects.filter(transfer_id=str(transfer_uuid)).count() == 2

    # Simulate an additional file object being added later on in the transfer
    # in a sub directory of the objects folder, e.g. transcribe contents.
    sub_dir = objects_path / "subdir"
    sub_dir.mkdir()
    new_file = sub_dir / "another_new_file.txt"
    new_file.touch()
    for _file_count, file_info in enumerate(transfer.files(None, "/objects"), 1):
        if file_info.get("%fileUUID%") != "None":
            continue
        file_path = Path(
            transfer.REPLACEMENT_PATH_STRING,
            "objects",
            Path(file_info.get("%relativeLocation%")).relative_to(Path(objects_path)),
        )
        kwargs = {
            "uuid": uuid.uuid4(),
            "currentlocation": bytes(file_path),
            "filegrpuse": "original",
            "transfer_id": transfer_uuid,
        }
        models.File.objects.create(**kwargs)
    assert _file_count == 3, (
        "Database and file objects were not returned by the generator"
    )
    assert models.File.objects.filter(transfer_id=str(transfer_uuid)).count() == 3

    # Now the database is updated, we will still have the same file count, but
    # all objects will be returned from the database and we will have uuids.
    for _file_count, file_info in enumerate(transfer.files(None, "/objects"), 1):
        if file_info.get("%fileUUID%") == "None":
            raise AssertionError(
                f"Non-database entries returned from package.files(): {file_info}"
            )
    assert _file_count == 3

    # Finally, let's just see if the scan works for a slightly larger no.
    # files, i.e. a number with an increment slightly larger than one.
    files = ["f1", "f2", "f3", "f4", "f5"]
    for file_ in files:
        new_file = objects_path / file_
        new_file.touch()
    new_count = 0
    for _file_count, file_info in enumerate(transfer.files(None, "/objects"), 1):
        if file_info.get("%fileUUID%") == "None":
            new_count += 1
    assert new_count == 5
    assert _file_count == 8

    # Clean up state and ensure test doesn't interfere with other transfers
    # expected to be in the database, e.g. in test_queues.py.
    models.File.objects.filter(transfer_id=str(transfer_uuid)).delete()


def test_package_files_materializes_database_rows_in_batches(monkeypatch):
    batch_size = 2

    class FakeQuerySet:
        def __init__(self, file_objs):
            self.file_objs = list(file_objs)

        def filter(self, **kwargs):
            assert set(kwargs) == {"uuid__gt"}
            file_objs = [
                file_obj
                for file_obj in self.file_objs
                if file_obj.uuid > kwargs["uuid__gt"]
            ]
            return FakeQuerySet(file_objs)

        def order_by(self, *fields):
            assert fields == ("uuid",)
            return FakeQuerySet(
                sorted(self.file_objs, key=lambda file_obj: file_obj.uuid)
            )

        def __getitem__(self, index):
            if isinstance(index, slice):
                return FakeQuerySet(self.file_objs[index])
            return self.file_objs[index]

        def __iter__(self):
            if len(self.file_objs) > batch_size:
                raise AssertionError(
                    "Package.files() must materialize bounded database pages"
                )
            return iter(self.file_objs)

        def iterator(self):
            raise AssertionError(
                "Package.files() must not stream database rows with QuerySet.iterator()"
            )

        def exists(self):
            return bool(self.file_objs)

    class FakePackage(Package):
        FILE_QUERYSET_BATCH_SIZE = 2
        REPLACEMENT_PATH_STRING = "%transferDirectory%"

        @property
        def base_queryset(self):
            return queryset

        def queryset(self):
            raise NotImplementedError

        def reload(self):
            raise NotImplementedError

    file_objs = [
        SimpleNamespace(uuid=uuid.UUID("00000000-0000-0000-0000-000000000001")),
        SimpleNamespace(uuid=uuid.UUID("00000000-0000-0000-0000-000000000002")),
        SimpleNamespace(uuid=uuid.UUID("00000000-0000-0000-0000-000000000003")),
    ]
    queryset = FakeQuerySet(file_objs)

    monkeypatch.setattr(packages, "auto_close_old_connections", nullcontext)
    monkeypatch.setattr(packages.os.path, "exists", lambda path: True)
    monkeypatch.setattr(packages.os, "walk", lambda path: [])
    monkeypatch.setattr(
        packages,
        "get_file_replacement_mapping",
        lambda file_obj, current_path: {
            "%inputFile%": f"{current_path}/{file_obj.uuid}",
            "%fileUUID%": str(file_obj.uuid),
        },
    )

    package = FakePackage("/transfer", uuid.uuid4())
    files = list(package.files())

    assert [file_obj["%fileUUID%"] for file_obj in files] == [
        str(file_objs[0].uuid),
        str(file_objs[1].uuid),
        str(file_objs[2].uuid),
    ]


@pytest.mark.django_db(transaction=True)
def test_package_files_with_non_ascii_names(tmp_path):
    # Create a Transfer package
    transfer_uuid = uuid.uuid4()
    transfer_path = tmp_path / f"test-transfer-{transfer_uuid}"
    transfer = Transfer.get_or_create_from_db_by_path(str(transfer_path))

    # Add a file to the transfer with non-ascii name
    transfer_path.mkdir()
    objects = transfer_path / "objects"
    objects.mkdir()
    file_ = objects / "montréal.txt"
    file_.touch()

    # Create a File model instance for the transfer file
    current_location = Path(transfer.REPLACEMENT_PATH_STRING, "objects", "montréal.txt")
    kwargs = {
        "uuid": uuid.uuid4(),
        "currentlocation": bytes(current_location),
        "filegrpuse": "original",
        "transfer_id": transfer_uuid,
    }
    models.File.objects.create(**kwargs)

    # Assert only one file is returned
    result = list(transfer.files(None, "/objects"))
    assert len(result) == 1

    # And it is the file we just created
    assert result[0]["%fileUUID%"] == str(kwargs["uuid"])
    assert result[0]["%currentLocation%"] == current_location.as_posix()
    assert result[0]["%fileGrpUse%"] == kwargs["filegrpuse"]


@pytest.fixture
def transfer():
    return models.Transfer.objects.create()


@pytest.fixture
def processing_dir(tmp_path):
    proc_dir = tmp_path / "processing"
    proc_dir.mkdir()
    return proc_dir


@pytest.mark.django_db(transaction=True)
class TestMoveToInternalSharedDir:
    def test_move_dir(self, tmp_path, processing_dir, transfer):
        filepath = tmp_path / "transfer"
        filepath.mkdir()

        _move_to_internal_shared_dir(str(filepath), str(processing_dir), transfer)

        transfer.refresh_from_db()
        dest_path = processing_dir / "transfer"
        assert dest_path.is_dir()
        assert Path(transfer.currentlocation) == dest_path

    def test_move_file(self, tmp_path, processing_dir, transfer):
        filepath = tmp_path / "transfer.zip"
        filepath.touch()

        _move_to_internal_shared_dir(str(filepath), str(processing_dir), transfer)

        dest_path = processing_dir / "transfer.zip"
        assert dest_path.is_file()

        transfer.refresh_from_db()
        assert Path(transfer.currentlocation) == dest_path


@pytest.mark.parametrize(
    "package_class,model_class",
    [
        (
            Transfer,
            models.Transfer,
        ),
        (
            SIP,
            models.SIP,
        ),
        (
            DIP,
            models.SIP,
        ),
    ],
)
@pytest.mark.django_db(transaction=True)
def test_package_statuses(tmp_path, package_class, model_class):
    package_id = uuid.uuid4()
    model_class.objects.create(pk=package_id)
    package = package_class(str(tmp_path), package_id)

    package.mark_as_done()

    assert model_class.objects.get(pk=package_id).status == models.PACKAGE_STATUS_DONE

    package.mark_as_failed()

    assert model_class.objects.get(pk=package_id).status == models.PACKAGE_STATUS_FAILED

    package.mark_as_processing()

    assert (
        model_class.objects.get(pk=package_id).status
        == models.PACKAGE_STATUS_PROCESSING
    )

    Package.cleanup_old_db_entries()

    assert model_class.objects.get(pk=package_id).status == models.PACKAGE_STATUS_FAILED


@pytest.mark.django_db(transaction=True)
def test_create_package(tmp_path, admin_user, settings):
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    workflow = mock.Mock(spec=Workflow)

    d = tmp_path / "sub"
    d.mkdir()
    (d / "tmp").mkdir()
    settings.SHARED_DIRECTORY = str(d)

    # Verify there are no existing transfers.
    assert models.Transfer.objects.count() == 0

    create_package(
        package_queue,
        executor,
        "foobar",
        "standard",
        "",
        "",
        d.as_posix(),
        "",
        admin_user.pk,
        workflow,
        auto_approve=True,
        processing_config="automated",
    )

    # Verify a transfer was added.
    assert models.Transfer.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_create_package_marks_auto_approved_transfer_processing_before_submission(
    admin_user, wf, retrieval_directories
):
    """The public status changes before background bootstrap is accepted."""
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)

    def submit(*args):
        transfer = models.Transfer.objects.get()
        assert transfer.status == models.PACKAGE_STATUS_PROCESSING
        return Future()

    executor.submit.side_effect = submit

    transfer = create_package(
        package_queue=package_queue,
        executor=executor,
        name="TransferName",
        type_="standard",
        accession="",
        access_system_id="",
        path="source-location:/transfer/source/path",
        metadata_set_id="",
        user_id=admin_user.pk,
        workflow=wf,
        auto_approve=True,
    )

    transfer.refresh_from_db()
    assert transfer.status == models.PACKAGE_STATUS_PROCESSING
    submitted = executor.submit.call_args.args
    assert submitted[0] is _start_package_transfer_with_auto_approval
    assert submitted[1] == transfer
    package_queue.schedule_job.assert_not_called()


@pytest.mark.django_db(transaction=True)
def test_create_package_marks_auto_approved_transfer_failed_when_submission_rejected(
    admin_user, wf, retrieval_directories
):
    """A rejected executor handoff leaves an explicit terminal transfer state."""
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    executor.submit.side_effect = RuntimeError(
        "cannot schedule new futures after shutdown"
    )

    with pytest.raises(RuntimeError, match="cannot schedule new futures"):
        create_package(
            package_queue=package_queue,
            executor=executor,
            name="TransferName",
            type_="standard",
            accession="",
            access_system_id="",
            path="source-location:/transfer/source/path",
            metadata_set_id="",
            user_id=admin_user.pk,
            workflow=wf,
            auto_approve=True,
        )

    transfer = models.Transfer.objects.get()
    assert transfer.status == models.PACKAGE_STATUS_FAILED
    assert transfer.completed_at is not None
    assert not any(retrieval_directories.staging.iterdir())
    package_queue.schedule_job.assert_not_called()


@pytest.mark.django_db(transaction=True)
def test_create_package_without_auto_approval_uses_watched_directory_copy(
    admin_user, wf, retrieval_directories
):
    """Non-auto-approved packages retain their watched-directory bootstrap."""
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    executor.submit.return_value = Future()
    starting_point = PACKAGE_TYPE_STARTING_POINTS["standard"]

    transfer = create_package(
        package_queue=package_queue,
        executor=executor,
        name="TransferName",
        type_="standard",
        accession="",
        access_system_id="",
        path="home/username/transfer",
        metadata_set_id="",
        user_id=admin_user.pk,
        workflow=wf,
        auto_approve=False,
    )

    assert transfer.status != models.PACKAGE_STATUS_PROCESSING
    executor.submit.assert_called_once_with(
        _start_package_transfer,
        transfer,
        "TransferName",
        "home/username/transfer",
        mock.ANY,
        starting_point,
    )
    package_queue.schedule_job.assert_not_called()


def _idempotent_package_kwargs(admin_user, wf):
    return {
        "name": "TransferName",
        "type_": "standard",
        "accession": "accession-1",
        "access_system_id": "system-1",
        "path": "source-location:/transfer/source/path",
        "metadata_set_id": "",
        "user_id": admin_user.pk,
        "workflow": wf,
        "auto_approve": True,
        "idempotency_key": "transfer-submission-123",
    }


@pytest.mark.django_db(transaction=True)
def test_create_package_replays_idempotent_submission(
    admin_user, wf, retrieval_directories
):
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    executor.submit.return_value = Future()
    kwargs = _idempotent_package_kwargs(admin_user, wf)

    first_uuid = create_package(package_queue, executor, **kwargs)
    second_uuid = create_package(package_queue, executor, **kwargs)

    assert second_uuid == first_uuid
    assert models.Transfer.objects.count() == 1
    assert models.IdempotencyRecord.objects.count() == 1
    record = models.IdempotencyRecord.objects.get()
    assert record.operation == PACKAGE_CREATE_OPERATION
    assert record.result == {"id": first_uuid}
    assert record.state == models.IdempotencyRecord.State.COMPLETED
    assert record.key_hash != kwargs["idempotency_key"]
    assert len(record.key_hash) == 64
    executor.submit.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_create_package_scopes_idempotency_key_to_user(
    admin_user, django_user_model, wf, retrieval_directories
):
    other_user = django_user_model.objects.create_user(username="other-user")
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    executor.submit.return_value = Future()
    kwargs = _idempotent_package_kwargs(admin_user, wf)

    first_uuid = create_package(package_queue, executor, **kwargs)
    second_uuid = create_package(
        package_queue,
        executor,
        **{**kwargs, "user_id": other_user.pk},
    )

    assert second_uuid != first_uuid
    assert models.Transfer.objects.count() == 2
    assert models.IdempotencyRecord.objects.count() == 2
    assert executor.submit.call_count == 2


@pytest.mark.django_db(transaction=True)
def test_create_package_rejects_changed_idempotent_submission(
    admin_user, wf, retrieval_directories
):
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    executor.submit.return_value = Future()
    kwargs = _idempotent_package_kwargs(admin_user, wf)
    create_package(package_queue, executor, **kwargs)

    with pytest.raises(IdempotencyKeyConflictError):
        create_package(
            package_queue,
            executor,
            **{**kwargs, "path": "source-location:/different/path"},
        )

    assert models.Transfer.objects.count() == 1
    assert models.IdempotencyRecord.objects.count() == 1
    executor.submit.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_create_package_reuses_expired_idempotency_key(
    admin_user, wf, retrieval_directories
):
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    executor.submit.return_value = Future()
    kwargs = _idempotent_package_kwargs(admin_user, wf)
    first_uuid = create_package(package_queue, executor, **kwargs)
    models.IdempotencyRecord.objects.update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )

    second_uuid = create_package(package_queue, executor, **kwargs)

    assert second_uuid != first_uuid
    assert models.Transfer.objects.count() == 2
    assert models.IdempotencyRecord.objects.count() == 1
    assert executor.submit.call_count == 2


@pytest.mark.django_db(transaction=True)
def test_create_package_replays_after_transfer_is_purged(
    admin_user, wf, retrieval_directories
):
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    executor.submit.return_value = Future()
    kwargs = _idempotent_package_kwargs(admin_user, wf)
    transfer_uuid = create_package(package_queue, executor, **kwargs)
    models.Transfer.objects.filter(pk=transfer_uuid).delete()

    replayed_uuid = create_package(package_queue, executor, **kwargs)

    assert replayed_uuid == transfer_uuid
    assert not models.Transfer.objects.exists()
    assert models.IdempotencyRecord.objects.count() == 1
    executor.submit.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_create_package_replays_when_processing_configuration_disappears(
    admin_user, wf, retrieval_directories
):
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    executor.submit.return_value = Future()
    config_dir = (
        retrieval_directories.shared
        / "sharedMicroServiceTasksConfigs"
        / "processingMCPConfigs"
    )
    config_dir.mkdir(parents=True)
    config_path = config_dir / "customProcessingMCP.xml"
    config_path.touch()
    kwargs = {
        **_idempotent_package_kwargs(admin_user, wf),
        "processing_config": "custom",
    }
    transfer_uuid = create_package(package_queue, executor, **kwargs)
    config_path.unlink()

    replayed_uuid = create_package(package_queue, executor, **kwargs)

    assert replayed_uuid == transfer_uuid
    assert models.Transfer.objects.count() == 1
    assert models.IdempotencyRecord.objects.count() == 1
    executor.submit.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_create_package_replays_when_metadata_set_is_deleted(
    admin_user, wf, retrieval_directories
):
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    executor.submit.return_value = Future()
    metadata_set = models.TransferMetadataSet.objects.create(
        createdbyuserid=admin_user.pk
    )
    kwargs = {
        **_idempotent_package_kwargs(admin_user, wf),
        "metadata_set_id": str(metadata_set.pk),
    }
    transfer_uuid = create_package(package_queue, executor, **kwargs)
    metadata_set.delete()

    replayed_uuid = create_package(package_queue, executor, **kwargs)

    assert replayed_uuid == transfer_uuid
    assert not models.Transfer.objects.exists()
    assert models.IdempotencyRecord.objects.count() == 1
    executor.submit.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_create_package_releases_keyed_result_when_executor_rejects_handoff(
    admin_user, wf, retrieval_directories
):
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    executor.submit.side_effect = [
        RuntimeError("executor unavailable"),
        Future(),
    ]
    kwargs = _idempotent_package_kwargs(admin_user, wf)

    with pytest.raises(RuntimeError, match="executor unavailable"):
        create_package(package_queue, executor, **kwargs)

    failed_transfer = models.Transfer.objects.get()
    assert failed_transfer.status == models.PACKAGE_STATUS_FAILED
    assert failed_transfer.completed_at is not None
    assert not models.IdempotencyRecord.objects.exists()

    retried_uuid = create_package(package_queue, executor, **kwargs)

    assert retried_uuid != str(failed_transfer.pk)
    assert models.Transfer.objects.count() == 2
    record = models.IdempotencyRecord.objects.get()
    assert record.result == {"id": retried_uuid}
    assert record.state == models.IdempotencyRecord.State.COMPLETED
    assert executor.submit.call_count == 2


@pytest.mark.django_db(transaction=True)
def test_concurrent_idempotent_submission_is_not_replayed_before_handoff(
    admin_user, wf, retrieval_directories
):
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    kwargs = _idempotent_package_kwargs(admin_user, wf)
    handoff_started = threading.Event()
    allow_handoff = threading.Event()

    def submit(*args):
        handoff_started.set()
        assert allow_handoff.wait(timeout=5)
        return Future()

    executor.submit.side_effect = submit
    with ThreadPoolExecutor(max_workers=1) as caller:
        first = caller.submit(create_package, package_queue, executor, **kwargs)
        assert handoff_started.wait(timeout=5)

        with pytest.raises(IdempotencyRequestInProgressError):
            create_package(package_queue, executor, **kwargs)

        allow_handoff.set()
        transfer_uuid = first.result(timeout=10)

    assert create_package(package_queue, executor, **kwargs) == transfer_uuid
    assert models.Transfer.objects.count() == 1
    assert models.IdempotencyRecord.objects.count() == 1
    executor.submit.assert_called_once()


@pytest.mark.parametrize(
    "starting_point",
    PACKAGE_TYPE_STARTING_POINTS.values(),
    ids=PACKAGE_TYPE_STARTING_POINTS,
)
@pytest.mark.django_db(transaction=True)
def test_auto_approved_package_schedules_retrieval_workflow(
    starting_point, wf, retrieval_directories
):
    """Every supported transfer type records its post-retrieval continuation."""
    transfer = models.Transfer.objects.create(uuid=uuid.uuid4())
    package_queue = mock.Mock(spec=PackageQueue)
    source_path = "a00a29b6-7530-4f09-b3df-fd88d9e478b1:home/username/transfer"

    _start_package_transfer_with_auto_approval(
        transfer,
        "TransferName",
        source_path,
        str(retrieval_directories.staging / "tmp123"),
        starting_point,
        wf,
        package_queue,
    )

    transfer.refresh_from_db()
    expected_copied_path = str(
        retrieval_directories.staging / "tmp123" / "TransferName"
    )
    assert transfer.status == models.PACKAGE_STATUS_PROCESSING
    assert transfer.currentlocation == "%sharedPath%tmp/tmp123/TransferName"
    unit_variable = models.UnitVariable.objects.get(
        unittype="Transfer",
        unituuid=transfer.uuid,
        variable="linkAfterTransferSourceRetrieval",
    )
    assert unit_variable.variablevalue == ""
    assert str(unit_variable.microservicechainlink) == starting_point.link

    scheduled_job = package_queue.schedule_job.call_args.args[0]
    assert scheduled_job.job_chain.chain.id == RETRIEVE_TRANSFER_SOURCE_CHAIN_ID
    assert scheduled_job.link.id == RETRIEVAL_LINK_ID
    assert scheduled_job.job_chain.context[r"%transferSourcePath%"] == (
        f"{source_path}/."
    )
    assert scheduled_job.job_chain.context[r"%transferSourceDestination%"] == (
        "/tmp/tmp123/TransferName"
    )
    assert (
        scheduled_job.job_chain.context[r"%transferSourceCopiedPath%"]
        == expected_copied_path
    )
    assert scheduled_job.job_chain.context[r"%sharedPath%"] == str(
        retrieval_directories.shared
    )


@pytest.mark.django_db(transaction=True)
def test_auto_approved_package_does_not_copy_before_workflow(wf, retrieval_directories):
    """MCPServer only plans retrieval; it performs no Storage Service I/O."""
    transfer = models.Transfer.objects.create(uuid=uuid.uuid4())
    package_queue = mock.Mock(spec=PackageQueue)

    with (
        mock.patch(
            "archivematica.MCPServer.server.packages._copy_from_transfer_sources"
        ) as copy_from_transfer_sources,
        mock.patch(
            "archivematica.MCPServer.server.packages._move_to_internal_shared_dir"
        ) as move_to_internal_shared_dir,
    ):
        _start_package_transfer_with_auto_approval(
            transfer,
            "TransferName",
            "home/username/transfer",
            str(retrieval_directories.staging / "tmp123"),
            PACKAGE_TYPE_STARTING_POINTS["standard"],
            wf,
            package_queue,
        )

    copy_from_transfer_sources.assert_not_called()
    move_to_internal_shared_dir.assert_not_called()


@pytest.mark.django_db(transaction=True)
def test_non_auto_approved_package_still_uses_watched_directory_copy(
    retrieval_directories,
):
    transfer = models.Transfer.objects.create(uuid=uuid.uuid4())
    starting_point = PACKAGE_TYPE_STARTING_POINTS["standard"]

    with (
        mock.patch(
            "archivematica.MCPServer.server.packages._copy_from_transfer_sources"
        ) as copy_from_transfer_sources,
        mock.patch(
            "archivematica.MCPServer.server.packages._move_to_internal_shared_dir"
        ) as move_to_internal_shared_dir,
    ):
        _start_package_transfer(
            transfer,
            "TransferName",
            "home/username/transfer",
            str(retrieval_directories.staging / "tmp123"),
            starting_point,
        )

    copy_from_transfer_sources.assert_called_once_with(
        ["home/username/transfer/."],
        "/tmp/tmp123/TransferName",
    )
    move_to_internal_shared_dir.assert_called_once_with(
        str(retrieval_directories.staging / "tmp123" / "TransferName"),
        starting_point.watched_dir,
        transfer,
    )


def test_capture_transfer_failure_propagates_transfer_does_not_exist():
    @_capture_transfer_failure
    def fn():
        raise models.Transfer.DoesNotExist

    with pytest.raises(models.Transfer.DoesNotExist):
        fn()


def test_capture_transfer_failure_propagates_validation_error():
    @_capture_transfer_failure
    def fn():
        raise ValidationError("invalid argument")

    with pytest.raises(ValidationError):
        fn()


def test_capture_transfer_failure_logs_other_exceptions():
    @_capture_transfer_failure
    def fn():
        raise RuntimeError("something went wrong")

    with mock.patch("archivematica.MCPServer.server.packages.logger") as mock_logger:
        fn()

    mock_logger.exception.assert_called_once_with(
        "Exception occurred during transfer processing"
    )


def test_capture_transfer_failure_closes_old_executor_connections():
    """Transfer workers discard stale thread-local connections before work."""
    calls = []

    @_capture_transfer_failure
    def fn():
        calls.append("called")

    with (
        mock.patch(
            "archivematica.archivematicaCommon.dbconns.close_old_connections"
        ) as close_old_connections,
        ThreadPoolExecutor(max_workers=1) as executor,
    ):
        executor.submit(fn).result(timeout=1)

    close_old_connections.assert_called_once_with()
    assert calls == ["called"]


@pytest.mark.django_db(transaction=True)
def test_capture_transfer_failure_marks_transfer_failed():
    transfer = models.Transfer.objects.create(
        status=models.PACKAGE_STATUS_PROCESSING,
    )

    @_capture_transfer_failure(mark_transfer_failed=True)
    def fn(transfer):
        raise RuntimeError("workflow scheduling failed")

    fn(transfer)

    transfer.refresh_from_db()
    assert transfer.status == models.PACKAGE_STATUS_FAILED
    assert transfer.completed_at is not None


@pytest.mark.django_db(transaction=True)
def test_capture_transfer_failure_preserves_old_transfer_status_by_default():
    transfer = models.Transfer.objects.create(
        status=models.PACKAGE_STATUS_UNKNOWN,
    )

    @_capture_transfer_failure
    def fn(transfer):
        raise RuntimeError("watched-directory copy failed")

    fn(transfer)

    transfer.refresh_from_db()
    assert transfer.status == models.PACKAGE_STATUS_UNKNOWN
    assert transfer.completed_at is None


@pytest.mark.django_db(transaction=True)
def test_startup_cleanup_fails_queued_transfer_retrieval():
    transfer = models.Transfer.objects.create(
        status=models.PACKAGE_STATUS_PROCESSING,
        currentlocation="%sharedPath%tmp/tmp123/TransferName",
    )

    assert not models.Job.objects.filter(sipuuid=transfer.uuid).exists()

    Package.cleanup_old_db_entries()

    transfer.refresh_from_db()
    assert transfer.status == models.PACKAGE_STATUS_FAILED
    assert transfer.completed_at is not None


@pytest.mark.django_db(transaction=True)
def test_startup_cleanup_fails_executing_transfer_retrieval():
    transfer = models.Transfer.objects.create(
        status=models.PACKAGE_STATUS_PROCESSING,
        currentlocation="%sharedPath%tmp/tmp123/TransferName",
    )
    retrieval_job = models.Job.objects.create(
        sipuuid=transfer.uuid,
        unittype="unitTransfer",
        jobtype="Retrieve transfer source",
        microservicegroup="Retrieve transfer source",
        microservicechainlink="b3843201-3c52-4124-a7ee-16faaccf24b9",
        currentstep=models.Job.STATUS_EXECUTING_COMMANDS,
        createdtime=timezone.now(),
    )
    retrieval_task = models.Task.objects.create(
        job=retrieval_job,
        createdtime=timezone.now(),
    )

    Package.cleanup_old_db_entries()
    WorkflowJob.cleanup_old_db_entries()
    WorkflowTask.cleanup_old_db_entries()

    transfer.refresh_from_db()
    retrieval_job.refresh_from_db()
    retrieval_task.refresh_from_db()
    assert transfer.status == models.PACKAGE_STATUS_FAILED
    assert transfer.completed_at is not None
    assert retrieval_job.currentstep == models.Job.STATUS_FAILED
    assert retrieval_task.exitcode == -1
    assert retrieval_task.stderror == "MCP shut down while processing."
