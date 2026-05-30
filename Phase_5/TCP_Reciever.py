from __future__ import annotations

import argparse
import random
import socket
import time
from pathlib import Path

from common import ensure_parent, should_drop
from packet import Packet, TYPE_ACK, TYPE_DATA, NO_ACK, FLAG_EOF


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--bind", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--out", required=True)
    p.add_argument("--rwnd", type=int, default=8)
    p.add_argument("--loss", type=float, default=0.0)
    p.add_argument("--error", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=2)
    p.add_argument("--verbose", action="store_true")

    p.add_argument("--debug", action="store_true")

    return p.parse_args()


def log(v, msg):
    if v:
        print(msg, flush=True)


def main():
    args = parse_args()
    rng = random.Random(args.seed)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.bind, args.port))
    sock.settimeout(0.5)

    expected = 0
    last_ack = NO_ACK
    buffer = {}

    ensure_parent(args.out)
    out = open(args.out, "wb")

    peer = None
    eof_seen = False
    linger_start = None

    if args.debug:
        print("[DEBUG][RECEIVER STARTED]")

    while True:
        if eof_seen and linger_start and time.perf_counter() - linger_start > 1.0:
            if args.debug:
                
                print("[DEBUG][EOF COMPLETE - EXIT]")
            break

        try:
            try:
                raw, addr = sock.recvfrom(65535)
            except (ConnectionResetError, OSError):
                if args.debug:
                    print("[DEBUG][SOCKET RESET IGNORED]")
                continue

            peer = addr

            # LOSS SIMULATION
            if should_drop(args.loss, rng):
                if args.debug:
                    print("[DEBUG][DROP] packet lost (simulated)")
                continue

            pkt = Packet.decode(raw)

            if pkt.pkt_type != TYPE_DATA:
                continue

            if args.debug:
                print(f"[DEBUG][RECV] seq={pkt.seq}")

            # FLOW CONTROL CHECK
            if len(buffer) >= args.rwnd:
                if args.debug:
                    print(f"[DEBUG][RWND FULL] seq={pkt.seq} dropped")
                continue

            buffer[pkt.seq] = pkt

            if args.debug:
                print(f"[DEBUG][BUFFERED] seq={pkt.seq} size={len(buffer)}")

            # Deliver in order
            while expected in buffer:
                p = buffer.pop(expected)
                out.write(p.payload)

                if args.debug:
                    print(f"[DEBUG][DELIVERED] seq={expected}")
                
                last_ack = expected - 1
                if last_ack < 0:
                    last_ack = 0
                expected += 1

                if p.flags & FLAG_EOF:
                    eof_seen = True
                    linger_start = time.perf_counter()

                    #eof_ack = Packet(pkt_type=TYPE_ACK, ack=last_ack, rwnd=max(args.rwnd - len(buffer), 0), flags=FLAG_EOF)
                    #sock.sendto(eof_ack.encode(), peer)

                    if args.debug:
                        print("[DEBUG][EOF RECEIVED]")

            # SEND ACK
            rwnd = max(args.rwnd - len(buffer), 0)
            ack = Packet(pkt_type=TYPE_ACK, ack=last_ack, rwnd=rwnd)
            #sock.sendto(ack.encode(), peer)

            if not eof_seen:
                sock.sendto(ack.encode(), peer)
            else:
                # send FINAL EOF ACK only once
                if expected not in buffer:   # or just send once
                    eof_ack = Packet(pkt_type=TYPE_ACK, ack=last_ack, rwnd=rwnd, flags=FLAG_EOF)
                    sock.sendto(eof_ack.encode(), peer)
                    eof_seen = "sent"

            if args.debug:
                print(f"[DEBUG][ACK_SENT] ack={last_ack}")

            log(args.verbose, f"[receiver] ACK {last_ack}")

        except socket.timeout:
            continue

    out.close()
    sock.close()

    if args.debug:
        print("[DEBUG][RECEIVER CLOSED]")


if __name__ == "__main__":
    main()