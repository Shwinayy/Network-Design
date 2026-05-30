#!/usr/bin/env python3
"""
RDT 2.2 Receiver (Stop-and-Wait, ACK-only, seq 0/1) over UDP
- Supports simulating DATA corruption (Option 3) and packet loss on inbound DATA.
- Writes received bytes to an output file.
- Terminates when it receives an uncorrupted EOF DATA packet with expected sequence.

Usage example:
  python3 rdt22_receiver.py --bind 0.0.0.0 --port 5000 --out output.bmp --chunk 1024 \
    --data-error 0.10 --data-loss 0.00
"""

import argparse
import socket
import struct
import random
from typing import Tuple

# Must match sender
HDR_FMT = "!BBH H B"
HDR_LEN = 7

TYPE_DATA = 0
TYPE_ACK  = 1
FLAG_EOF  = 0x01


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
    last_ack_seq = 1  # "previous" ACK when expected=0 is ACK1 (as in FSM)

    with open(args.outfile, "wb") as out:
        print(f"[RECEIVER] listening on {args.bind}:{args.port}")
        while True:
            pkt, addr = sock.recvfrom(args.mtu)

            # Simulate DATA loss/corruption AFTER receive (as Phase 2 asks)
            if random.random() < args.data_loss:
                continue
            if random.random() < args.data_error:
                pkt = corrupt_bytes(pkt)

            try:
                pkt_type, seq, length, _, flags = unpack_header(pkt)
            except Exception:
                # can't parse => treat as corrupt => resend previous ACK
                ack = pack_packet(TYPE_ACK, last_ack_seq, b"", flags=0)
                sock.sendto(ack, addr)
                continue

            if pkt_type != TYPE_DATA:
                continue

            if is_corrupt(pkt):
                # corrupted data => resend previous ACK
                ack = pack_packet(TYPE_ACK, last_ack_seq, b"", flags=0)
                sock.sendto(ack, addr)
                continue

            # not corrupt
            payload = pkt[HDR_LEN:HDR_LEN + length]

            if seq != expected:
                # duplicate or out-of-order => resend previous ACK
                ack = pack_packet(TYPE_ACK, last_ack_seq, b"", flags=0)
                sock.sendto(ack, addr)
                continue

            # correct & expected packet
            if flags & FLAG_EOF:
                # ACK EOF and finish
                ack = pack_packet(TYPE_ACK, seq, b"", flags=0)
                sock.sendto(ack, addr)
                break

            out.write(payload)

            # send ACK for this seq
            ack = pack_packet(TYPE_ACK, seq, b"", flags=0)
            sock.sendto(ack, addr)

            # update expected seq and last ACK seq
            last_ack_seq = seq
            expected ^= 1

    sock.close()
    print("[RECEIVER] complete")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bind", default="0.0.0.0")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--out", dest="outfile", required=True)
    p.add_argument("--mtu", type=int, default=2048)

    # Option 3 knobs
    p.add_argument("--data-error", type=float, default=0.0, help="probability to corrupt a received DATA packet (0..1)")
    p.add_argument("--data-loss", type=float, default=0.0, help="probability to drop a received DATA packet (0..1)")

    p.add_argument("--seed", type=int, default=2)
    args = p.parse_args()

    run_receiver(args)

if __name__ == "__main__":
    main()
