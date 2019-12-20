# -*- encoding: utf-8

import pytest

from move_or_merge import move_or_merge


@pytest.fixture
def src_txt(tmpdir):
    return tmpdir.join("src.txt")


@pytest.fixture
def dst_txt(tmpdir):
    return tmpdir.join("dst.txt")


@pytest.fixture
def src_dir(tmpdir):
    return tmpdir.mkdir("src")


@pytest.fixture
def dst_dir(tmpdir):
    return tmpdir.mkdir("dst")


def test_move_or_merge_when_dst_doesnt_exist(src_txt, dst_txt):
    src_txt.write("hello world")

    move_or_merge(src=str(src_txt), dst=str(dst_txt))
    assert not src_txt.exists()
    assert dst_txt.exists()
    assert dst_txt.read() == "hello world"


def test_okay_if_dst_exists_and_is_same(src_txt, dst_txt):
    src_txt.write("hello world")
    dst_txt.write("hello world")

    move_or_merge(src=str(src_txt), dst=str(dst_txt))
    assert not src_txt.exists()
    assert dst_txt.exists()
    assert dst_txt.read() == "hello world"


def test_error_if_dst_exists_and_is_different(src_txt, dst_txt):
    src_txt.write("hello world")
    dst_txt.write("we come in peace")

    with pytest.raises(RuntimeError, match="dst exists and is different"):
        move_or_merge(src=str(src_txt), dst=str(dst_txt))

    # Check the original file wasn't deleted
    assert src_txt.exists()
    assert dst_txt.exists()


def test_moves_contents_of_directory_when_dst_does_not_exist(tmpdir):
    src_dir = tmpdir.mkdir("src")
    dst_dir = tmpdir.join("dst")

    src = src_dir.join("file.txt")
    dst = dst_dir.join("file.txt")
    src.write("hello world")

    move_or_merge(src=str(src_dir), dst=str(dst_dir))
    assert not src.exists()
    assert dst.exists()
    assert dst.read() == "hello world"


def test_moves_contents_with_no_files_at_src(tmpdir):
    src_dir = tmpdir.mkdir("src")
    dst_dir = tmpdir.join("dst")

    move_or_merge(src=str(src_dir), dst=str(dst_dir))
    assert dst_dir.exists()
    assert not len(dst_dir.listdir())


def test_moves_contents_of_directory(src_dir, dst_dir):
    src = src_dir.join("file.txt")
    dst = dst_dir.join("file.txt")
    src.write("hello world")

    move_or_merge(src=str(src_dir), dst=str(dst_dir))
    assert not src.exists()
    assert dst.exists()
    assert dst.read() == "hello world"


def test_moves_nested_directory(src_dir, dst_dir):
    src_nested = src_dir.mkdir("nested")
    dst_nested = dst_dir.join("nested")

    src = src_nested.join("file.txt")
    dst = dst_nested.join("file.txt")
    src.write("hello world")

    move_or_merge(src=str(src_dir), dst=str(dst_dir))
    assert not src.exists()
    assert dst.exists()
    assert dst.read() == "hello world"


def test_merges_nested_directory(src_dir, dst_dir):
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


def test_merges_nested_directory_with_existing_file(src_dir, dst_dir):
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


def test_merges_nested_directory_with_mismatched_existing_file(src_dir, dst_dir):
    src_nested = src_dir.mkdir("nested")
    dst_nested = dst_dir.mkdir("nested")

    src = src_nested.join("file.txt")
    dst = dst_nested.join("file.txt")
    src.write("hello world")
    dst.write("we come in peace")

    with pytest.raises(RuntimeError, match="dst exists and is different"):
        move_or_merge(src=str(src_dir), dst=str(dst_dir))


def test_ignores_existing_files_in_dst(src_dir, dst_dir):
    dst_existing = dst_dir.join("philosophy.txt")
    dst_existing.write("i think therefore i am")

    src_dir.join("file.txt").write("hello world")

    move_or_merge(src=str(src_dir), dst=str(dst_dir))
    assert dst_existing.exists()
    assert dst_existing.read() == "i think therefore i am"
