from loguru import logger
from .transport_server import Transport
from .tcp import TcpManager
import asyncio
import socket

class BtClient:
    def __init__(self, client_mgr):
        self.transport = Transport(client_mgr)

    async def run(self):
        serverMACAddress = '00:15:83:46:BA:C5'
        port = 13
        while True:
            s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            reader, writer = await asyncio.open_connection(serverMACAddress, port, sock=s)
            await self.transport.on_connect(reader, writer)


class BtServer:
    def __init__(self, client_mgr):
        self.transport = Transport(client_mgr)

    async def handle_client(self, reader, writer):
        await self.transport.on_connect(reader, writer)


    async def run(self):
        hostMACAddress = '00:15:83:46:BA:C5' # The MAC address of a Bluetooth adapter on the server. The server might have multiple Bluetooth adapters.
        port = 13 # 3 is an arbitrary choice. However, it must match the port used by the client.
        s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        s.bind((hostMACAddress,port))
        server = await asyncio.start_server(self.handle_client, sock=s)
        async with server:
            await server.serve_forever()


async def bt_run_srv(port = 24800):
    tcp_mgr = TcpManager(port)
    bt = BtServer(tcp_mgr.connection_manager)
    tcp_mgr.set_transport(bt.transport)
    logger.info( "server started" )
    await bt.run()

async def bt_run_clt(port = 24800):
    tcp_mgr = TcpManager(port)
    bt = BtServer(tcp_mgr.connection_manager)
    tcp_mgr.set_transport(bt.transport)
    logger.info( "server started" )
    await asyncio.gather( bt.run(), tcp_mgr.run_server())

def bt_srv():
    asyncio.run(bt_run_srv())

def bt_clt():
    asyncio.run(bt_run_clt())
