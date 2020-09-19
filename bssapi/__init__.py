__version__ = '0.1.0'
__all__ = [r'api', r'app']


import uvicorn
import fastapi.middleware
import fastapi.middleware.gzip

from .api.router import router

api = fastapi.FastAPI(debug=True, version=__version__,
                      middleware=[fastapi.middleware.Middleware(fastapi.middleware.gzip.GZipMiddleware, minimum_size=100)])

api.include_router(router=router)

app = uvicorn.Server(uvicorn.Config(app=r'bssapi:api', debug=api.debug)).run
