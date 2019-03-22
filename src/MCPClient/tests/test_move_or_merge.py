# -*- encoding: utf-8

import pytest

from .move_or_merge import move_or_merge


def test_move_or_merge_when_dst_doesnt_exist(tmpdir):
    src = tmpdir.join("src.txt")
    dst = tmpdir.join("dst.txt")

    src.write("hello world")

    move_or_merge(src=src, dst=dst)
    assert not src.exists()
    assert dst.exists()
    assert dst.read() == "hello world"


def test_okay_if_dst_exists_and_is_same(tmpdir):
    src = tmpdir.join("src.txt")
    dst = tmpdir.join("dst.txt")

    src.write("hello world")
    dst.write("hello world")

    move_or_merge(src=src, dst=dst)
    assert not src.exists()
    assert dst.exists()
    assert dst.read() == "hello world"


def test_error_if_dst_exists_and_is_different(tmpdir):
    src = tmpdir.join("src.txt")
    dst = tmpdir.join("dst.txt")

    src.write("hello world")
    dst.write("we come in peace")

    with pytest.raises(RuntimeError, match="dst exists and is different"):
        move_or_merge(src=src, dst=dst)

    # Check the original file wasn't deleted
    assert src.exists()
    assert dst.exists()


def test_moves_contents_of_directory(tmpdir):
    src_dir = tmpdir.mkdir("src")
    dst_dir = tmpdir.mkdir("dst")

    src = src_dir.join("file.txt")
    dst = dst_dir.join("file.txt")
    src.write("hello world")

    move_or_merge(src=str(src_dir), dst=str(dst_dir))
    assert not src.exists()
    assert dst.exists()
    assert dst.read() == "hello world"


def test_moves_nested_directory(tmpdir):
    src_dir = tmpdir.mkdir("src")
    dst_dir = tmpdir.mkdir("dst")

    src_nested = src_dir.mkdir("nested")
    dst_nested = dst_dir.join("nested")

    src = src_nested.join("file.txt")
    dst = dst_nested.join("file.txt")
    src.write("hello world")

    move_or_merge(src=str(src_dir), dst=str(dst_dir))
    assert not src.exists()
    assert dst.exists()
    assert dst.read() == "hello world"


def test_merges_nested_directory(tmpdir):
    src_dir = tmpdir.mkdir("src")
    dst_dir = tmpdir.mkdir("dst")

    src_nested = src_dir.mkdir("nested")

    # Unlike the previous test, we create the "nested" directory upfront,
    # but we don't populate it.
    dst_nested = dst_dir.mkdir("nested")

    src = src_nested.join("file.txt")
    dst = dst_nested.join("file.txt")
    src.write("hello world")

    move_or_merge(src=str(src_dir), dst=str(dst_dir))
    assert not src.exists()
    assert dst.exists()
    assert dst.read() == "hello world"


def test_merges_nested_directory_with_existing_file(tmpdir):
    src_dir = tmpdir.mkdir("src")
    dst_dir = tmpdir.mkdir("dst")

    src_nested = src_dir.mkdir("nested")
    dst_nested = dst_dir.mkdir("nested")

    src = src_nested.join("file.txt")
    dst = dst_nested.join("file.txt")
    src.write("hello world")
    dst.write("hello world")

    move_or_merge(src=str(src_dir), dst=str(dst_dir))
    assert not src.exists()
    assert dst.exists()
    assert dst.read() == "hello world"


def test_merges_nested_directory_with_mismatched_existing_file(tmpdir):
    src_dir = tmpdir.mkdir("src")
    dst_dir = tmpdir.mkdir("dst")

    src_nested = src_dir.mkdir("nested")
    dst_nested = dst_dir.mkdir("nested")

    src = src_nested.join("file.txt")
    dst = dst_nested.join("file.txt")
    src.write("hello world")
    dst.write("we come in peace")

    with pytest.raises(RuntimeError, match="dst exists and is different"):
        move_or_merge(src=str(src_dir), dst=str(dst_dir))


def test_ignores_existing_files_in_dst(tmpdir):
    src_dir = tmpdir.mkdir("src")
    dst_dir = tmpdir.mkdir("dst")

    dst_existing = dst_dir.join("philosophy.txt")
    dst_existing.write("i think therefore i am")

    src_dir.join("file.txt").write("hello world")

    move_or_merge(src=str(src_dir), dst=str(dst_dir))
    assert dst_existing.exists()
    assert dst_existing.read() == "i think therefore i am"
