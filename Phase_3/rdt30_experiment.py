#!/usr/bin/env python3
"""Phase 3 experiment runner for options 1-5.

This version resolves the sender/receiver scripts relative to this file,
so it works on a local machine as long as all three Python files are in the
same folder.
"""

import argparse
import csv
import math
import os
import subprocess
import sys
import time

import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SENDER = os.path.join(BASE_DIR, "rdt30_sender.py")
RECEIVER = os.path.join(BASE_DIR, "rdt30_receiver.py")


def resolve_script(path: str, label: str) -> str:
    if os.path.isfile(path):
        return path
    raise FileNotFoundError(
        f"Could not find {label} at: {path}\n"
        f"Make sure {os.path.basename(path)} is in the same folder as this experiment script."
    )


def run_once(option: int, rate: float, infile: str, outfile: str, port: int,
             timeout: float, chunk: int, sender_cap: float,
             rx_start_delay: float, eof_linger: float):
    sender_script = resolve_script(SENDER, "sender script")
    receiver_script = resolve_script(RECEIVER, "receiver script")

    rx_cmd = [
        sys.executable, receiver_script,
        "--port", str(port),
        "--out", outfile,
        "--eof-linger", str(eof_linger),
    ]
    tx_cmd = [
        sys.executable, sender_script,
        "--host", "127.0.0.1",
        "--port", str(port),
        "--in", infile,
        "--timeout", str(timeout),
        "--chunk", str(chunk),
    ]

    if option == 2:
        tx_cmd += ["--ack-error", str(rate)]
    elif option == 3:
        rx_cmd += ["--data-error", str(rate)]
    elif option == 4:
        tx_cmd += ["--ack-loss", str(rate)]
    elif option == 5:
        rx_cmd += ["--data-loss", str(rate)]
    elif option != 1:
        raise ValueError("option must be 1..5")

    rx = subprocess.Popen(rx_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(rx_start_delay)

    t0 = time.perf_counter()
    try:
        tx = subprocess.run(
            tx_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=sender_cap,
        )
    except subprocess.TimeoutExpired:
        rx.kill()
        return None
    t1 = time.perf_counter()

    try:
        rx.wait(timeout=max(5.0, eof_linger + 1.0))
    except subprocess.TimeoutExpired:
        rx.kill()

    if tx.returncode != 0:
        raise RuntimeError(f"Sender failed.\nSTDOUT:\n{tx.stdout}\nSTDERR:\n{tx.stderr}")

    return t1 - t0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="infile", required=True)
    p.add_argument("--out", dest="outfile", default="output.bmp")
    p.add_argument("--option", type=int, choices=[1, 2, 3, 4, 5], required=True)
    p.add_argument("--runs", type=int, default=5)
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--timeout", type=float, default=0.25)
    p.add_argument("--chunk", type=int, default=1024)
    p.add_argument("--sender-cap", type=float, default=180.0,
                   help="max seconds allowed for one sender run")
    p.add_argument("--rx-start-delay", type=float, default=0.15)
    p.add_argument("--eof-linger", type=float, default=2.0)
    args = p.parse_args()

    rates = [i / 100 for i in range(0, 100, 5)]

    rows = []
    for r in rates:
        times = []
        for _ in range(args.runs):
            dt = run_once(args.option, r, args.infile, args.outfile, args.port,
                          args.timeout, args.chunk, args.sender_cap,
                          args.rx_start_delay, args.eof_linger)
            times.append(float("nan") if dt is None else dt)
        valid = [t for t in times if not math.isnan(t)]
        avg = float("nan") if not valid else sum(valid) / len(valid)
        rows.append((r, avg))
        timeout_ct = sum(1 for t in times if math.isnan(t))
        print(f"rate={r:.2f} avg={'TIMEOUT' if math.isnan(avg) else f'{avg:.6f}s'} timeouts={timeout_ct}/{len(times)}")

    csv_name = os.path.join(BASE_DIR, f"results_option{args.option}.csv")
    with open(csv_name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rate", "avg_time_s"])
        w.writerows(rows)

    xs = [r for r, t in rows if not math.isnan(t)]
    ys = [t for _, t in rows if not math.isnan(t)]
    plt.figure()
    plt.plot(xs, ys, marker="o")
    plt.xlabel("Error/Loss Rate")
    plt.ylabel("Completion Time (s)")
    plt.title(f"Phase 3 Option {args.option}")
    png_name = os.path.join(BASE_DIR, f"plot_option{args.option}.png")
    plt.savefig(png_name, dpi=200, bbox_inches="tight")
    print(f"Wrote {csv_name} and {png_name}")


if __name__ == "__main__":
    main()
