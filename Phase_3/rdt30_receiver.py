#!/usr/bin/env python3
"""
RDT 3.0 Receiver (same FSM as RDT 2.2 receiver, with practical EOF linger)
- handles DATA corruption/loss simulation
- re-ACKs duplicates
- after EOF, stays alive briefly to ACK duplicate EOF retransmissions
"""

import argparse
import random
import socket
import struct
import time
from typing import Tuple

HDR_LEN = 7
TYPE_DATA = 0
TYPE_ACK = 1
FLAG_EOF = 0x01


def internet_checksum(data: bytes) -> int:
    if len(data) % 2 == 1:
        data += b"\x00"
    s = 0
    for i in range(0, len(data), 2):
        w = (data[i] << 8) + data[i + 1]
        s += w
        s = (s & 0xFFFF) + (s >> 16)
    return (~s) & 0xFFFF


def pack_packet(pkt_type: int, seq: int, payload: bytes = b"", flags: int = 0) -> bytes:
    length = len(payload)
    hdr0 = struct.pack("!BBH", pkt_type, seq, length) + struct.pack("!H", 0) + struct.pack("!B", flags)
    cksum = internet_checksum(hdr0 + payload)
    hdr = struct.pack("!BBH", pkt_type, seq, length) + struct.pack("!H", cksum) + struct.pack("!B", flags)
    return hdr + payload


def unpack_header(pkt: bytes) -> Tuple[int, int, int, int, int]:
    if len(pkt) < HDR_LEN:
        raise ValueError("packet too short")
    pkt_type, seq, length = struct.unpack("!BBH", pkt[:4])
    cksum = struct.unpack("!H", pkt[4:6])[0]
    flags = pkt[6]
    return pkt_type, seq, length, cksum, flags


def is_corrupt(pkt: bytes) -> bool:
    return internet_checksum(pkt) != 0


def corrupt_bytes(data: bytes) -> bytes:
    if not data:
        return data
    b = bytearray(data)
    idx = random.randrange(len(b))
    bit = 1 << random.randrange(8)
    b[idx] ^= bit
    return bytes(b)


def run_receiver(args: argparse.Namespace) -> None:
    random.seed(args.seed)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.bind, args.port))

    expected = 0
    last_ack_seq = 1
    eof_seq = None
    eof_addr = None
    eof_linger_deadline = None

    with open(args.outfile, "wb") as out:
        print(f"[RECEIVER] listening on {args.bind}:{args.port}")

        while True:
            if eof_linger_deadline is not None:
                remaining = max(0.0, eof_linger_deadline - time.monotonic())
                if remaining == 0.0:
                    break
                sock.settimeout(remaining)
            else:
                sock.settimeout(None)

            try:
                pkt, addr = sock.recvfrom(args.mtu)
            except socket.timeout:
                break

            # Simulate channel issues after receive.
            if random.random() < args.data_loss:
                continue
            if random.random() < args.data_error:
                pkt = corrupt_bytes(pkt)

            try:
                pkt_type, seq, length, _, flags = unpack_header(pkt)
            except Exception:
                if eof_linger_deadline is None:
                    ack = pack_packet(TYPE_ACK, last_ack_seq)
                    sock.sendto(ack, addr)
                continue

            if pkt_type != TYPE_DATA:
                continue

            if is_corrupt(pkt):
                if eof_linger_deadline is None:
                    ack = pack_packet(TYPE_ACK, last_ack_seq)
                    sock.sendto(ack, addr)
                continue

            payload = pkt[HDR_LEN:HDR_LEN + length]

            if eof_linger_deadline is not None:
                # Sender may retransmit EOF because final ACK was lost/corrupted.
                if (flags & FLAG_EOF) and seq == eof_seq and addr == eof_addr:
                    ack = pack_packet(TYPE_ACK, seq)
                    sock.sendto(ack, addr)
                continue

            if seq != expected:
                ack = pack_packet(TYPE_ACK, last_ack_seq)
                sock.sendto(ack, addr)
                continue

            if flags & FLAG_EOF:
                ack = pack_packet(TYPE_ACK, seq)
                sock.sendto(ack, addr)
                eof_seq = seq
                eof_addr = addr
                eof_linger_deadline = time.monotonic() + args.eof_linger
                continue

            out.write(payload)
            ack = pack_packet(TYPE_ACK, seq)
            sock.sendto(ack, addr)
            last_ack_seq = seq
            expected ^= 1

    sock.close()
    print("[RECEIVER] complete")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--bind", default="0.0.0.0")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--out", dest="outfile", required=True)
    p.add_argument("--mtu", type=int, default=2048)
    p.add_argument("--data-error", type=float, default=0.0)
    p.add_argument("--data-loss", type=float, default=0.0)
    p.add_argument("--eof-linger", type=float, default=2.0,
                   help="seconds to keep ACKing duplicate EOF after first EOF")
    p.add_argument("--seed", type=int, default=2)
    args = p.parse_args()
    run_receiver(args)


if __name__ == "__main__":
    main()
