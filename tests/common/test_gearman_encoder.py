from datetime import datetime

from django.utils.timezone import make_aware
from gearman_encoder import JSONDataEncoder


def test_encoder():
    assert JSONDataEncoder.encode(b"bytes") == b'"bytes"'
    assert JSONDataEncoder.encode([1, 2, 3]) == b"[1,2,3]"
    assert (
        JSONDataEncoder.encode(
            {"date": make_aware(datetime(2019, 6, 18, 1, 1, 1, 123))}
        )
        == b'{"date":"2019-06-18T01:01:01.000123+00:00"}'
    )

    assert JSONDataEncoder.decode("[1,2,3]") == [1, 2, 3]
