import pytest

from package import _determine_transfer_paths


@pytest.mark.parametrize("name,path,tmpdir,expected", [
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
    )
])
@pytest.mark.django_db
def test__determine_transfer_paths(name, path, tmpdir, expected):
    results = _determine_transfer_paths(name, path, tmpdir)
    assert results[0] == expected[0], "name mismatch"
    assert results[1] == expected[1], "path mismatch"
    assert results[2] == expected[2], "tmpdir mismatch"
