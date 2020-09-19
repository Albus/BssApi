import fastapi
from . import dbf

router = fastapi.APIRouter()
router.include_router(dbf.router, tags=["DBF"], prefix="/dbf")
