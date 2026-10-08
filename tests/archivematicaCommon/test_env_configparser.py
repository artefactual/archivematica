import configparser
import os
from io import StringIO

import pytest

from archivematica.archivematicaCommon.env_configparser import EnvConfigParser


@pytest.fixture
def environ() -> dict[str, str]:
    """Return a copy of the environment that tests can change freely."""
    return os.environ.copy()


def read_test_config(
    environ: dict[str, str], test_config: str, prefix: str = ""
) -> EnvConfigParser:
    config = EnvConfigParser(env=environ, prefix=prefix)
    config.read_file(StringIO(test_config))
    return config


def test_env_lookup_int(environ: dict[str, str]) -> None:
    """The environment precedes the configuration."""
    environ["ARCHIVEMATICA_NICESERVICE_QUEUE_MAX_SIZE"] = "100"
    config = read_test_config(
        environ,
        prefix="ARCHIVEMATICA_NICESERVICE",
        test_config="""
[queue]
max_size = 500
""",
    )
    assert config.getint("queue", "max_size") == 100


def test_env_lookup_nosection_bool(environ: dict[str, str]) -> None:
    """The environment string matches the option even though the corresponding
    section was not included.
    """
    environ["ARCHIVEMATICA_NICESERVICE_TLS"] = "off"
    config = read_test_config(
        environ,
        prefix="ARCHIVEMATICA_NICESERVICE",
        test_config="""
[network]
tls = on
""",
    )
    assert config.getboolean("network", "tls") is False


def test_unknown_section(environ: dict[str, str]) -> None:
    """It should raise `NoSectionError` when the section is undefined."""
    config = read_test_config(
        environ,
        """
[main]
foo = bar
""",
    )
    with pytest.raises(configparser.NoSectionError):
        config.get("undefined_section", "foo")


def test_unknown_option(environ: dict[str, str]) -> None:
    """It should raise `NoOptionError` when the option is undefined."""
    config = read_test_config(
        environ,
        """
[main]
foo = bar
""",
    )
    with pytest.raises(configparser.NoOptionError):
        config.get("main", "undefined_option")


def test_unknown_option_with_fallback(environ: dict[str, str]) -> None:
    """A fallback keyword argument can be used to obtain a value from the
    configuration even if it's undefined.
    """
    config = read_test_config(
        environ,
        """
[main]
foo = bar
""",
    )
    assert config.getboolean("main", "undefined_option", fallback=True) is True
    assert (
        config.getint("undefined_section", "undefined_option", fallback=12345) == 12345
    )
