import time
from decimal import Decimal
from typing import Any
import os
import json
from typing import Hashable


def actual_time():
    """ Returns actual time in microseconds """
    return int(time.time() * 1_000_000)


def serialize(obj: Any):
    """ Use to convert non-serializable data to serializable format while json.dumps """
    if isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, bytes):
        return obj.decode()
    else:
        try:
            return obj.__dict__
        except AttributeError:
            pass


def get_env_var(env: str, default: Any):
    return os.getenv(env) if os.getenv(env) else default


def response(obj: Hashable):
    return json.dumps(obj, default=serialize)
