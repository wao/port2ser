from loguru import logger
import asyncio
import traceback

class Connection:
    def __init__(self, link_id, reader, writer):
        self.link_id = link_id
        self.reader = reader
        self.writer = writer

class ConnectionManager:
    def __init__(self, transport, tcp_client):
        self.transport = transport
        self.links = {}
        self.tcp_client = tcp_client

    async def handle_tcp_connection(self, link_id, tcp_reader, tcp_writer, accepted=True):
        try:
            assert link_id < 256, "link_id %d should less than 256" 
            assert not link_id in self.links, "link_id %d has already live" % link_id

            self.links[link_id] = Connection(link_id, tcp_reader, tcp_writer)

            if accepted:
                logger.info("TCP Server got tcp connection for id %d " % link_id)
                self.transport.cmd_connect(link_id)

            while True:
                data = await tcp_reader.read(64*1024)
                if len(data) == 0:
                    self.transport.cmd_disconnect(link_id)
                    break
                    
                self.transport.cmd_data(link_id, data)
                await self.transport.flush()

                logger.info("Close the connection for id %d " % link_id)

        except Exception as e:
            logger.error("Got unknown exception %s" % e )
            traceback.print_tb(e.__traceback__)

        await self.close(link_id)

        
    def write(self, link_id, data):
        self.links[link_id].writer.write(data)

    async def close(self, link_id):
        if link_id in self.links:
            self.links[link_id].writer.close()
            await self.links[link_id].writer.wait_closed()
            del self.links[link_id]


    async def close_all(self):
        for link_id, link in self.links.items():
            link.writer.close()
            await link.writer.wait_closed()

        self.links = {}


    async def on_socket_connect(self, link_id):
        logger.info( "connecting TcpClient for %d " % link_id )
        reader, writer = await self.tcp_client.connect()
        logger.info( "connected TcpClient for %d " % link_id )
        asyncio.create_task(self.handle_tcp_connection(link_id,reader, writer, False))

    def on_recv(self, link_id, data ):
        self.write(link_id, data)

    async def on_socket_disconnect(self, link_id):
            await self.close(link_id)

    async def on_socket_disconnect_all(self):
        await self.close_all()


class TcpServer:
    def __init__(self, connection_manager, port):
        super().__init__()
        self.port = port
        self.connection_manager = connection_manager
        self.instance_id = 0
        self.next_link_id = 1

    async def handle_echo(self, reader, writer):
        local_link_id = self.next_link_id % 256
        self.next_link_id += 1

        await self.connection_manager.handle_tcp_connection( local_link_id, reader, writer)

    async def run(self):
        server = await asyncio.start_server(
            self.handle_echo, '127.0.0.1', self.port)

        addr = server.sockets[0].getsockname()
        logger.info(f'Port2ser Serving on {addr}')

        try:
            async with server:
                await server.serve_forever()
        except Exception as e:
            logger.exception(e)

class TcpClient:
    def __init__(self, port):
        self.port = port

    async def connect(self):
        return await asyncio.open_connection('127.0.0.1', self.port )

class TcpManager:
    def __init__(self, transport, port):
        self.transport = transport
        self.port = port
        self.connection_manager = ConnectionManager(transport, TcpClient(port))

    async def run_server(self):
        tcp_server = TcpServer(self.connection_manager, self.port)

        await tcp_server.run()
