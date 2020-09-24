import io

from unittest import TestCase

from bssapi_schemas import exch
from fastapi import UploadFile
from pydantic import AnyUrl, BaseModel, StrictStr, Field

from bssapi.api.router.parser.dbf import parse_format, parse_source
import pytest


class test_parser_dbf(TestCase):
    filename = 'S0041283.dbf'
    url = AnyUrl(None, scheme="ftp", user="user",
                 password="password", host="santens.ru",
                 port="21", path="/path/to/folder/")
    file = UploadFile(filename=filename, content_type='application/octet-stream',
                      file=io.BytesIO(open(filename, mode='rb').read()))

    @pytest.mark.asyncio
    async def test_parser_dbf_source(self):
        filename = 'S0041283.dbf'
        assert isinstance(await parse_source(**self), exch.Packet)

    @pytest.mark.asyncio
    async def test_parser_dbf_packet(self):
        assert isinstance(await parse_format(request=None, **self), exch.FormatPacket)


class test_model(TestCase):

    class Mod(BaseModel):
        name: str = Field(regex="^[0-9]+$")

    def test_regex(self):
        self.Mod(name="ivan")
