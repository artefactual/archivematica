import importlib

import pytest

# Import package that starts with a number.
mod = importlib.import_module("main.migrations.0066_archivesspace_base_url")


@pytest.mark.parametrize(
    "host_and_port, expected_result",
    [
        ((None, None), ""),
        (("", ""), ""),
        (("foobar", ""), "http://foobar"),
        (("foobar.tld", ""), "http://foobar.tld"),
        (("foobar.tld", None), "http://foobar.tld"),
        (("foobar.tld", "12345"), "http://foobar.tld:12345"),
        (("http://foobar.tld", "12345"), "http://foobar.tld"),
        (("http://foobar.tld:789/asdf", "8089"), "http://foobar.tld:789/asdf"),
    ],
)
def test_0066_get_base_url(host_and_port, expected_result):
    """Test _get_baseurl."""
    assert expected_result == mod._get_base_url(*host_and_port), (
        "Failed with args %s" % (host_and_port)
    )


@pytest.mark.parametrize(
    "url, expected_result",
    [
        (None, ("", "")),
        ("", ("", "")),
        ("foobar.tld", ("foobar.tld", "")),
        ("foobar.tld:12345", ("foobar.tld", "12345")),
        ("http://foobar.tld", ("foobar.tld", "")),
        ("http://foobar.tld:8089", ("foobar.tld", "8089")),
        ("http://foobar.tld:8089/subpath", ("foobar.tld", "8089")),
    ],
)
def test_0066_get_host_and_port(url, expected_result):
    """Test _get_host_and_port."""
    assert expected_result == mod._get_host_and_port(url), f"Failed with arg {url}"
