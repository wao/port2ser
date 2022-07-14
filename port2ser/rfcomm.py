from loguru import logger
from .transport_server import TransportServer
import asyncio

import socket

BAUDRATE=3000000

class RfcommClient(TransportServer):
    def __init__(self, client_mgr):
        super().__init__(client_mgr)

    async def open_transport(self):
        serverMACAddress = '00:15:83:46:BA:C5'
        port = 13
        s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        reader, writer = await asyncio.open_connection(serverMACAddress, port, sock=s)
        await self.connect_transport(reader, writer)
