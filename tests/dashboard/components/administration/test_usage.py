import subprocess
from unittest import mock

import pytest
from django.conf import settings
from django.test import Client

pytestmark = pytest.mark.usefixtures("dashboard_uuid")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query_string",
    [
        "",
        "?calculate=False",
        "?calculate=false",
        "?calculate=no",
        "?calculate=0",
        "?calculate=random",
    ],
)
def test_no_calculation(admin_client: Client, query_string: str) -> None:
    response = admin_client.get(f"/administration/usage/{query_string}")

    assert not response.context["calculate_usage"]
    content = response.content.decode("utf8")
    assert '<a href="?calculate=true"' in content
    assert "Calculate disk usage" in content


@pytest.mark.django_db
@pytest.mark.parametrize("calculate", ["true", "True", "ON", "yes", "1"])
@mock.patch(
    "archivematica.dashboard.components.administration.views._usage_get_directory_used_bytes",
    return_value=5368709120,
)
@mock.patch(
    "archivematica.dashboard.components.administration.views._usage_check_directory_volume_size",
    return_value=10737418240,
)
@mock.patch(
    "archivematica.dashboard.components.administration.views._get_mount_point_path",
    return_value="/",
)
def test_calculation(
    get_mount_point_path: mock.MagicMock,
    check_directory_volume_size: mock.MagicMock,
    get_directory_used_bytes: mock.MagicMock,
    admin_client: Client,
    calculate: str,
) -> None:
    response = admin_client.get(f"/administration/usage/?calculate={calculate}")

    assert response.context["calculate_usage"]
    get_mount_point_path.assert_called_once_with(settings.SHARED_DIRECTORY)
    check_directory_volume_size.assert_called_once_with("/")
    # The usage of the mount point, the shared directory and its five
    # clearable directories is calculated.
    assert get_directory_used_bytes.call_count == 7


@pytest.mark.django_db
@mock.patch(
    "subprocess.check_output",
    side_effect=[
        subprocess.CalledProcessError(1, cmd="du", output=b"unknown error ocurred"),
        subprocess.CalledProcessError(
            1, cmd="du", output=b"14141414\t/var/archivematica/sharedDirectory/\n"
        ),
    ],
)
@mock.patch(
    "archivematica.dashboard.components.administration.views._usage_check_directory_volume_size",
    return_value=10737418240,
)
@mock.patch(
    "archivematica.dashboard.components.administration.views._get_shared_dirs",
    return_value={},
)
def test_calculation_with_disk_usage_errors(
    get_shared_dirs: mock.MagicMock,
    check_directory_volume_size: mock.MagicMock,
    check_output: mock.MagicMock,
    admin_client: Client,
) -> None:
    """Test calculations of the usage view when the `du` call raises errors.

    We've mocked the helper that iterates disk usage on each
    shared directory so `du` is only called twice in this test
    case:

    - First with the mount point to which we raise an unknown
      error that results in a 0 bytes calculation
    - Then with the SHARED_DIRECTORY root to which we return
      parseable output that results in a valid integer
    """
    response = admin_client.get("/administration/usage/?calculate=yes")

    assert response.context["root"] == {"path": "/", "size": 10737418240, "used": 0}
    assert response.context["shared"] == {
        "path": "/var/archivematica/sharedDirectory/",
        "used": 14141414,
    }
