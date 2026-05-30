from __future__ import annotations

import subprocess
import sys
import time
import re
from pathlib import Path
import csv
import matplotlib.pyplot as plt

# CONFIG
ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "new_results"

SAMPLE_FILE = ROOT / "sample_input.bin"
PORT = 5005
LOSS = 0.0

# capture both cwnd and ACK from debug output
CWND_RE = re.compile(r"cwnd=(\d+)")
ACK_RE = re.compile(r"ack=(\d+)")


# START RECEIVER
def start_receiver():
    cmd = [
        sys.executable,
        "TCP_Reciever.py",
        "--out", str(ROOT / "tmp.bin"),
        "--rwnd", "10",
        "--loss", str(LOSS),
        "--bind", "127.0.0.1",
        "--port", str(PORT),
        "--debug"
    ]
    return subprocess.Popen(cmd)


# RUN SENDER
def run_sender():
    cmd = [
        sys.executable,
        "TCP_Sender.py",
        "--in", str(SAMPLE_FILE),
        "--host", "127.0.0.1",
        "--port", str(PORT),
        "--debug"
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.stdout


# EXTRACT (ACK, CWND) PAIRS
def extract_ack_cwnd(debug_output: str):
    ack_cwnd_pairs = []

    current_ack = 0
    current_cwnd = None

    for line in debug_output.splitlines():

        ack_match = ACK_RE.search(line)
        if ack_match:
            current_ack = int(ack_match.group(1))

        cwnd_match = CWND_RE.search(line)
        if cwnd_match:
            current_cwnd = int(cwnd_match.group(1))

            # store pair only when both exist
            ack_cwnd_pairs.append((current_ack, current_cwnd))

    return ack_cwnd_pairs


# WRITE CSV
def write_csv(data):
    RESULTS.mkdir(exist_ok=True)

    csv_path = RESULTS / "cwnd_log_chart_2.csv"

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ack", "cwnd"])

        for ack, cwnd in data:
            writer.writerow([ack, cwnd])

    print(f"[Chart2] CSV saved → {csv_path}")
    return csv_path


# PLOT 
def plot(csv_path):
    ack = []
    cwnd = []

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            ack.append(int(row["ack"]))
            cwnd.append(int(row["cwnd"]))

    #SORTED BY ACK
    combined = sorted(zip(ack, cwnd))
    ack, cwnd = zip(*combined)

    plt.figure()

    plt.step(ack, cwnd, where="post", linewidth=2)

    #SMOOTH LINE for PLOT
    plt.plot(ack, cwnd, alpha=0.3)

    plt.xlabel("ACK Number")
    plt.ylabel("Congestion Window (cwnd)")
    plt.title("TCP Reno cwnd vs ACK Progression")

    plt.grid(True)

    out = RESULTS / "chart2_cwnd.png"
    plt.savefig(out)
    plt.close()

    print(f"[Chart2] Plot saved → {out}")



def main():
    receiver = start_receiver()
    time.sleep(0.3)

    debug_output = run_sender()

    receiver.kill()

    data = extract_ack_cwnd(debug_output)

    if not data:
        print("ERROR: No cwnd/ACK data captured")
        return

    csv_path = write_csv(data)

    plot(csv_path)


if __name__ == "__main__":
    main()