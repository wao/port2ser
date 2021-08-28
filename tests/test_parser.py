from port2ser.parser import Parser
from port2ser.packet import Packet
import asyncio
import pytest

class FakeReader:
    def __init__(self, datas):
        self.datas = datas

    async def read(self, max_len):
        return self.datas.pop(0)

def fake_a_to_e():
    datas = FakeReader([b"a", b"bcd", b"e"])
    p = Parser(datas)
    return p


@pytest.mark.asyncio
async def test_readchar():
    p = fake_a_to_e()
    assert ord('a') == await p.read_char()
    assert ord('b') == await p.read_char()
    assert ord('c') == await p.read_char()
    assert ord('d') == await p.read_char()
    assert ord('e') == await p.read_char()

@pytest.mark.asyncio
async def test_readbuf():
    p = fake_a_to_e()
    assert b"abc" == await p.read_buf(3)
    assert b"de" == await p.read_buf(2)

def fake_reset_pkt():
    datas = FakeReader([ [ 0x19 ], [0x74 , Packet.CMD_RESET, 0, 0 ], "a" ])
    p = Parser(datas)
    return p

@pytest.mark.asyncio
async def test_parse_cmd_packet():
    p = fake_reset_pkt()
    pkt = await p.parse()
    assert pkt.cmd == Packet.CMD_RESET
    assert pkt.buf == None

def fake_data_pkt():
    datas = FakeReader([ [ 0x19 ], [0x74 , Packet.CMD_DATA, 5, 0 ], b"ab", b"cdefhij" ])
    p = Parser(datas)
    return p

@pytest.mark.asyncio
async def test_parse_data_packet():
    p = fake_data_pkt()
    pkt = await p.parse()
    assert pkt.cmd == Packet.CMD_DATA
    assert pkt.buf == b"abcde"

def fake_data_pkt_with_wrong_magic():
    datas = FakeReader([ b"wrong", [0x19], b"data", [ 0x19 ], [0x74 , Packet.CMD_DATA, 5, 0 ], b"ab", b"cdefhij" ])
    p = Parser(datas)
    return p

@pytest.mark.asyncio
async def test_parse_skip_none_magic():
    p = fake_data_pkt_with_wrong_magic()
    pkt = await p.parse()
    assert pkt.cmd == Packet.CMD_DATA
    assert pkt.buf == b"abcde"
