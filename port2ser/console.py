import asyncio
from .port2ser import Ser2Port, Port2Ser

def ser2port():
    srv = Ser2Port()
    asyncio.run(srv.run("/dev/ttyUSB0"))

def port2ser():
    srv = Port2Ser()
    asyncio.run(srv.run("/dev/ttyUSB1"))
