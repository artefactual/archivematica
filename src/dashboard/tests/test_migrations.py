# -*- coding: utf-8 -*-
from __future__ import absolute_import

import importlib

import pytest


# Import package that starts with a number.
mod = importlib.import_module("main.migrations.0066_archivesspace_base_url")


@pytest.mark.parametrize(
    "host_and_port, base_url",
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
def test_0066_get_base_url(host_and_port, base_url):
    """Test _get_baseurl."""
    assert base_url == mod._get_base_url(*host_and_port), "Failed with args %s" % (
        host_and_port
    )


@pytest.mark.parametrize(
    "base_url, host_and_port",
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
def test_0066_get_host_and_port(base_url, host_and_port):
    """Test _get_host_and_port."""
    assert host_and_port == mod._get_host_and_port(base_url), "Failed with arg %s" % (
        base_url,
    )
