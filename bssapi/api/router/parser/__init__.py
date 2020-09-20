import fastapi
import starlette.responses

from . import dbf

router = fastapi.APIRouter(default_response_class=starlette.responses.UJSONResponse)
router.include_router(dbf.router, tags=["DBF"], prefix="/dbf")
