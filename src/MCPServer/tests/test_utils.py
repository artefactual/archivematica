from utils import valid_uuid


def test_valid_uuid():
    # UUIDv4 is validated
    assert valid_uuid("07dc3d44-2ea3-45f7-a069-4ba1c79fb789") is True
    # Other versions are not accepted
    assert valid_uuid("00000000-0000-0000-0000-000000000000") is False
    assert valid_uuid("77b99cea-8ab4-11e8-96a8-185e0fad6335") is False
