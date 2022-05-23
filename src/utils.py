import time
from decimal import Decimal
from typing import Any


def actual_time():
    """ Returns actual time in microseconds """
    return int(time.time() * 1_000_000)


def serialize(obj: Any):
    """ Use to convert non-serializable data to serializable format while json.dumps """
    if isinstance(obj, Decimal):
        return str(obj)
    else:
        try:
            return obj.__dict__
        except AttributeError:
            pass
