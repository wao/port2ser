import serial
import asyncio
import serial_asyncio
from loguru import logger
from .serial_server import SerialServer
import traceback
from .tcp import TcpManager


class Ser2Port:
    def __init__(self):
        self.tcps = {}

    async def run(self, url, port = 24800):
        tcp_mgr = TcpManager(port)
        serial = SerialServer(url, tcp_mgr.connection_manager)
        tcp_mgr.set_transport(serial.transport)
        logger.info( "server started" )
        await asyncio.gather( serial.run() )
        logger.info( "server end" )



class Port2Ser:
    async def run(self, url, port = 24800):
        tcp_mgr = TcpManager(port)
        serial = SerialServer(url, tcp_mgr.connection_manager)
        tcp_mgr.set_transport(serial.transport)
        logger.info( "server started" )
        await asyncio.gather( serial.run(), tcp_mgr.run_server() )
        logger.info( "server end" )
