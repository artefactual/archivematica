# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pytest

from fileOperations import get_extract_dir_name


@pytest.mark.parametrize(
    "filename,dirname",
    [
        ("/parent/test.zip", "/parent/test"),
        ("/parent/test.tar.gz", "/parent/test"),
        ("/parent/test.TAR.GZ", "/parent/test"),
        ("/parent/test.TAR.GZ", "/parent/test"),
        (
            "/parent/test.target.tar.gz",
            "/parent/test.target",
        ),  # something beginning with "tar"
    ],
)
def test_get_extract_dir_name(filename, dirname):
    assert get_extract_dir_name(filename) == dirname


def test_get_extract_dir_name_raises_if_no_extension():
    with pytest.raises(ValueError):
        get_extract_dir_name("test")
