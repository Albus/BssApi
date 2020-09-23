
from pydantic import BaseModel, StrictStr, typing


class ContentType(BaseModel):
    type: StrictStr
    params: typing.List[StrictStr]

    @classmethod
    async def from_str(cls, content_type: StrictStr):
        content_type, *content_params = content_type.split(';')
        return cls(type=content_type, params=content_params)
