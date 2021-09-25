from port2ser import __version__
from port2ser.port2ser import Ser2Port, Port2Ser

import asyncio
import pytest

async def tcp_echo_client(message):
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 28888)

    print(f'Echo Client: Send: {message!r}')
    writer.write(message.encode())

    data = await reader.read(100)
    print(f'Echo Client: Received: {data.decode()!r}')

    print('Echo Clinet: Close the connection')
    assert message == data
    writer.close()

class EchoServer:
    async def handle_echo(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Echo Sever: Received {message!r} from {addr!r}")

        print(f"Echo Server: Send: {message!r}")
        writer.write(data)
        await writer.drain()

        await asyncio.sleep(2)

        print("Echo Server: Close the connection")
        reader.close()
        writer.close()

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_echo, '127.0.0.1', 18888)

        addr = self.server.sockets[0].getsockname()
        print(f'Echo Serving on {addr}')

    async def run(self):
        async with self.server:
            await self.server.serve_forever()

def test_version():
    assert __version__ == '0.1.0'

async def ser2port():
    srv = Ser2Port()
    await srv.run("/dev/ttyUSB0", 18888)

async def port2ser():
    srv = Port2Ser()
    await srv.run("/dev/ttyUSB1", 28888)

async def two_tcp_echo_client():
    await asyncio.sleep(2)
    await tcp_echo_client( "Hello world! New world!" )
    await tcp_echo_client( "Hello world! Old world!" )
    await asyncio.sleep(2)
    await tcp_echo_client( "Hello world! New world! 1" )
    await tcp_echo_client( "Hello world! Old world! 2" )

async def echo():
    await asyncio.sleep(2)
    srv = EchoServer()
    await srv.start()
    await asyncio.gather( srv.run(), two_tcp_echo_client())

@pytest.mark.asyncio
async def test_full():
    await asyncio.gather( ser2port(), port2ser(), echo() )
