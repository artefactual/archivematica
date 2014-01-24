import sys

sys.path.append('/usr/lib/archivematica/MCPServer')
from passClasses import ChoicesDict, ReplacementDict

def test_alternate_replacementdict_constructor():
    """
    This constructor allows serialized Python strings to be expanded
    into ReplacementDict instances.
    """

    d = {"foo": "bar"}
    assert ReplacementDict(d) == ReplacementDict.fromstring(str(d))

def test_alternate_choicesdict_constructor():
    d = {"foo": "bar"}
    assert ChoicesDict(d) == ChoicesDict.fromstring(str(d))

def test_replacementdict_replace():
    d = ReplacementDict({"%PREFIX%": "/usr/local"})
    assert d.replace("%PREFIX%/bin/") == ["/usr/local/bin/"]
