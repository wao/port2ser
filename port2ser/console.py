import serial
import asyncio
import serial_asyncio

class TcpServer:
    async def handle_echo(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received {message!r} from {addr!r}")

        print(f"Send: {message!r}")
        writer.write(data)
        await writer.drain()

        print("Close the connection")
        writer.close()

    async def run(self):
        server = await asyncio.start_server(
            self.handle_echo, '127.0.0.1', 8888)

        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')

        async with server:
            await server.serve_forever()




class TcpClient:
    def __init__(self, serial_writer):
        self.serial_writer = serial_writer

    @staticmethod
    async def connect(writer):
        inst = TcpClient(writer)
        await inst.internal_connect()
        return inst

    async def internal_connect(self):
        self.reader, self.writer = await asyncio.open_connection('127.0.0.1', 24800 )

    def write(self, data):
        self.writer.write(data)

    async def run(self):
        while True:
            data = await self.reader.read(128000)
            print("got data from tcp")
            self.serial_writer.write(data)
        


class SerialServer:
    def __init(self):
        self.tcp = None

    async def read(self):
        while True:
            data = await self.reader.read(128000)
            print("got data from ser len %d " % len(data))
            self.tcp.write(data)


    async def run(self):
        url = "/dev/ttyUSB0"
        self.reader, self.writer = await serial_asyncio.open_serial_connection(url=url, baudrate=115200, bytesize=8, parity='N', stopbits=serial.STOPBITS_ONE, xonxoff=1, rtscts=0 )
        print("wait data from ser")
        data = await self.reader.read(128000)
        print("connect tcp")
        self.tcp = await TcpClient.connect(self.writer)
        self.tcp.write(data)

        await asyncio.gather(self.read(), self.tcp.run())

def ser2port():
    print("hello world!")
    srv = SerialServer()
    asyncio.run(srv.run())

async def srv():
        url = "/dev/ttyUSB1"
        reader, writer = await serial_asyncio.open_serial_connection(url=url, baudrate=115200, bytesize=8, parity='N', stopbits=serial.STOPBITS_ONE, xonxoff=1, rtscts=0 )
        writer.write(b"hello world!")

def port2ser():
    asyncio.run(srv())
