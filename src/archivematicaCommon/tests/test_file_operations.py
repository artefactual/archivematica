import pytest

from fileOperations import get_extract_dir_name


@pytest.mark.parametrize(
    "filename,dirname",
    [
        ("test.zip", "test"),
        ("test.tar.gz", "test"),
        ("test.TAR.GZ", "test"),
        ("test.TAR.GZ", "test"),
        ("test.target.tar.gz", "test.target"),  # something beginning with "tar"
    ],
)
def test_get_extract_dir_name(filename, dirname):
    assert get_extract_dir_name(filename) == dirname


def test_get_extract_dir_name_raises_if_no_extension():
    with pytest.raises(ValueError):
        get_extract_dir_name("test")
