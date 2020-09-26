__all__ = ['router']

import typing
from pathlib import PurePosixPath

import lz4.block
from bssapi_dbfread import DBF
from fastapi import UploadFile, Query, APIRouter, File
from fastapi.exceptions import RequestValidationError
import multipart.multipart
from pydantic import AnyUrl, StrictStr, StrBytes
import pydantic.error_wrappers
from starlette.requests import Request
import starlette.responses

import bssapi.core.dbf
import bssapi.schemas.exch
import bssapi_schemas.exch
from bssapi.schemas.http.headers import ContentType

router = APIRouter(default_response_class=starlette.responses.UJSONResponse)

_descr_source = """
    Путь к папке с файлом без названия самого файла.
    Используйте закрывающий слеш !
    Пример: ftp://ivan@santens.ru:21/path/to/folder/
    !!! Если не передавать данный параметр, то поля (url, hash/source) расчитываться не будут"""


async def unpack(content_type: ContentType, value: UploadFile, dont_close_after_read=typing.Any) -> StrBytes:
    await value.seek(0)
    _value = await value.read()
    if dont_close_after_read:
        await value.close()
    else:
        await value.seek(0)
    try:
        if 'base64' in content_type.params:
            _value = multipart.multipart.base64.standard_b64decode(_value)
        if 'lz4' in content_type.params:
            _value = lz4.block.decompress(source=_value)
    except BaseException as exc:
        raise RequestValidationError(
            errors=[pydantic.error_wrappers.ErrorWrapper(
                exc=ValueError('Не могу распаковать содержиме файла.', StrictStr(exc)),
                loc=("body", "params"))],
            body=ContentType)
    return _value


@router.post('/format', response_model=bssapi_schemas.exch.FormatPacket,
             summary='Описание формата файла DBF',
             description="Препарирует переданный файл DBF. Выдает описание его формата.",
             response_description="Файл обработан без ошибок")
async def parse_format(
        url: AnyUrl = Query(
            default=None, title="URI источника данных",
            description=_descr_source),
        file: UploadFile = File(
            default=..., title="Файл DBF", description="Файл формата dBase(3/4)"),
        request: Request = None):
    content_type = await ContentType.from_str(StrictStr(file.content_type))
    if content_type.type == "application/octet-stream":

        dbf_bytes = await unpack(value=file, content_type=content_type, dont_close_after_read=request)

        ext = PurePosixPath(file.filename).suffix.lower()
        if ext in ['.dbf']:
            dbf = None
            try:
                dbf = await bssapi.core.dbf.get_dbf(dbf_bytes) if len(dbf_bytes) else None
            except BaseException as exc:
                raise RequestValidationError(
                    errors=[pydantic.error_wrappers.ErrorWrapper(
                        exc=ValueError('Не могу открыть файл.', StrictStr(exc)), loc=("body", "file"))],
                    body={"file": file.filename})
            else:
                if isinstance(dbf, DBF):
                    format_packet = await bssapi.schemas.exch.build_format(url=url, fields=dbf.fields)
                    dbf.unload()
                    return format_packet
                else:
                    raise RequestValidationError(
                        errors=[pydantic.error_wrappers.ErrorWrapper(exc=ValueError('Не могу открыть файл.'),
                                                                     loc=("body", "file"))],
                        body={"file": file.filename})

        else:
            raise RequestValidationError(
                errors=[
                    pydantic.error_wrappers.ErrorWrapper(exc=ValueError('Не верное расширение файла'),
                                                         loc=("body", "filename", "extension"))],
                body={"filename": {"extension": ext, "filename": file.filename}})

    else:
        raise RequestValidationError(
            errors=[pydantic.error_wrappers.ErrorWrapper(
                exc=ValueError("Не верный тип содержимого тела запроса. Ожидалось 'application/octet-stream'"),
                loc=("body", "Сontent-type"))],
            body={"Сontent-type": file.content_type})


@router.post('/source', response_model=bssapi_schemas.exch.Packet,
             summary='Схема источника данных файла DBF',
             description="Препарирует переданный файл DBF. Выдает описание источника данных.",
             response_description="Файл обработан без ошибок")
async def parse_source(url: AnyUrl = Query(
                           default=None, title="URI источника данных",
                           description=_descr_source),
                       file: UploadFile = File(
                           default=..., title="Файл DBF", description="Файл формата dBase(3/4)")):
    format_packet = await parse_format(url=url, file=file)

    dbf_bytes = await unpack(value=file, dont_close_after_read=False,
                             content_type=await ContentType.from_str(StrictStr(file.content_type)))

    dbf = await bssapi.core.dbf.get_dbf(dbf_bytes)
    source_packet = bssapi.schemas.exch.build_packet(format_packet=format_packet, dbf=dbf,
                                                     dbf_bytes=dbf_bytes, file=file)
    dbf.unload()

    return source_packet
