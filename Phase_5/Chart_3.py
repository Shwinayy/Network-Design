from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path
import matplotlib.pyplot as plt

# CONFIG
ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "new_results"

SAMPLE_FILE = ROOT / "sample_input.bin"
LOSS = 0.0
PHASE_PORT_BASE = 5000


def run_cmd(cmd):
    start = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    end = time.perf_counter()
    return end - start


# FILE RUNNER
def run_file(cmd, label: str):
    script = cmd[1]

    if not Path(script).exists():
        print(f"[ERROR] Missing file: {script}")
        return 0.0

    return run_cmd(cmd)


# RUNS PHASE TESTS
def run_phase(phase: int, port: int) -> float:

    if phase == 1:
        server_cmd = [
            sys.executable,
            "Phase_1_b_server.py",
            str(ROOT / "phase1_out.bin")
        ]

        client_cmd = [
            sys.executable,
            "Phase_1_b_client.py",
            str(SAMPLE_FILE)
        ]

        # Start server 
        server = subprocess.Popen(server_cmd)

        # Give it time to bind
        time.sleep(0.3)

        # Run client 
        t = run_cmd(client_cmd)

        # Force server shutdown
        try:
            server.terminate()
            server.wait(timeout=2)
        except subprocess.TimeoutExpired:
            server.kill()

        return t
    
    
    if phase == 2:
        receiver = subprocess.Popen([
            sys.executable,
            "rdt22_receiver.py",
            "--bind", "127.0.0.1",
            "--port", str(port),
            "--out", str(ROOT / "p2_out.bin"),
            "--data-loss", str(LOSS)
        ])

        time.sleep(0.2)

        t = run_file([
            sys.executable,
            "rdt22_sender.py",
            "--host", "127.0.0.1",
            "--port", str(port),
            "--in", str(SAMPLE_FILE),
            "--ack-loss", str(LOSS)
        ], "rdt22_sender")

        receiver.kill()
        return t

    if phase == 3:
        receiver = subprocess.Popen([
            sys.executable,
            "rdt30_receiver.py",
            "--bind", "127.0.0.1",
            "--port", str(port),
            "--out", str(ROOT / "p3_out.bin"),
            "--data-loss", str(LOSS)
        ])

        time.sleep(0.2)

        t = run_file([
            sys.executable,
            "rdt30_sender.py",
            "--host", "127.0.0.1",
            "--port", str(port),
            "--in", str(SAMPLE_FILE)
        ], "rdt30_sender")

        receiver.kill()
        return t

    if phase == 4:
        receiver = subprocess.Popen([
            sys.executable,
            "receiver.py",
            "--bind", "127.0.0.1",
            "--port", str(port),
            "--out", str(ROOT / "p4_out.bin"),
            "--data-loss", str(LOSS)
        ])

        time.sleep(0.2)

        t = run_cmd([
            sys.executable,
            "sender.py",
            "--host", "127.0.0.1",
            "--port", str(port),
            "--in", str(SAMPLE_FILE)
        ])

        receiver.terminate()
        return t

    if phase == 5:
        receiver = subprocess.Popen([
            sys.executable,
            "TCP_Reciever.py",
            "--bind", "127.0.0.1",
            "--port", str(port),
            "--out", str(ROOT / "p5_out.bin"),
            "--loss", str(LOSS)
        ])

        time.sleep(0.2)

        t = run_cmd([
            sys.executable,
            "TCP_Sender.py",
            "--host", "127.0.0.1",
            "--port", str(port),
            "--in", str(SAMPLE_FILE)
        ])

        receiver.terminate()
    return t
    
# Graphs and WRITES CHART 3
def chart3():
    phases = [1, 2, 3, 4, 5]
    results = []

    for phase in phases:
        print(f"[Chart3] Running Phase {phase}...")

        t = run_phase(phase, PHASE_PORT_BASE + phase)

        results.append({
            "phase": f"Phase {phase}",
            "time_s": t
        })

        print(f"Phase {phase} -> {t:.4f}s")

    RESULTS.mkdir(exist_ok=True)

    csv_path = RESULTS / "chart3_phase_compare.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["phase", "time_s"])
        writer.writeheader()
        writer.writerows(results)

    x = [r["phase"] for r in results]
    y = [r["time_s"] for r in results]

    plt.figure()
    plt.plot(x, y, marker="o")
    plt.xlabel("Protocol Phase")
    plt.ylabel("File Transfer Time (s)")
    plt.title("Phase Comparison: TCP Evolution Performance")

    out = RESULTS / "chart3.png"
    plt.savefig(out)
    plt.close()

    print(f"[Chart3] Saved -> {out}")


if __name__ == "__main__":
    chart3()