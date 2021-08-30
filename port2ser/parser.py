from .packet import Packet
from loguru import logger

class Parser:
    def __init__(self, reader):
        self.buf = None
        self.buf_off = 0
        self.buf_len = 0
        self.reader = reader

    async def parse(self):
        await self.read_magic()
        cmd = await self.read_cmd()
        buf_len = await self.read_len()
        #logger.info( "Read buf len %d" % buf_len )
        if buf_len > 0:
            buf = await self.read_buf(buf_len)
        else:
            buf = None

        return Packet(cmd, buf)

    async def read_magic(self):
        while True:
            #wait magic 0
            magic_0 = await self.read_char()
            if magic_0 != Packet.MAGIC_0:
                logger.error( "Expect MAGIC_0 but get get 0x%x" % magic_0 )
                continue

            magic_1 = await self.read_char()
            while magic_1 == Packet.MAGIC_0:
                magic_1 = await self.read_char()

            if magic_1 != Packet.MAGIC_1:
                logger.error( "Expect MAGIC_1 but get get 0x%x" % magic_1 )
                continue

            return

    async def read_cmd(self):
        return await self.read_char()

    async def read_len(self):
        len_0 = await self.read_char()
        len_1 = await self.read_char()

        return len_1 * 256 + len_0
        

    async def read_buf(self, buf_len):
        ret = []
        while buf_len > 0:
            await self.load_if_empty()
            copy_len = min( self.buf_len, buf_len )
            ret.append(self.buf[self.buf_off:self.buf_off + copy_len])
            self.buf_off += copy_len
            self.buf_len -= copy_len
            buf_len -= copy_len

        if len(ret) == 1:
            return ret[0]
        else:
            return b"".join(ret)

    async def read_char(self):
        await self.load_if_empty()
        ret = self.buf[self.buf_off]
        self.buf_off += 1
        self.buf_len -= 1
        return ret

    async def load_if_empty(self):
        if self.buf_len <= 0:
            self.buf = await self.reader.read(128*1024)
            self.buf_off = 0
            self.buf_len = len(self.buf)
            logger.info( b"read data from serail " + self.buf )
            ##logger.info( "Data len %d" % self.buf_len )
