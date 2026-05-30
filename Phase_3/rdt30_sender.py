#!/usr/bin/env python3
"""
RDT 3.0 Sender (Stop-and-Wait over UDP)
- seq numbers 0/1
- checksum + ACK-only reliability
- handles ACK corruption/loss with timeout-based retransmission
- sends EOF as zero-length DATA packet with EOF flag
"""

import argparse
import os
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


def await_valid_ack(sock: socket.socket, expected_seq: int, args: argparse.Namespace) -> bool:
    """Return True when a valid ACK for expected_seq is received, else False on timeout/invalid."""
    try:
        ack, _ = sock.recvfrom(2048)
    except socket.timeout:
        return False

    # Simulate channel issues after receive, as required by the project.
    if random.random() < args.ack_loss:
        return False
    if random.random() < args.ack_error:
        ack = corrupt_bytes(ack)

    try:
        pkt_type, ack_seq, _, _, _ = unpack_header(ack)
    except Exception:
        return False

    if pkt_type != TYPE_ACK:
        return False
    if is_corrupt(ack):
        return False
    if ack_seq != expected_seq:
        return False
    return True


def send_stop_and_wait(sock: socket.socket, addr, pkt: bytes, seq: int, args: argparse.Namespace) -> None:
    while True:
        sock.sendto(pkt, addr)
        if await_valid_ack(sock, seq, args):
            return
        # timeout, loss, corruption, or wrong ACK => retransmit


def send_file(args: argparse.Namespace) -> float:
    random.seed(args.seed)

    addr = (args.host, args.port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(args.timeout)

    seq = 0
    start = time.perf_counter()

    with open(args.infile, "rb") as f:
        while True:
            chunk = f.read(args.chunk)
            if not chunk:
                break
            pkt = pack_packet(TYPE_DATA, seq, chunk, flags=0)
            send_stop_and_wait(sock, addr, pkt, seq, args)
            seq ^= 1

    eof_pkt = pack_packet(TYPE_DATA, seq, b"", flags=FLAG_EOF)
    send_stop_and_wait(sock, addr, eof_pkt, seq, args)

    end = time.perf_counter()
    sock.close()
    return end - start


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--in", dest="infile", required=True)
    p.add_argument("--chunk", type=int, default=1024)
    p.add_argument("--timeout", type=float, default=0.25)
    p.add_argument("--ack-error", type=float, default=0.0)
    p.add_argument("--ack-loss", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()

    if not os.path.isfile(args.infile):
        raise SystemExit(f"Input file not found: {args.infile}")

    dt = send_file(args)
    print(f"[SENDER] done in {dt:.6f} s")


if __name__ == "__main__":
    main()
