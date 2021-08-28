class Packet:
    MAGIC_0 = 0x19
    MAGIC_1 = 0x74

    CMD_DATA = 0x01
    CMD_RESET = 0x02
    CMD_RESET_OK = 0x03
    CMD_RESET_DONE = 0x04
    CMD_CONNECT = 0x05
    CMD_DISCONNECT = 0x06

    def __init__(self, cmd, buf):
        self.cmd = cmd
        self.buf = buf
