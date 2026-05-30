from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path
import re
import matplotlib.pyplot as plt


# CONFIG
ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "new_results"

LOSS_RATES = list(range(0, 100, 5))
TRANSFER_RE = re.compile(r"TIME:\s*([0-9.]+)")


# ARGS
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    return parser.parse_args()


# START RECEIVER
def start_receiver(loss, host, port):
    cmd = [
        sys.executable,
        "TCP_Reciever.py",
        "--out", str(ROOT / "tmp.bin"),
        "--rwnd", "10",
        "--loss", str(loss / 100.0),
        "--bind", host,
        "--port", str(port),
    ]
    return subprocess.Popen(cmd)


# RUN SENDER
def run_sender(input_file, host, port):
    cmd = [
        sys.executable,
        "TCP_Sender.py",
        "--in", input_file,
        "--host", host,
        "--port", str(port),
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)

    match = TRANSFER_RE.search(proc.stdout)
    if match:
        return float(match.group(1))

    return 999.0


# CHART 1 TEST
def chart1(args):
    rows = []

    RESULTS.mkdir(exist_ok=True)

    for loss in LOSS_RATES:
        for run in range(args.runs):

            receiver = start_receiver(loss, args.host, args.port)
            time.sleep(0.2)

            t = run_sender(args.input, args.host, args.port)

            receiver.kill()

            rows.append({
                "loss_percent": loss,
                "run": run + 1,
                "time_s": t
            })

            print(f"loss={loss}% run={run+1} time={t:.4f}s")

    # WRITES CSV
    out_csv = RESULTS / "chart1_loss.csv"

    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"[Chart1] Saved → {out_csv}")

    # PLOTS THE CSV DATA
    grouped = {}

    for r in rows:
        loss = int(r["loss_percent"])
        grouped.setdefault(loss, []).append(float(r["time_s"]))

    x = sorted(grouped.keys())
    y = [sum(grouped[i]) / len(grouped[i]) for i in x]

    plt.figure()
    plt.plot(x, y, marker="o")
    plt.title("Completion Time vs Packet Loss")
    plt.xlabel("Packet Loss (%)")
    plt.ylabel("Time (s)")
    plt.grid(True)

    out_png = RESULTS / "chart1.png"
    plt.savefig(out_png)
    plt.close()

    print(f"[Chart1] Plot saved → {out_png}")



def main():
    args = parse_args()
    chart1(args)


if __name__ == "__main__":
    main()