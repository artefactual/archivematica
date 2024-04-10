from datetime import datetime
from uuid import UUID

from django.utils.timezone import make_aware
from gearman_encoder import JSONDataEncoder


def test_json_data_encoder():
    encoder = JSONDataEncoder
    object_py = {
        "id": UUID("ccf0368e-ec97-4375-a408-5c4d95c0c671"),
        "data": [1, 2, 3],
        "when": make_aware(datetime(2019, 6, 18, 1, 1, 1, 123)),
    }
    object_js = (
        "{"
        + '"id":{"__type__":"UUID","value":"ccf0368eec974375a4085c4d95c0c671"},'
        + '"data":[1,2,3],'
        + '"when":{"__type__":"datetime","year":2019,"month":6,"day":18,"hour":1,"minute":1,"second":1,"microsecond":123}}'
    )

    assert encoder.encode(object_py) == object_js
    assert encoder.decode(object_js) == object_py


def test_json_data_encoder_with_bytes():
    encoder = JSONDataEncoder

    assert encoder.encode(b"bytes") == '"bytes"'
