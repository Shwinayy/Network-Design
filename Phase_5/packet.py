from __future__ import annotations

import random
import struct
from dataclasses import dataclass

TYPE_DATA = 0
TYPE_ACK = 1
TYPE_CTRL = 2

FLAG_EOF = 0x01
NO_ACK = 0xFFFFFFFF

# type(1) seq(4) ack(4) rwnd(4) length(2) flags(1) checksum(2)
HEADER_STRUCT = struct.Struct("!BIIIHBH")
HEADER_SIZE = HEADER_STRUCT.size


@dataclass(slots=True)
class Packet:
    pkt_type: int
    seq: int = 0
    ack: int = NO_ACK
    rwnd: int = 0         
    flags: int = 0
    payload: bytes = b""

    def encode(self) -> bytes:
        payload = self.payload or b""
        header_wo_checksum = HEADER_STRUCT.pack(
            self.pkt_type,
            self.seq & 0xFFFFFFFF,
            self.ack & 0xFFFFFFFF,
            self.rwnd & 0xFFFFFFFF,  
            len(payload),
            self.flags & 0xFF,
            0,
        )
        checksum = internet_checksum(header_wo_checksum + payload)
        header = HEADER_STRUCT.pack(
            self.pkt_type,
            self.seq & 0xFFFFFFFF,
            self.ack & 0xFFFFFFFF,
            self.rwnd & 0xFFFFFFFF,   
            len(payload),
            self.flags & 0xFF,
            checksum,
        )
        return header + payload

    @classmethod
    def decode(cls, raw: bytes) -> "Packet":
        if len(raw) < HEADER_SIZE:
            raise ValueError("packet too short")
        pkt_type, seq, ack, rwnd, length, flags, checksum = HEADER_STRUCT.unpack(raw[:HEADER_SIZE])
        payload = raw[HEADER_SIZE:]
        if len(payload) != length:
            raise ValueError("payload length mismatch")
        zeroed = HEADER_STRUCT.pack(pkt_type, seq, ack, rwnd, length, flags, 0) + payload
        if internet_checksum(zeroed) != checksum:
            raise ValueError("checksum mismatch")
        return cls(pkt_type=pkt_type, seq=seq, ack=ack, rwnd=rwnd, flags=flags, payload=payload)

    @property
    def is_eof(self) -> bool:
        return bool(self.flags & FLAG_EOF)


def internet_checksum(data: bytes) -> int:
    if len(data) % 2 == 1:
        data += b"\x00"
    total = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i + 1]
        total += word
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def maybe_flip_one_bit(raw: bytes, probability: float, rng: random.Random) -> bytes:
    if probability <= 0.0 or rng.random() >= probability or not raw:
        return raw
    mutated = bytearray(raw)
    byte_index = rng.randrange(len(mutated))
    bit_index = rng.randrange(8)
    mutated[byte_index] ^= 1 << bit_index
    return bytes(mutated)
