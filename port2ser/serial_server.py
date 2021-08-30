from .parser import Parser
from .packet import Packet
from loguru import logger
import asyncio
import serial_asyncio
import serial
import struct
import traceback

BAUDRATE=3000000

class SerialServer:


    def __init__(self, url, client):
        self.client = client
        self.url = url
        self.recv_cnt = 0
        self.send_cnt = 0
        self.cookie = -1

    def send_cmd(self, cmd_code):
        logger.info("Send cmd %d to %s" % ( cmd_code, self.url ) )
        self.writer.write( struct.pack( "BBBBBBBBB",0x19, 0x19, 0x19, 0x19, 0x19, 0x74, cmd_code, 0x00, 0x00  ))

    def write(self, data):
        self.cmd_data(data)

    def cmd_data(self, data):
        if data == None:
            logger.error("Skip None data")
            return

        data_len = len(data)
        if data_len == 0:
            logger.error("Skip empty data")
            return

        self.send_cnt += data_len
        logger.info( "Total send %d" % self.send_cnt )

        #logger.error("Send data to %s and len %d" % ( self.url, data_len ) )
        ##logger.info(b"Data:" + data )
        header = struct.pack( "BBBBBBBBB", 0x19, 0x19, 0x19, 0x19, 0x19, 0x74, Packet.CMD_DATA, data_len % 256, data_len // 256  )
        ret = struct.unpack( "BBBBBBBBB", header )
        if data_len != ret[7] + ret[8] * 256:
            logger.error("wrong data length expect %d but 0x%x 0x%x" % ( data_len, ret[6], ret[7] ) )
            raise Exception("Fatal error")

        self.writer.write( struct.pack( "BBBBBBBBB", 0x19, 0x19, 0x19, 0x19, 0x19, 0x74, Packet.CMD_DATA, data_len % 256, data_len // 256  ))
        self.writer.write(data)

    def cmd_disconnect(self):
        self.send_cmd(Packet.CMD_DISCONNECT)

    def cmd_connect(self):
        self.send_cmd(Packet.CMD_CONNECT)

    async def flush(self):
        await self.writer.drain()


    async def open_serial_port(self):
        #self.reader, self.writer = await serial_asyncio.open_serial_connection(url=self.url, baudrate=BAUDRATE, bytesize=8, parity='N', stopbits=serial.STOPBITS_ONE, xonxoff=0, rtscts=1 )
        self.reader, self.writer = await serial_asyncio.open_serial_connection(url=self.url, baudrate=BAUDRATE, bytesize=8, parity='N', stopbits=serial.STOPBITS_ONE, xonxoff=1, rtscts=0 )
        self.parser = Parser(self.reader) 


    async def connect_to_remote(self):
        logger.info( "Connecting remote" )
        self.send_cmd(Packet.CMD_RESET)        
        await self.flush()
        while True:
            pkt = await self.parser.parse()
            if pkt.cmd == Packet.CMD_RESET_OK:
                break
            elif pkt.cmd == Packet.CMD_RESET:
                self.send_cmd(Packet.CMD_RESET_OK)
                break
            else:
                logger.info("Wait connect remote, drop unknown packet: 0x%x" % pkt.cmd)

        logger.info("Remote connected")


    async def setup_serial(self):
        await self.open_serial_port()
        await self.connect_to_remote()

    async def read_proc(self):
        try:
            while True:
                #logger.info( "Wait  data from serial port " + self.url)
                pkt = await self.parser.parse()
                #logger.info( "Recv pkt type 0x%x" % pkt.cmd )

                if pkt.cmd == Packet.CMD_DATA:
                    self.recv_cnt += len(pkt.buf)
                    logger.info("Recv data total %d" % self.recv_cnt) 
                    self.client.on_recv( pkt.buf )
                elif pkt.cmd == Packet.CMD_CONNECT:
                    await self.client.on_socket_connect()
                elif pkt.cmd == Packet.CMD_DISCONNECT:
                    await self.client.on_socket_disconnect() 
                elif pkt.cmd == Packet.CMD_RESET:
                    self.send_cmd(Packet.CMD_RESET_OK)
                    await self.client.on_socket_disconnect() 
                elif pkt.cmd == Packet.CMD_RESET_OK:
                    # ingore it
                    pass
                else:
                    logger.warning( "Uknown pkt type 0x%x" % pkt.cmd )

        except Exception as e:
            logger.error( "Got exception %s" % e )
            traceback.print_tb(e.__traceback__)


        #logger.error("Send data to %s and len %d" % ( self.url, data_len ) )
        ##logger.info(b"Data:" + data )
        header = struct.pack( "BBBBBBBBB", 0x19, 0x19, 0x19, 0x19, 0x19, 0x74, Packet.CMD_DATA, data_len % 256, data_len // 256  )
        ret = struct.unpack( "BBBBBBBBB", header )
        if data_len != ret[7] + ret[8] * 256:
            logger.error("wrong data length expect %d but 0x%x 0x%x" % ( data_len, ret[6], ret[7] ) )
            raise Exception("Fatal error")

        self.writer.write( struct.pack( "BBBBBBBBB", 0x19, 0x19, 0x19, 0x19, 0x19, 0x74, Packet.CMD_DATA, data_len % 256, data_len // 256  ))
        self.writer.write(data)

    def cmd_disconnect(self):
        self.send_cmd(Packet.CMD_DISCONNECT)

    def cmd_connect(self):
        self.send_cmd(Packet.CMD_CONNECT)

    async def flush(self):
        await self.writer.drain()


    async def open_serial_port(self):
        self.reader, self.writer = await serial_asyncio.open_serial_connection(url=self.url, baudrate=BAUDRATE, bytesize=8, parity='N', stopbits=serial.STOPBITS_ONE, xonxoff=1, rtscts=0 )
        self.parser = Parser(self.reader) 


    async def connect_to_remote(self):
        logger.info( "Connecting remote" )
        self.send_cmd(Packet.CMD_RESET)        
        await self.flush()
        while True:
            pkt = await self.parser.parse()
            if pkt.cmd == Packet.CMD_RESET_OK:
                break
            elif pkt.cmd == Packet.CMD_RESET:
                self.send_cmd(Packet.CMD_RESET_OK)
                break
            else:
                logger.info("Wait connect remote, drop unknown packet: 0x%x" % pkt.cmd)

        logger.info("Remote connected")


    async def setup_serial(self):
        await self.open_serial_port()
        await self.connect_to_remote()

    async def read_proc(self):
        try:
            while True:
                #logger.info( "Wait  data from serial port " + self.url)
                pkt = await self.parser.parse()
                #logger.info( "Recv pkt type 0x%x" % pkt.cmd )

                if pkt.cmd == Packet.CMD_DATA:
                    self.recv_cnt += len(pkt.buf)
                    logger.error("Recv data total len %d" % self.recv_cnt)
                    self.client.on_recv( pkt.buf, self.cookie )
                elif pkt.cmd == Packet.CMD_CONNECT:
                    self.cookie = await self.client.on_socket_connect()
                elif pkt.cmd == Packet.CMD_DISCONNECT:
                    await self.client.on_socket_disconnect(self.cookie) 
                elif pkt.cmd == Packet.CMD_RESET:
                    self.send_cmd(Packet.CMD_RESET_OK)
                    await self.client.on_socket_disconnect(self.cookie) 
                elif pkt.cmd == Packet.CMD_RESET_OK:
                    # ingore it
                    pass
                else:
                    logger.info( "Uknown pkt type 0x%x" % pkt.cmd )

        except Exception as e:
            logger.error( "Got exception %s" % e )
            traceback.print_tb(e.__traceback__)

