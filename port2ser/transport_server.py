from .parser import Parser
from .packet import Packet
from loguru import logger
import asyncio
import serial_asyncio
import serial
import struct
import traceback
import base64

BAUDRATE=3000000
class Transport:
    def __init__(self, client_mgr):
        self.client_mgr = client_mgr
        self.recv_cnt = 0
        self.send_cnt = 0
        self.cookie = -1
        self.reader = None
        self.writer = None 

    async def on_connect(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.parser = Parser(self.reader) 
        await self.read_proc()
        self.writer.close()
        await self.writer.wait_closed()

    def send_cmd(self, cmd_code, link_id):
        logger.info("[%d] Send cmd %d" % ( link_id, cmd_code ) )
        if self.writer == None:
            logger.error( "[%d] Tranport doesn't connected, skip send cmd %d" % ( link_id, cmd_code ) )
        else:
            self.writer.write( struct.pack( "BBBBBBBBBB",0x19, 0x19, 0x19, 0x19, 0x19, 0x74, cmd_code, link_id, 0x00, 0x00  ))

    def write(self, link_id, data):
        self.cmd_data(link_id, data)

    def internal_cmd_data_pkt(self, link_id, data_off, data_len, data):
        #logger.error("Send data to %s and len %d" % ( self.url, data_len ) )
        ##logger.info(b"Data:" + data )
        #logger.error("3Send data off %d, len %d" % (data_off, data_len))
        #header = struct.pack( "BBBBBBBBBB", 0x19, 0x19, 0x19, 0x19, 0x19, 0x74, Packet.CMD_DATA, link_id, data_len % 256, data_len // 256  )
        #ret = struct.unpack( "BBBBBBBBBB", header )
        #if data_len != ret[8] + ret[9] * 256:
        #    logger.error("wrong data length expect %d but 0x%x 0x%x" % ( data_len, ret[8], ret[9] ) )
        #    raise Exception("Fatal error")

        self.writer.write( struct.pack( "BBBBBBBBBB", 0x19, 0x19, 0x19, 0x19, 0x19, 0x74, Packet.CMD_BASE64, link_id, data_len % 256, data_len // 256  ))
        self.writer.write(data[data_off:data_off+data_len])
        self.send_cnt += data_len

    def cmd_data(self, link_id, data):
        if data == None:
            logger.error("Skip None data")
            return

        if self.writer == None:
            logger.error( "[%d] Tranport doesn't connected, skip send data" % ( link_id ) )
            return

        data = base64.b64encode(data)

        data_len = len(data)
        data_off = 0
        #logger.error("1Send data off %d, len %d" % (data_off, data_len))
        while data_off < data_len:
            send_len = data_len - data_off
            if send_len > 255 * 256:
                send_len = 255 * 256
            #logger.error("2Send data off %d, len %d" % (data_off, send_len))
            self.internal_cmd_data_pkt(link_id, data_off, send_len, data)
            data_off += send_len

        #logger.info( "Total send %d" % self.send_cnt )


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
                    #logger.info("Recv data total %d" % self.recv_cnt) 
                    self.client_mgr.on_recv( pkt.link_id, pkt.buf )
                if pkt.cmd == Packet.CMD_BASE64:
                    self.recv_cnt += len(pkt.buf)
                    #logger.info("Recv data total %d" % self.recv_cnt) 
                    self.client_mgr.on_recv( pkt.link_id, base64.b64decode(pkt.buf) )
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
            logger.exception( "Got exception %s" % e )
            #  traceback.print_tb(e.__traceback__)

    async def flush(self):
        await self.writer.drain()

"""
    async def connect_transport(self, reader, writer):
        await self.connect_to_remote()

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
"""
