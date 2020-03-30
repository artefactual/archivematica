# -*- coding: utf-8 -*-
from __future__ import absolute_import

import bagit
from mock import patch

from archivematicaFunctions import get_bag_size, walk_dir


def test_get_bag_size(tmpdir):
    """Test that get_bag_size uses bag-info Payload-Oxum when present.
    """
    # Set up test data
    bag_dir = tmpdir.mkdir("bag")
    data_file = bag_dir.join("file.txt")
    data_file.write("Lorem ipsum")
    bag = bagit.make_bag(bag_dir.strpath)
    # Replace Payload-Oxum with incorrect arbitrary value
    size_oxum = "105621.12"
    bag.info["Payload-Oxum"] = size_oxum
    bag.save()
    # Assertions
    with patch("archivematicaFunctions.os") as mock_os:
        # Test returned value against expected
        size = get_bag_size(bag, bag_dir.strpath)
        assert size == int(size_oxum.split(".")[0])
        # Verify directory was not walked
        mock_os.path.getsize.assert_not_called()


def test_get_bag_size_bag_missing_oxum(tmpdir):
    """Test that get_bag_size uses walk if bag-info Payload-Oxum is missing.
    """
    # Set up test data
    bag_dir = tmpdir.mkdir("bag")
    data_file = bag_dir.join("file.txt")
    data_file.write("Lorem ipsum")
    bag = bagit.make_bag(bag_dir.strpath)
    # Remove Payload-Oxum from bag.info
    del bag.info["Payload-Oxum"]
    bag.save()
    # Test returned value against expected
    size_on_disk = walk_dir(bag_dir.strpath)
    size = get_bag_size(bag, bag_dir.strpath)
    assert size == size_on_disk
    # Verify directory was walked
    with patch("archivematicaFunctions.os") as mock_os:
        get_bag_size(bag, bag_dir.strpath)
        mock_os.path.getsize.assert_called()
