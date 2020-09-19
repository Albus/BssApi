import io

import fastapi
import pydantic
import starlette.responses
import pathlib

import bssapi.core.dbf

router = fastapi.APIRouter(default_response_class=starlette.responses.JSONResponse)


@router.post('/parse')
async def post_parse(source: pydantic.AnyUrl = fastapi.Query(default=...),
                     file: fastapi.UploadFile = fastapi.File(default=...)):
    if file.content_type == 'application/octet-stream':
        if pathlib.PurePosixPath(file.filename).suffix.lower() == '.dbf':
            dbf_bytes = io.BytesIO(await file.read())
            try:
                dbf = await bssapi.core.dbf.get_dbf(dbf_bytes)
            except ValueError:
                return starlette.responses.PlainTextResponse(status_code=422,
                                                             content='Не удалось прочитать файл')
    pass
