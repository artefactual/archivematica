import pytest

from fileOperations import get_extract_dir_name


@pytest.mark.parametrize(
    "filename,dirname", [("test.zip", "test"), ("test.tar.gz", "test")]
)
def test_get_extract_dir_name(filename, dirname):
    assert get_extract_dir_name(filename) == dirname
