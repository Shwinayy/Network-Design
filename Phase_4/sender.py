from __future__ import annotations

import argparse
import random
import socket
import time
from pathlib import Path

from common import chunk_bytes, sha256_file, pct_to_prob
from packet import NO_ACK, Packet, TYPE_ACK, TYPE_DATA, FLAG_EOF, maybe_flip_one_bit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 4 GBN sender")
    parser.add_argument("--in", dest="input_path", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--window", type=int, default=5)
    parser.add_argument("--chunk-size", type=int, default=1024)
    parser.add_argument("--timeout", type=float, default=0.2)
    parser.add_argument("--ack-error", type=float, default=0.0, help="Probability [0,1] or percent [0,100]")
    parser.add_argument("--ack-loss", type=float, default=0.0, help="Probability [0,1] or percent [0,100]")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def log(enabled: bool, message: str) -> None:
    if enabled:
        print(message, flush=True)


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    ack_error = pct_to_prob(args.ack_error)
    ack_loss = pct_to_prob(args.ack_loss)

    input_path = Path(args.input_path)
    data = input_path.read_bytes()
    chunks = chunk_bytes(data, args.chunk_size)

    packets = [Packet(pkt_type=TYPE_DATA, seq=i, payload=chunk) for i, chunk in enumerate(chunks)]

    eof_seq = len(packets)
    packets.append(Packet(pkt_type=TYPE_DATA, seq=eof_seq, flags=FLAG_EOF, payload=b""))

    total_packets = len(packets)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.01)

    peer = (args.host, args.port)

    base = 0
    nextseqnum = 0
    timer_start: float | None = None

    started = time.perf_counter()

    while base < total_packets:

        # Send packets within window
        while nextseqnum < base + args.window and nextseqnum < total_packets:
            sock.sendto(packets[nextseqnum].encode(), peer)

            log(args.verbose, f"[sender] sent seq={nextseqnum}{' EOF' if nextseqnum == eof_seq else ''}")

            if base == nextseqnum:
                timer_start = time.perf_counter()

            nextseqnum += 1

        try:
            raw, _ = sock.recvfrom(65535)

            # Simulate ACK loss
            if ack_loss > 0.0 and rng.random() < ack_loss:
                log(args.verbose, "[sender] intentionally dropped ACK before processing")
                raise socket.timeout

            # Simulate ACK corruption
            raw = maybe_flip_one_bit(raw, ack_error, rng)

            ack_pkt = Packet.decode(raw)

            if ack_pkt.pkt_type != TYPE_ACK:
                continue

            acknum = ack_pkt.ack

            if acknum != NO_ACK and acknum >= base:
                base = acknum + 1

                log(args.verbose, f"[sender] received cumulative ACK {acknum}; base -> {base}")

                if base == nextseqnum:
                    timer_start = None
                else:
                    timer_start = time.perf_counter()

        except ValueError:
            log(args.verbose, "[sender] corrupted ACK ignored")

        except ConnectionResetError:
            # 🔥 Windows-specific fix
            log(args.verbose, "[sender] Windows UDP reset ignored (treated as lost ACK)")

            now = time.perf_counter()
            if timer_start is not None and now - timer_start >= args.timeout:
                log(args.verbose, f"[sender] timeout on base={base}; retransmitting {base}..{nextseqnum - 1}")

                timer_start = time.perf_counter()
                for i in range(base, nextseqnum):
                    sock.sendto(packets[i].encode(), peer)

        except socket.timeout:
            now = time.perf_counter()

            if timer_start is not None and now - timer_start >= args.timeout:
                log(args.verbose, f"[sender] timeout on base={base}; retransmitting {base}..{nextseqnum - 1}")

                timer_start = time.perf_counter()
                for i in range(base, nextseqnum):
                    sock.sendto(packets[i].encode(), peer)

    elapsed = time.perf_counter() - started

    print(f"TRANSFER_COMPLETE_SECONDS={elapsed:.6f}")
    print(f"INPUT_SHA256={sha256_file(input_path)}")
    print(f"TOTAL_PACKETS={total_packets}")

    sock.close()


if __name__ == "__main__":
    main()