import collections
import datetime
import io
import typing

import chardet
import dbfread
import pydantic


class RecFactory(collections.OrderedDict):

    def __setitem__(self, key: pydantic.StrictStr,
                    value: typing.Union[pydantic.StrictStr, pydantic.StrictInt, pydantic.StrictFloat,
                                        pydantic.StrictBool, datetime.datetime, datetime.date, None]):
        if value:
            super(RecFactory, self).__setitem__(key, value)


async def get_dbf(file: pydantic.StrBytes) -> dbfread.DBF:
    encoding = chardet.detect(file).get('encoding')
    if encoding:
        return dbfread.DBF(filename=io.BytesIO(file),
                           ignorecase=True,
                           lowernames=True,
                           parserclass=dbfread.FieldParser,
                           recfactory=RecFactory,
                           load=True,
                           raw=False,
                           ignore_missing_memofile=False,
                           char_decode_errors='strict', encoding=encoding)
    else:
        pass  # TODO: обработать ошибку определения кодировки DBF

