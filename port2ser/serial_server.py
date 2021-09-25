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


    def __init__(self, url, client_mgr):
        self.client_mgr = client_mgr
        self.url = url
        self.recv_cnt = 0
        self.send_cnt = 0
        self.cookie = -1

    def send_cmd(self, cmd_code, link_id):
        logger.info("[%d] Send cmd %d to %s" % ( link_id, cmd_code, self.url ) )
        self.writer.write( struct.pack( "BBBBBBBBBB",0x19, 0x19, 0x19, 0x19, 0x19, 0x74, cmd_code, link_id, 0x00, 0x00  ))

    def write(self, link_id, data):
        self.cmd_data(link_id, data)

    def cmd_data(self, link_id, data):
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
        header = struct.pack( "BBBBBBBBBB", 0x19, 0x19, 0x19, 0x19, 0x19, 0x74, Packet.CMD_DATA, link_id, data_len % 256, data_len // 256  )
        ret = struct.unpack( "BBBBBBBBBB", header )
        if data_len != ret[8] + ret[9] * 256:
            logger.error("wrong data length expect %d but 0x%x 0x%x" % ( data_len, ret[8], ret[9] ) )
            raise Exception("Fatal error")

        self.writer.write( struct.pack( "BBBBBBBBBB", 0x19, 0x19, 0x19, 0x19, 0x19, 0x74, Packet.CMD_DATA, link_id, data_len % 256, data_len // 256  ))
        self.writer.write(data)

    def cmd_disconnect(self, link_id):
        self.send_cmd(Packet.CMD_DISCONNECT, link_id)

    def cmd_connect(self, link_id):
        self.send_cmd(Packet.CMD_CONNECT, link_id)

    async def read_proc(self):
        try:
            while True:
                #logger.info( "Wait  data from serial port " + self.url)
                pkt = await self.parser.parse()
                #logger.info( "Recv pkt type 0x%x" % pkt.cmd )

                if pkt.cmd == Packet.CMD_DATA:
                    self.recv_cnt += len(pkt.buf)
                    logger.info("Recv data total %d" % self.recv_cnt) 
                    self.client_mgr.on_recv( pkt.link_id, pkt.buf )
                elif pkt.cmd == Packet.CMD_CONNECT:
                    await self.client_mgr.on_socket_connect(pkt.link_id)
                elif pkt.cmd == Packet.CMD_DISCONNECT:
                    await self.client_mgr.on_socket_disconnect(pkt.link_id) 
                elif pkt.cmd == Packet.CMD_RESET:
                    self.send_cmd(Packet.CMD_RESET_OK, 0)
                    await self.client_mgr.on_socket_disconnect_all() 
                elif pkt.cmd == Packet.CMD_RESET_OK:
                    # ingore it
                    pass
                else:
                    logger.warning( "Uknown pkt type 0x%x" % pkt.cmd )

        except Exception as e:
            logger.error( "Got exception %s" % e )
            traceback.print_tb(e.__traceback__)

    async def flush(self):
        await self.writer.drain()


    async def open_serial_port(self):
        self.reader, self.writer = await serial_asyncio.open_serial_connection(url=self.url, baudrate=BAUDRATE, bytesize=8, parity='N', stopbits=serial.STOPBITS_ONE, xonxoff=0, rtscts=True, dsrdtr=True )
        self.parser = Parser(self.reader) 


    async def connect_to_remote(self):
        logger.info( "Connecting remote" )
        self.send_cmd(Packet.CMD_RESET, 0)        
        await self.flush()
        while True:
            pkt = await self.parser.parse()
            if pkt.cmd == Packet.CMD_RESET_OK:
                break
            elif pkt.cmd == Packet.CMD_RESET:
                self.send_cmd(Packet.CMD_RESET_OK, 0)
                break
            else:
                logger.info("Wait connect remote, drop unknown packet: 0x%x" % pkt.cmd)

        logger.info("Remote connected")


    async def setup_serial(self):
        await self.open_serial_port()
        await self.connect_to_remote()

