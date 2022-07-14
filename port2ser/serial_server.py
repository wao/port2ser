from .parser import Parser
from .packet import Packet
from loguru import logger
from .transport_server import TransportServer
import asyncio
import serial_asyncio
import serial
import struct
import traceback

BAUDRATE=3000000

class SerialServer(TransportServer):
    def __init__(self, url, client_mgr):
        super.__init__(client_mgr)
        self.url = url

    async def open_transport(self):
        reader, writer = await serial_asyncio.open_serial_connection(url=self.url, baudrate=BAUDRATE, bytesize=8, parity='N', stopbits=serial.STOPBITS_ONE, xonxoff=0, rtscts=True, dsrdtr=True )
        await self.connect_transport(reader, writer)
