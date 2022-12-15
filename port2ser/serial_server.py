from .parser import Parser
from .packet import Packet
from loguru import logger
from .transport_server import Transport
import asyncio
import serial_asyncio
import serial
import struct
import traceback

#BAUDRATE=3000000
BAUDRATE=230400

class SerialServer:
    def __init__(self, url, client_mgr):
        self.transport = Transport(client_mgr)
        self.url = url

    async def run(self):
        while True:
            #reader, writer = await serial_asyncio.open_serial_connection(url=self.url, baudrate=BAUDRATE, bytesize=8, parity='N', stopbits=serial.STOPBITS_ONE, xonxoff=0, rtscts=True, dsrdtr=True )
            reader, writer = await serial_asyncio.open_serial_connection(url=self.url, baudrate=BAUDRATE, bytesize=8, parity='N', stopbits=serial.STOPBITS_ONE, xonxoff=0, rtscts=False, dsrdtr=False )
            await self.transport.on_connect(reader, writer)
