#!/usr/bin/env python3
"""
RDT 2.2 Sender (Stop-and-Wait, ACK-only, seq 0/1) over UDP
- Supports simulating ACK corruption (Option 2) and packet loss on inbound ACKs.
- Sends a file in fixed-size chunks as DATA packets.
- Terminates with an EOF DATA packet (zero-length payload + EOF flag).

Usage example:
  python3 rdt22_sender.py --host 127.0.0.1 --port 5000 --in input.bmp --chunk 1024 --timeout 0.25 \
    --ack-error 0.10 --ack-loss 0.00
"""

import argparse
import os
import socket
import struct
import time
import random
from typing import Tuple

# Packet format:
#  type (1B): 0=DATA, 1=ACK
#  seq  (1B): 0 or 1
#  length (2B): payload length (0..65535) for DATA; 0 for ACK
#  checksum (2B): 16-bit internet checksum over header(with checksum=0) + payload
#  flags (1B): bit0 = EOF (only meaningful for DATA)
HDR_FMT = "!BBH H B"   # spaces ignored by struct, kept for readability
HDR_LEN = struct.calcsize("!BBH") + struct.calcsize("!H") + struct.calcsize("!B")  # 7


TYPE_DATA = 0
TYPE_ACK  = 1
FLAG_EOF  = 0x01


def internet_checksum(data: bytes) -> int:
    """Compute 16-bit internet checksum (RFC-style)."""
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
    header_wo_cksum = struct.pack("!BBH", pkt_type, seq, length) + struct.pack("!H", 0) + struct.pack("!B", flags)
    cksum = internet_checksum(header_wo_cksum + payload)
    header = struct.pack("!BBH", pkt_type, seq, length) + struct.pack("!H", cksum) + struct.pack("!B", flags)
    return header + payload


def unpack_header(pkt: bytes) -> Tuple[int, int, int, int, int]:
    if len(pkt) < HDR_LEN:
        raise ValueError("Packet too short")
    pkt_type, seq, length = struct.unpack("!BBH", pkt[:4])
    cksum = struct.unpack("!H", pkt[4:6])[0]
    flags = pkt[6]
    return pkt_type, seq, length, cksum, flags


def is_corrupt(pkt: bytes) -> bool:
    return internet_checksum(pkt) != 0


def corrupt_bytes(data: bytes) -> bytes:
    """Flip one random bit in the bytes."""
    if not data:
        return data
    b = bytearray(data)
    idx = random.randrange(len(b))
    bit = 1 << random.randrange(8)
    b[idx] ^= bit
    return bytes(b)


def send_file(args: argparse.Namespace) -> float:
    random.seed(args.seed)

    addr = (args.host, args.port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(args.timeout)

    seq = 0
    bytes_sent = 0
    start = time.perf_counter()

    with open(args.infile, "rb") as f:
        while True:
            chunk = f.read(args.chunk)
            if not chunk:
                break

            pkt = pack_packet(TYPE_DATA, seq, chunk, flags=0)

            while True:
                sock.sendto(pkt, addr)
                bytes_sent += len(chunk)

                try:
                    ack, _ = sock.recvfrom(2048)
                except socket.timeout:
                    # timeout => retransmit
                    continue

                # Simulate ACK loss/corruption AFTER receive (as Phase 2 asks)
                if random.random() < args.ack_loss:
                    # drop this ACK as if it never arrived
                    continue
                if random.random() < args.ack_error:
                    ack = corrupt_bytes(ack)

                # validate ACK
                try:
                    pkt_type, ack_seq, length, _, _ = unpack_header(ack)
                except Exception:
                    continue

                if pkt_type != TYPE_ACK:
                    continue
                if is_corrupt(ack):
                    # corrupted ACK => retransmit
                    continue
                if ack_seq != seq:
                    # duplicate/wrong ACK => ignore and keep waiting
                    continue

                # correct ACK
                seq ^= 1
                break

    # Send EOF packet (zero-length DATA with EOF flag)
    eof_pkt = pack_packet(TYPE_DATA, seq, b"", flags=FLAG_EOF)
    while True:
        sock.sendto(eof_pkt, addr)
        try:
            ack, _ = sock.recvfrom(2048)
        except socket.timeout:
            continue

        if random.random() < args.ack_loss:
            continue
        if random.random() < args.ack_error:
            ack = corrupt_bytes(ack)

        try:
            pkt_type, ack_seq, _, _, _ = unpack_header(ack)
        except Exception:
            continue
        if pkt_type != TYPE_ACK:
            continue
        if is_corrupt(ack):
            continue
        if ack_seq != seq:
            continue
        break

    end = time.perf_counter()
    sock.close()
    return end - start


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--in", dest="infile", required=True, help="input file to send")
    p.add_argument("--chunk", type=int, default=1024)
    p.add_argument("--timeout", type=float, default=0.25)

    # Option 2 knobs
    p.add_argument("--ack-error", type=float, default=0.0, help="probability to corrupt a received ACK (0..1)")
    p.add_argument("--ack-loss", type=float, default=0.0, help="probability to drop a received ACK (0..1)")

    p.add_argument("--seed", type=int, default=1)

    args = p.parse_args()

    if not os.path.isfile(args.infile):
        raise SystemExit(f"Input file not found: {args.infile}")

    dt = send_file(args)
    print(f"[SENDER] done in {dt:.6f} s")
    print(f"[SENDER] host={args.host} port={args.port} chunk={args.chunk} timeout={args.timeout} "
          f"ack_error={args.ack_error} ack_loss={args.ack_loss}")

if __name__ == "__main__":
    main()
