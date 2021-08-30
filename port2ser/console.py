import asyncio
from .port2ser import Ser2Port, Port2Ser
import sys
from loguru import logger

def ser2port():
    logger.add(sys.stderr, level="ERROR")
    url = "/dev/ttyUSB0"
    if len(sys.argv) > 1:
        url = sys.argv[1]

    srv = Ser2Port()
    asyncio.run(srv.run(url))

def port2ser():
    url = "/dev/ttyUSB0"
    if len(sys.argv) > 1:
        url = sys.argv[1]

    srv = Port2Ser()
    asyncio.run(srv.run(url))
