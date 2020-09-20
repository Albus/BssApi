import _hashlib

import orjson
import pydantic


def default_encoder(obj):
    if isinstance(obj, bytes):
        return obj.hex()
    elif isinstance(obj, pydantic.BaseModel):
        return obj.json()
    elif isinstance(obj, _hashlib.HASH):
        return obj.hexdigest()
    raise TypeError


def dump_bytes(v, *, default=default_encoder, sort: pydantic.StrictBool = False) -> bytes:
    option = orjson.OPT_NON_STR_KEYS | orjson.OPT_OMIT_MICROSECONDS | orjson.OPT_INDENT_2 | orjson.OPT_STRICT_INTEGER
    if sort:
        option = orjson.OPT_SORT_KEYS | option
    return orjson.dumps(v, default=default, option=option)


def dump_bytes_sorted(*args, **kwargs) -> bytes:
    return dump_bytes(sort=True, *args, **kwargs)

def dump_str(*args, **kwargs) -> str:
    return dump_bytes(sort=True, *args, **kwargs).decode()
