__version__ = '0.1.0'
__all__ = [r'api', r'app']

import uvicorn
import fastapi.middleware
import fastapi.middleware.gzip
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, UJSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from .api.router import router

api = fastapi.FastAPI(debug=False, version=__version__,
                      middleware=[
                          fastapi.middleware.Middleware(fastapi.middleware.gzip.GZipMiddleware, minimum_size=100)],
                      openapi_tags=[
                          {
                              "name": "DBF",
                              "description": "Операции с файлами DBF"
                          }
                      ],
                      docs_url="/test", redoc_url="/",
                      title="BssAPI", description="Функционал перефирийного взаимодействия "
                                                  "корпоративной учетной системы BSS",
                      default_response_class=UJSONResponse,
                      routes=router.routes)


async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                        content={
                            "detail": jsonable_encoder(exc.errors()),
                            "body": jsonable_encoder(exc.body) if exc.body else None
                        })


api.add_exception_handler(RequestValidationError, request_validation_exception_handler)

app = uvicorn.Server(
    uvicorn.Config(app='bssapi:api', debug=api.debug, limit_max_requests=10000, host="0.0.0.0", use_colors=True,
                   workers=6)).run
