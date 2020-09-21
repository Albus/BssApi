
__all__ = ['router']

from pathlib import PurePosixPath

from dbfread import DBF
from fastapi import UploadFile, Query, APIRouter, File
from pydantic import AnyUrl, StrictStr

from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from pydantic.error_wrappers import ErrorWrapper
from starlette.responses import UJSONResponse

import bssapi.core.dbf
import bssapi.schemas.Exch

router = APIRouter(default_response_class=UJSONResponse)

_descr_source = """
    Путь к папке с файлом без названия самого файла.
    Используйте закрывающий слеш !
    Пример: ftp://ivan@santens.ru:21/path/to/folder/
    !!! Если не передавать данный параметр, то поля (url, hash/source) расчитываться не будут"""


@router.post('/format', response_model=bssapi.schemas.Exch.FormatPacket,
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
    if file.content_type == 'application/octet-stream':

        ext = PurePosixPath(file.filename).suffix.lower()

        await file.seek(0)
        dbf_bytes = await file.read()
        if request:
            await file.close()

        if ext in ['.dbf']:
            dbf = None
            try:
                dbf = await bssapi.core.dbf.get_dbf(dbf_bytes)
            except BaseException as exc:
                raise RequestValidationError(
                    errors=[ErrorWrapper(
                        exc=ValueError('Не могу открыть файл.', StrictStr(exc)), loc=("body", "file"))],
                    body={"file": file.filename})
            else:
                if isinstance(dbf, DBF):
                    format_packet = bssapi.schemas.Exch.build_format(url=url, fields=dbf.fields)
                    dbf.unload()
                    return format_packet
                else:
                    raise RequestValidationError(
                        errors=[ErrorWrapper(exc=ValueError('Не могу открыть файл.'), loc=("body", "file"))],
                        body={"file": file.filename})

        else:
            raise RequestValidationError(
                errors=[
                    ErrorWrapper(exc=ValueError('Не верное расширение файла'), loc=("body", "filename", "extension"))],
                body={"filename": {"extension": ext, "filename": file.filename}})

    else:
        raise RequestValidationError(
            errors=[ErrorWrapper(
                exc=ValueError("Не верный тип содержимого тела запроса. Ожидалось 'application/octet-stream'"),
                loc=("body", "Сontent-type"))],
            body={"Сontent-type": file.content_type})


@router.post('/source', response_model=bssapi.schemas.Exch.Packet,
             summary='Схема источника данных файла DBF',
             description="Препарирует переданный файл DBF. Выдает описание источника данных.",
             response_description="Файл обработан без ошибок")
async def parse_source(
        url: AnyUrl = Query(
            default=None, title="URI источника данных",
            description=_descr_source),
        file: UploadFile = File(
            default=..., title="Файл DBF", description="Файл формата dBase(3/4)")):
    format_packet = await parse_format(url=url, file=file)

    await file.seek(0)
    dbf_bytes = await file.read()
    await file.close()

    dbf = await bssapi.core.dbf.get_dbf(dbf_bytes)
    source_packet = bssapi.schemas.Exch.build_packet(format_packet=format_packet, dbf=dbf,
                                                     dbf_bytes=dbf_bytes, file=file)
    dbf.unload()

    return source_packet
