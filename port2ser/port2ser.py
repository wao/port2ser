import serial
import asyncio
import serial_asyncio
from loguru import logger
from .serial_server import SerialServer
import traceback

class Connection:
    def __init__(self, link_id, reader, writer):
        self.link_id = link_id
        self.reader = reader
        self.writer = writer

class TcpServer:
    def __init__(self, serial, port):
        super().__init__()
        self.port = port
        self.serial = serial
        self.instance_id = 0
        self.next_link_id = 1
        self.links = {}


    async def handle_echo(self, reader, writer):
        try:
            local_link_id = self.next_link_id % 256
            self.next_link_id += 1

            self.links[local_link_id] = Connection(local_link_id, reader, writer)

            logger.info("TCP Server got tcp connection for id %d " % local_link_id)
            self.serial.cmd_connect(local_link_id)

            while True:
                data = await reader.read(64*1024)
                if len(data) == 0:
                    self.serial.cmd_disconnect(local_link_id)
                    break
                    
                self.serial.cmd_data(local_link_id, data)
                await self.serial.flush()

            logger.info("Close the connection for id %d " % local_link_id)
        except Exception as e:
            logger.error("Got unknown exception %s" % e )
            traceback.print_tb(e.__traceback__)
        
        #TODO: need to clean leaked linkid here

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

    def write(self, link_id, data):
        self.links[link_id].writer.write(data)

    def close(self, link_id):
        if link_id in self.links:
            self.links[link_id].writer.close()

    def close_all(self):
        for link_id, link in self.links.items():
            link.writer.close()

tcp_instance_cnt = 0

class TcpClient:
    def __init__(self, link_id, serial_writer, port):
        super().__init__()
        self.link_id = link_id
        self.port = port
        self.serial_writer = serial_writer
        logger.info( "TcpClient: serial_writer %s" % str(self.serial_writer) )

    def start(self):
        self.task = asyncio.create_task(self.run())

    @staticmethod
    async def connect(link_id, writer, port):
        inst = TcpClient(link_id, writer, port)
        await inst.internal_connect()
        return inst

    async def internal_connect(self):
        self.reader, self.writer = await asyncio.open_connection('127.0.0.1', self.port )

    def write(self, data):
        self.writer.write(data)

    async def run(self):
        while True:
            #logger.info( "TcpClient[%d]: Wait data from tcp client socket" % self.link_id )
            data = await self.reader.read(64*1024)
            #logger.info("TcpClinet[%d]: got data from tcp len %d" %( self.link_id, len(data)))

            if len(data) == 0:
                self.serial_writer.cmd_disconnect(self.link_id)
                break

            self.serial_writer.write(self.link_id, data)
        
    def close(self):
        self.writer.close()


class Ser2Port:
    def __init__(self):
        self.tcps = {}

    async def run(self, url, port = 24800):
        self.port = port
        self.tcp_create_event = asyncio.Event()
        self.serial = SerialServer(url, self)
        logger.info( "Ser2Port setup serial")
        await self.serial.setup_serial()
        await asyncio.gather( self.serial.read_proc(), self.tcp_to_serial_proc() )
        logger.info( "run end" )

    async def tcp_to_serial_proc(self):
        self.create_evt_task = asyncio.create_task(self.tcp_create_event.wait())
        while True:
            logger.info( "wait for connect/disconnect event" )
            await asyncio.wait([self.create_evt_task] + [ v.task for v in self.tcps.values()])
            if self.tcp_create_event.is_set():
                self.tcp_create_event.clear()
                self.create_evt_task = asyncio.create_task(self.tcp_create_event.wait())
            


    async def on_socket_connect(self, link_id):
        logger.info( "connecting TcpClient for %d " % link_id )
        self.tcps[link_id] = await TcpClient.connect(link_id, self.serial, self.port)
        self.tcps[link_id].start()
        logger.info( "connected TcpClient for %d " % link_id )
        self.tcp_create_event.set()


    def on_recv(self, link_id, data ):
        self.tcps[link_id].write(data)

    async def on_socket_disconnect(self, link_id):
        if link_id in self.tcps:
            self.tcps[link_id].close()
            del self.tcps[link_id]
            self.tcp_create_event.set()

    async def on_socket_disconnect_all(self):
        for conn_id, conn in self.tcps.items():
            conn.close()

        self.tcps.clear()
        self.tcp_create_event.set()


class Port2Ser:
    async def run(self, url, port = 24800):
        self.port = port
        self.serial = SerialServer(url, self)
        logger.info( "Port2Ser setup serial")
        await self.serial.setup_serial()
        self.tcp = TcpServer(self.serial, self.port)
        await asyncio.gather( self.serial.read_proc(), self.tcp.run() )
        logger.info( "run end" )

    def on_recv(self, link_id, data):
        self.tcp.write(link_id, data)

    async def on_socket_disconnect(self, link_id):
        self.tcp.close(link_id)

    async def on_socket_disconnect_all(self):
        self.tcp.close_all()
