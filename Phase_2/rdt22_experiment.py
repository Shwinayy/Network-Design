#!/usr/bin/env python3
"""
Experiment runner + plotter for Phase 2 charts.
Runs receiver in a subprocess, then sender, measures sender completion time.
Repeats 5 runs per rate, from 0% to 95% in 5% steps.

produces:
  - results_optionX.csv
  - plot_optionX.png

Options:
  option1: no errors
  option2: ACK corruption at sender
  option3: DATA corruption at receiver

Usage:
  python3 rdt22_experiment.py --in input.bmp --out output.bmp --option 2 --runs 5 --port 5000
"""

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt

SENDER = "rdt22_sender.py"
RECEIVER = "rdt22_receiver.py"


def run_once(option: int, rate: float, infile: str, outfile: str, port: int, timeout: float, chunk: int) -> float:
    # Build receiver cmd
    rx_cmd = [sys.executable, RECEIVER, "--port", str(port), "--out", outfile]
    tx_cmd = [sys.executable, SENDER, "--host", "127.0.0.1", "--port", str(port),
              "--in", infile, "--timeout", str(timeout), "--chunk", str(chunk)]

    if option == 1:
        pass
    elif option == 2:
        tx_cmd += ["--ack-error", str(rate)]
    elif option == 3:
        rx_cmd += ["--data-error", str(rate)]
    else:
        raise ValueError("option must be 1, 2, or 3")

    # Start receiver
    rx = subprocess.Popen(rx_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # Give receiver a moment to bind
    time.sleep(0.10)

    # Run sender (capture time from sender output OR measure wall time)
    t0 = time.perf_counter()
    try:
        tx = subprocess.run(tx_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        # Sender took too long at this error rate; treat as timeout
        try:
            rx.kill()
        except Exception:
            pass
        return None
    t1 = time.perf_counter()

    # Wait receiver to exit
    try:
        rx.wait(timeout=5)
    except subprocess.TimeoutExpired:
        rx.kill()

    if tx.returncode != 0:
        raise RuntimeError(f"Sender failed.\nSTDOUT:\n{tx.stdout}\nSTDERR:\n{tx.stderr}")

    return t1 - t0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="infile", required=True)
    p.add_argument("--out", dest="outfile", default="output.bmp")
    p.add_argument("--option", type=int, choices=[1,2,3], required=True)
    p.add_argument("--runs", type=int, default=5)
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--timeout", type=float, default=0.25)
    p.add_argument("--chunk", type=int, default=1024)
    args = p.parse_args()

    rates = [i/100 for i in range(0, 100, 5)]
    rates = [r for r in rates if r <= 0.95]

    rows = []
    for r in rates:
        times = []
        for _ in range(args.runs):
            dt = run_once(args.option, r, args.infile, args.outfile, args.port, args.timeout, args.chunk)
            if dt is None:
                # record timeout as NaN
                times.append(float('nan'))
            else:
                times.append(dt)
        valid = [t for t in times if t == t]  # t==t filters out NaN
        avg = (sum(valid)/len(valid)) if valid else float('nan')
        rows.append((r, avg))
        timeout_ct = sum(1 for t in times if t != t)
        if avg == avg:
            print(f"rate={r:.2f} avg_time={avg:.6f}s (timeouts={timeout_ct}/{len(times)})")
        else:
            print(f"rate={r:.2f} avg_time=TIMEOUT (timeouts={timeout_ct}/{len(times)})")

    csv_name = f"results_option{args.option}.csv"
    with open(csv_name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rate", "avg_time_s"])
        w.writerows(rows)

    # Plot
    xs = [r for r,t in rows if t == t]
    ys = [t for r,t in rows if t == t]
    plt.figure()
    plt.plot(xs, ys)
    plt.xlabel("Error/Loss Rate")
    plt.ylabel("Completion Time (s)")
    plt.title(f"Phase 2 Option {args.option}")
    png_name = f"plot_option{args.option}.png"
    plt.savefig(png_name, dpi=200, bbox_inches="tight")
    print(f"Wrote {csv_name} and {png_name}")

if __name__ == "__main__":
    main()
