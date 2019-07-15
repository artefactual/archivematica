from __future__ import absolute_import, unicode_literals

from google.protobuf.timestamp_pb2 import Timestamp


def datetime_to_timestamp(datetime):
    timestamp = Timestamp()
    timestamp.FromDatetime(datetime)

    return timestamp


def current_timestamp():
    timestamp = Timestamp()
    timestamp.GetCurrentTime()

    return timestamp
