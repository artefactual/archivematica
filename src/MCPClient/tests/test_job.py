import os
import sys
from uuid import uuid4

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))
from job import Job


def test_job(tmpdir):
    job_name = "somejob"
    job_uuid = str(uuid4())
    job_args = ["a", "b"]
    j = Job(name=job_name, uuid=job_uuid, args=job_args)
    unicode_printable = u"change\u0301"
    j.pyprint(unicode_printable)
    stdout = j.get_stdout()
    expected = "{}\n".format(unicode_printable.encode("utf8"))
    assert expected == stdout
