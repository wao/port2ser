import asyncio
from loguru import logger

class DataForwarder:
    def __init__(self, name, reader, writer):
        self.reader = reader
        self.writer = writer
        self.name = name

    async def run(self):

        logger.info( "%s begin to forward data" % self.name )

        while True:
            data = await self.reader.read(64*1024)
            if len(data) == 0:
                logger.info( "%s stop to forward data" % self.name )
                self.writer.close()
                self.reader.close()
                break
            else:
                self.writer.write(data)

    def start(self):
        self.task = asyncio.create_task(self.run())
