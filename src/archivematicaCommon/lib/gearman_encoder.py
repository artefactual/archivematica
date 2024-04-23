import gearman
import orjson


class JSONDataEncoder(gearman.DataEncoder):
    """Custom data encoder class for the `gearman` library (JSON)."""

    @classmethod
    def encode(cls, encodable_object):
        # Object of type bytes is not JSON serializable.
        if isinstance(encodable_object, bytes):
            encodable_object = encodable_object.decode("utf-8")
        return orjson.dumps(encodable_object)

    @classmethod
    def decode(cls, decodable_string):
        return orjson.loads(decodable_string)
