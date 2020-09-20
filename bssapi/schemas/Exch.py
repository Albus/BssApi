import collections
import datetime
import hashlib
import io
import pathlib
import tempfile
import typing
from _hashlib import HASH

import dbfread
import fastapi
import pydantic

import bssapi.core.dbf
import bssapi.core.json


class Source(pydantic.BaseModel):
    """
    Адрес службы доступа к файлам. Объект участвуе в формировании подписи источника данных (hash/source).
    """
    user: typing.Optional[pydantic.StrictStr] = pydantic.Field(
        title="Логин",
        description="Учетная запись пользователя под которой осуществляется доступ к файловой службе",
        example="ivan")
    host: pydantic.StrictStr = pydantic.Field(
        title="Сервер",
        description="DNS имя или IP адрес сервера",
        example="santens.ru")
    port: typing.Optional[pydantic.StrictInt] = pydantic.Field(
        title="ТСР порт",
        example=21)
    path: typing.Optional[pydantic.StrictStr] = pydantic.Field(
        title="Путь на сервере",
        example="/path/to/folder")

    class Config:
        from bssapi.core.json import dump_str
        title = 'Источник'
        json_dumps = dump_str


class ColumnDescription(pydantic.BaseModel):
    """
    Описание формата поля файла DBF
    """
    type: typing.Literal['C', 'N', 'D'] = pydantic.Field(
        example="C", title="Формат поля DBF",
        description="C(строка), N(число) D(дата)")
    length: pydantic.StrictInt = pydantic.Field(
        example=19,
        title="Максимальная длинна значения поля")
    decimal_count: typing.Optional[pydantic.StrictInt] = pydantic.Field(
        example=5,
        title="Кол-во десятичных знаков, если формат поля - число")

    class Config:
        title = "Формат колонки DBF"


class Hash(pydantic.BaseModel):
    """
    Контрольные суммы по алгоритму SHA1
    """
    format: pydantic.StrictStr = pydantic.Field(
        exclusiveRegex="^[0-9a-fA-F]{40}$",
        title="Идентификатор формата файла DBF",
        description="Высчитывается из набора колонок файла DBF (columns). "
                    "Выражает тип DBF в независимости от источника получения файла. "
                    "Может случить идентификатором набора колонок, их типов и порядка их расположения.",
        example="da58e0c8b7a42981282358c43c15b1d7004deaf4")
    source: typing.Optional[pydantic.StrictStr] = pydantic.Field(
        exclusiveRegex="^[0-9a-fA-F]{40}$",
        title="Идентификатор источника данных DBF",
        description="Высчитывается из набора колонок файла DBF (columns) и источника получения файла (url). "
                    "Так как одинаковые форматы DBF могут нести разную прикландую информцию, необходимо точно "
                    "идентифицировать формат файла. Не только по структуре, но и по ее применяемости.",
        example="4e38e02213ec9307ca5cd2bdd3ad9b05f0d24e7a")

    class Config:
        title = "Идентификаторы файла DBF"


class FormatPacket(pydantic.BaseModel):
    namespace: pydantic.StrictStr = pydantic.Field(
        default='Exch', const=True, example='Exch',
        title="Имя адресного пространства схемы данных 1С",
        description="Является константой, служит для идентификации системой 1С данного пакета")
    columns: typing.OrderedDict[pydantic.StrictStr, ColumnDescription] = pydantic.Field(title="Набор колонок файла DBF")
    url: typing.Optional[Source]
    hash: Hash

    class Config:
        from bssapi.core.json import dump_str
        json_dumps = dump_str
        title = "Формат файла DBF"


RowValueType = typing.TypeVar('RowValueType', pydantic.StrictStr, pydantic.StrictInt, pydantic.StrictFloat,
                              pydantic.StrictBool, datetime.datetime, datetime.date)


class Packet(Hash, pydantic.BaseModel):
    class Config:
        from bssapi.core.json import dump_str
        json_dumps = dump_str
        title = "Формат источника данных DBF"

    rows: typing.List[typing.OrderedDict[pydantic.StrictStr, RowValueType]] = pydantic.Field(title="Строки файла DBF")

    class File(pydantic.BaseModel):
        name: pydantic.StrictStr = pydantic.Field(title="Имя загруженного файла")
        hash: pydantic.StrictStr = pydantic.Field(exclusiveRegex="^[0-9a-fA-F]{40}$",
                                                  title="Хеш файла по алгоритму SHA1",
                                                  example="65188ac21abf3198780ebab1cefb005c12958afb")
        modify: datetime.date = pydantic.Field(title="Дата модификации файла DBF",
                                               description="Берется из заголовка самого файла, "
                                                           "не имеет значения зафиксированное время изменнения, "
                                                           "полученое из файловой системы")
        url: typing.Optional[Source]
        hex: pydantic.StrictStr = pydantic.Field(title="Содержимое файла в виде HEX строки")

        class Config:
            title = "Описание загруженного файла DBF"

    file: File


def get_hash(*values) -> pydantic.StrBytes:
    return hashlib.sha1(repr(values).encode()).digest()


def build_hash(url: Source, columns: typing.OrderedDict[pydantic.StrictStr, ColumnDescription]) -> Hash:
    format_hash = pydantic.StrictStr(get_hash(columns).hex())
    return Hash(
        format=format_hash,
        source=get_hash(url, format_hash).hex() if url and columns else None)


def build_source(url: pydantic.AnyUrl) -> Source:
    return Source(user=url.user or None,
                  host=pydantic.StrictStr(url.host) or None,
                  port=int(url.port) or None,
                  path=pathlib.PurePosixPath(url.path).as_posix() if url.path else None)


def build_format(url: typing.Optional[pydantic.AnyUrl], fields: typing.List) -> FormatPacket:
    _url = build_source(url) if url else None
    _columns = collections.OrderedDict(
        sorted({f.name: ColumnDescription(type=f.type, length=f.length or None,
                                          decimal_count=f.decimal_count or None)
                for f in fields}.items())) if fields else None

    return FormatPacket(columns=_columns, url=_url, hash=build_hash(url=_url, columns=_columns))


def build_packet(format_packet: FormatPacket, dbf: dbfread.DBF,
                 file: fastapi.UploadFile, dbf_bytes: pydantic.StrBytes) -> Packet:
    return Packet(format=format_packet.hash.format,
                  source=format_packet.hash.source,
                  rows=[collections.OrderedDict(sorted(row.items())) for row in dbf.records if row],
                  file=Packet.File(
                      name=pydantic.StrictStr(file.filename),
                      modify=dbf.date or 0,
                      url=format_packet.url,
                      hex=pydantic.StrictStr(dbf_bytes.hex()),
                      hash=pydantic.StrictStr(hashlib.sha1(dbf_bytes).hexdigest().upper())))
