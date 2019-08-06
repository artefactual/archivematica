# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

from django.test import TestCase
import pytest
from six import StringIO
import six.moves.configparser as ConfigParser

from env_configparser import EnvConfigParser


class TestConfigReader(TestCase):
    def setUp(self):
        """
        Make sure that we are not mutating the global environment. `os.environ`
        is an instance of `os._Environ` which implements a `copy` method.
        """
        self.environ = os.environ.copy()

    def tearDown(self):
        self.environ = None

    def read_test_config(self, test_config, prefix=""):
        buf = StringIO(test_config)
        config = EnvConfigParser(env=self.environ, prefix=prefix)
        config.readfp(buf)
        return config

    def test_env_lookup_int(self):
        """
        Note that the environment precedes the configuration.
        """
        self.environ["ARCHIVEMATICA_NICESERVICE_QUEUE_MAX_SIZE"] = "100"
        config = self.read_test_config(
            prefix="ARCHIVEMATICA_NICESERVICE",
            test_config="""
[queue]
max_size = 500
""",
        )
        assert config.getint("queue", "max_size") == 100

    def test_env_lookup_nosection_bool(self):
        """
        The environment string matches the option even though the corresponding
        section was not included.
        """
        self.environ["ARCHIVEMATICA_NICESERVICE_TLS"] = "off"
        config = self.read_test_config(
            prefix="ARCHIVEMATICA_NICESERVICE",
            test_config="""
[network]
tls = on
""",
        )
        assert config.getboolean("network", "tls") is False

    def test_unknown_section(self):
        """
        Confirm that `EnvConfigParser` throws a `NoSectionError` exception
        when undefined.
        """
        config = self.read_test_config(
            """
[main]
foo = bar
"""
        )
        with pytest.raises(ConfigParser.NoSectionError):
            assert config.get("undefined_section", "foo")

    def test_unknown_option(self):
        """
        Confirm that `EnvConfigParser` throws a `NoOptionError` exception
        when undefined.
        """
        config = self.read_test_config(
            """
[main]
foo = bar
"""
        )
        with pytest.raises(ConfigParser.NoOptionError):
            assert config.get("main", "undefined_option")

    def test_unknown_option_with_fallback(self):
        """
        A fallback keyword argument can be used to obtain a value from the
        configuration even if it's undefiend.
        """
        config = self.read_test_config(
            """
[main]
foo = bar
"""
        )
        assert config.getboolean("main", "undefined_option", fallback=True) is True
        assert (
            config.getint("undefined_section", "undefined_option", fallback=12345)
            == 12345
        )
