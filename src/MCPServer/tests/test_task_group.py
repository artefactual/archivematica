from taskGroup import TaskGroup


def test__write_file_to_disk(mocker):
    tg = TaskGroup(None, u"foobar")

    open_ = mocker.mock_open()
    mocker.patch("taskGroup.open", open_)
    chmod = mocker.patch("os.chmod")

    # It does nothing when the parameters are not appropiate.
    tg._write_file_to_disk(None, None)
    assert not open_.called

    # It writes the contents and set the permissions.
    tg._write_file_to_disk("path", "contents")
    open_.assert_called_with("path", "a")
    fp = open_.return_value.__enter__.return_value
    fp.write.assert_called_with("contents")
    chmod.assert_called_with("path", 488)
