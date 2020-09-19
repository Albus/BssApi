import collections
import datetime
import io
import typing

import dbfread
import pydantic


class RecFactory(collections.OrderedDict):

    def __setitem__(self, key: pydantic.StrictStr,
                    value: typing.Union[pydantic.StrictStr, pydantic.StrictInt, pydantic.StrictFloat,
                                        pydantic.StrictBool, datetime.datetime, datetime.date, None]):
        if value:
            super(RecFactory, self).__setitem__(key, value)


async def get_dbf(file: typing.Union[pydantic.StrictStr, io.BytesIO]) -> dbfread.DBF:
    return dbfread.DBF(filename=file,
                       ignorecase=True,
                       lowernames=True,
                       parserclass=dbfread.FieldParser,
                       recfactory=RecFactory,
                       load=True,
                       raw=False,
                       ignore_missing_memofile=False,
                       char_decode_errors='strict')
