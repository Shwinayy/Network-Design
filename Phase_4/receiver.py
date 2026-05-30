from __future__ import annotations

import argparse
import random
import socket
import time
from pathlib import Path

from common import ensure_parent, should_drop
from packet import NO_ACK, Packet, TYPE_ACK, TYPE_DATA, maybe_flip_one_bit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 4 GBN receiver")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--out", required=True)
    parser.add_argument("--data-error", type=float, default=0.0, help="Probability [0,1] or percent [0,100]")
    parser.add_argument("--data-loss", type=float, default=0.0, help="Probability [0,1] or percent [0,100]")
    parser.add_argument("--seed", type=int, default=2)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--max-packet-size", type=int, default=65535)
    parser.add_argument("--linger", type=float, default=1.0, help="Seconds to remain alive after EOF to re-ACK duplicates")
    return parser.parse_args()


def normalize_rate(value: float) -> float:
    return value / 100.0 if value > 1.0 else value


def log(enabled: bool, message: str) -> None:
    if enabled:
        print(message, flush=True)


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    data_error = normalize_rate(args.data_error)
    data_loss = normalize_rate(args.data_loss)

    ensure_parent(args.out)
    expected_seq = 0
    last_acked = NO_ACK

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.bind, args.port))

    # Short timeout so we can periodically check whether linger time is over
    sock.settimeout(0.1)

    peer_addr = None
    output_path = Path(args.out)

    transfer_done = False
    done_time: float | None = None

    with open(output_path, "wb") as fout:
        while True:
            # If we've already accepted EOF, linger a bit so retransmitted
            # final packets can still be ACKed in case sender missed the ACK.
            if transfer_done and done_time is not None:
                if time.perf_counter() - done_time >= args.linger:
                    break

            try:
                raw, addr = sock.recvfrom(args.max_packet_size)
            except socket.timeout:
                continue

            peer_addr = addr

            if should_drop(data_loss, rng):
                log(args.verbose, f"[receiver] intentionally dropped DATA candidate from {addr}")
                continue

            raw = maybe_flip_one_bit(raw, data_error, rng)

            try:
                pkt = Packet.decode(raw)
            except ValueError:
                ack_pkt = Packet(pkt_type=TYPE_ACK, ack=last_acked)
                sock.sendto(ack_pkt.encode(), addr)
                log(args.verbose, f"[receiver] corrupt packet -> re-ACK {last_acked}")
                continue

            if pkt.pkt_type != TYPE_DATA:
                continue

            # Normal in-order accept
            if pkt.seq == expected_seq:
                if pkt.payload:
                    fout.write(pkt.payload)

                last_acked = expected_seq
                expected_seq += 1

                ack_pkt = Packet(pkt_type=TYPE_ACK, ack=last_acked)
                sock.sendto(ack_pkt.encode(), addr)

                log(args.verbose, f"[receiver] accepted seq={pkt.seq} eof={pkt.is_eof}")

                if pkt.is_eof:
                    transfer_done = True
                    done_time = time.perf_counter()
                    log(args.verbose, f"[receiver] EOF accepted, entering linger for {args.linger:.2f}s")

            else:
                # Out-of-order or duplicate packet:
                # Go-Back-N receiver re-ACKs the last correctly received in-order packet.
                ack_pkt = Packet(pkt_type=TYPE_ACK, ack=last_acked)
                sock.sendto(ack_pkt.encode(), addr)
                log(args.verbose, f"[receiver] out-of-order/duplicate seq={pkt.seq}, expected={expected_seq}, re-ACK {last_acked}")

    sock.close()
    log(args.verbose, f"[receiver] done -> {output_path} from {peer_addr}")


if __name__ == "__main__":
    main()