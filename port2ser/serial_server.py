from .parser import Parser
from .packet import Packet
from loguru import logger
import asyncio
import serial_asyncio
import serial
import struct

class SerialServer:
    def __init__(self, client):
        self.client = client

    def send_cmd(self, cmd_code):
        self.writer.write( struct.pack( "BBBBB",  0x19, 0x74, cmd_code, 0x00, 0x00  ))

    def send_data(self, data):
        data_len = len(data)
        self.writer.write( struct.pack( "BBBBB",  0x19, 0x74, cmd_code, data_len / 256, data_len % 256  ))
        self.writer.write(data)

    async def flush(self):
        await self.writer.drain()


    async def open_serial_port(self,url):
        self.reader, self.writer = await serial_asyncio.open_serial_connection(url=url, baudrate=30000, bytesize=8, parity='N', stopbits=serial.STOPBITS_ONE, xonxoff=1, rtscts=0 )
        self.parser = Parser(self.reader) 


    async def connect_to_remote(self):
        logger.info( "Connecting remote" )
        self.send_cmd(Packet.CMD_RESET)        
        await self.flush()
        while True:
            pkt = await self.parser.parse()
            if pkt.cmd == Packet.CMD_RESET_OK:
                break

            if pkt.cmd == Packet.CMD_RESET:
                self.send_cmd(Packet.CMD_RESET_OK)
                break

            logger.info("Wait connect remote, drop unknown packet: 0x%x" % pkt.cmd)

        logger.info("Remote connected")


    async def connect_remote(self, url):
        await self.open_serial_port(url)
        await self.connect_to_remote()

    async def read_proc(self):
        while True:
            pkt = await self.parse.parse()

            if pkt.cmd == Packet.CMD_DATA:
                self.client.on_recv( pkt.buf )
            else if pkt.cmd == Packet.CMD_CONNECT:
                await self.client.on_socket_connect()
            else if pkt.cmd == Packet.CMD_DISCONNECT:
                await self.on_socket_disconnect() 
            else if pkt.cmd == Packet.CMD_RESET:
                self.send_cmd(Packet.CMD_RESET_OK)
                await self.on_socket_disconnect() 

