import collections
import hashlib
import pathlib
import typing

import bssapi_schemas.exch
import bssapi_dbfread as dbfread
import fastapi
import pydantic
import std_hash


async def get_hash(*values) -> pydantic.StrictStr:
    return pydantic.StrictStr(std_hash.hash(values).hex())


async def build_hash(url: bssapi_schemas.exch.Source, columns: typing.OrderedDict[
    pydantic.StrictStr, bssapi_schemas.exch.ColumnDescription]) -> bssapi_schemas.exch.Hash:
    format_hash = pydantic.StrictStr(await get_hash(columns))
    return bssapi_schemas.exch.Hash(
        format=format_hash,
        source=await get_hash(url, format_hash) if url and columns else None)


def build_source(url: pydantic.AnyUrl) -> bssapi_schemas.exch.Source:
    return bssapi_schemas.exch.Source(user=url.user or None,
                                      host=pydantic.StrictStr(url.host) or None,
                                      port=int(url.port) or None,
                                      path=pathlib.PurePosixPath(url.path).as_posix() if url.path else None)


async def build_format(url: typing.Optional[pydantic.AnyUrl], fields: typing.List) -> bssapi_schemas.exch.FormatPacket:
    _url = build_source(url) if url else None
    _columns = collections.OrderedDict(
        sorted({f.name: bssapi_schemas.exch.ColumnDescription(type=f.type, length=f.length or None,
                                                              decimal_count=f.decimal_count or None)
                for f in fields}.items())) if fields else None

    return bssapi_schemas.exch.FormatPacket(columns=_columns, url=_url,
                                            hash=await build_hash(url=_url, columns=_columns))


def build_packet(format_packet: bssapi_schemas.exch.FormatPacket, dbf: dbfread.DBF,
                 file: fastapi.UploadFile, dbf_bytes: pydantic.StrBytes) -> bssapi_schemas.exch.Packet:
    # noinspection PyCallByClass
    return bssapi_schemas.exch.Packet(format=format_packet.hash.format,
                                      source=format_packet.hash.source,
                                      rows=[collections.OrderedDict(sorted(row.items())) for row in dbf.records if row],
                                      file=bssapi_schemas.exch.Packet.File(
                                          name=pydantic.StrictStr(file.filename),
                                          modify=dbf.date or 0,
                                          url=format_packet.url,
                                          hex=pydantic.StrictStr(dbf_bytes.hex().upper()),
                                          hash=pydantic.StrictStr(hashlib.sha1(dbf_bytes).hexdigest().upper())))
