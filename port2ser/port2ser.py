import serial
import asyncio
import serial_asyncio
from loguru import logger
from .serial_server import SerialServer
import traceback

class TcpClosable:
    def __init__(self):
        self.is_closed = False

    def close(self):
        if not self.is_closed:
            self.is_closed = True
            self.writer.close()

class TcpServer(TcpClosable):
    def __init__(self, serial, port):
        super().__init__()
        self.port = port
        self.serial = serial

    async def handle_echo(self, reader, writer):
        try:
            logger.info("Port2ser got tcp connection")
            self.serial.cmd_connect()
            self.writer = writer
            self.reader = reader

            self.is_closed = False

            while True:
                data = await reader.read(64*1024)
                if len(data) == 0:
                    self.serial.cmd_disconnect()
                    break
                    
                self.serial.cmd_data(data)
                await self.serial.flush()
                logger.info( "data sended" )

            logger.info("Close the connection")
        except Exception as e:
            logger.error("Got unknown exception %s" % e )
            traceback.print_tb(e.__traceback__)

        self.close()

    async def run(self):
        server = await asyncio.start_server(
            self.handle_echo, '127.0.0.1', self.port)

        addr = server.sockets[0].getsockname()
        logger.info(f'Port2ser Serving on {addr}')

        async with server:
            await server.serve_forever()

    def write(self, data):
        self.writer.write(data)



class TcpClient(TcpClosable):
    def __init__(self, serial_writer, port):
        super().__init__()
        self.port = port
        self.serial_writer = serial_writer

    @staticmethod
    async def connect(writer, port):
        inst = TcpClient(writer, port)
        await inst.internal_connect()
        return inst

    async def internal_connect(self):
        self.reader, self.writer = await asyncio.open_connection('127.0.0.1', self.port )

    def write(self, data):
        self.writer.write(data)

    async def run(self):
        while True:
            logger.info( "Wait data from tcp client socket" )
            data = await self.reader.read(64*1024)
            logger.info("got data from tcp")
            if len(data) == 0:
                self.serial_writer.cmd_disconnect()
                break
            self.serial_writer.write(data)

        self.close()


class Ser2Port:
    def __init__(self):
        self.tcp = None

    async def run(self, url, port = 24800):
        self.port = port
        self.tcp_create_event = asyncio.Event()
        self.serial = SerialServer(url, self)
        logger.info( "Ser2Port setup serial")
        await self.serial.setup_serial()
        await asyncio.gather( self.serial.read_proc(), self.tcp_to_serial_proc() )
        logger.info( "run end" )

    async def tcp_to_serial_proc(self):
        while True:
            await self.tcp_create_event.wait()
            self.tcp_create_event.clear()
            await self.tcp.run()

    async def on_socket_connect(self):
        logger.info( "connecting TcpClient" )
        self.tcp = await TcpClient.connect(self.serial, self.port)
        logger.info( "connected TcpClient" )
        self.tcp_create_event.set()


    def on_recv(self, data):
        self.tcp.write(data)

    async def on_socket_disconnect(self):
        if self.tcp:
            self.tcp.close()
            self.tcp = None

class Port2Ser:
    async def run(self, url, port = 24800):
        self.port = port
        self.serial = SerialServer(url, self)
        logger.info( "Port2Ser setup serial")
        await self.serial.setup_serial()
        self.tcp = TcpServer(self.serial, self.port)
        await asyncio.gather( self.serial.read_proc(), self.tcp.run() )
        logger.info( "run end" )

    def on_recv(self, data):
        self.tcp.write(data)

    async def on_socket_disconnect(self):
        self.tcp.close()
