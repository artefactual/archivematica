import json
import uuid
from datetime import datetime

import gearman
from django.utils.timezone import make_aware


class JSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        kwargs["object_hook"] = self.object_hook
        super().__init__(*args, **kwargs)

    def object_hook(self, d: dict):
        object_type = d.get("__type__")
        if object_type == "datetime":
            return make_aware(
                datetime(
                    d["year"],
                    d["month"],
                    d["day"],
                    d["hour"],
                    d["minute"],
                    d["second"],
                    d["microsecond"],
                )
            )
        elif object_type == "UUID":
            return uuid.UUID(hex=d["value"])
        return d


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return {
                "__type__": "datetime",
                "year": obj.year,
                "month": obj.month,
                "day": obj.day,
                "hour": obj.hour,
                "minute": obj.minute,
                "second": obj.second,
                "microsecond": obj.microsecond,
            }
        elif isinstance(obj, uuid.UUID):
            return {
                "__type__": "UUID",
                "value": obj.hex,
            }
        else:
            return super().default(obj)


class JSONDataEncoder(gearman.DataEncoder):
    """Custom data encoder class for the `gearman` library (JSON).

    This class enables serialization and deserialization of data using JSON
    format, supporting UUID and datetime data types.
    """

    @classmethod
    def encode(cls, encodable_object):
        # Object of type bytes is not JSON serializable.
        if isinstance(encodable_object, bytes):
            encodable_object = encodable_object.decode("utf-8")
        return json.dumps(encodable_object, cls=JSONEncoder, separators=(",", ":"))

    @classmethod
    def decode(cls, decodable_string):
        return json.loads(decodable_string, cls=JSONDecoder)
