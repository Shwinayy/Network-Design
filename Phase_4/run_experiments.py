from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
RESULTS = ROOT / "results"
RATES = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
WINDOW_SIZES = [1, 2, 5, 10, 20, 50]
TRANSFER_RE = re.compile(r"TRANSFER_COMPLETE_SECONDS=([0-9.]+)")

OPTION_CONFIGS = {
    1: {"ack_error": 0.0, "data_error": 0.0, "ack_loss": 0.0, "data_loss": 0.0},
    2: {"ack_error": "RATE", "data_error": 0.0, "ack_loss": 0.0, "data_loss": 0.0},
    3: {"ack_error": 0.0, "data_error": "RATE", "ack_loss": 0.0, "data_loss": 0.0},
    4: {"ack_error": 0.0, "data_error": 0.0, "ack_loss": "RATE", "data_loss": 0.0},
    5: {"ack_error": 0.0, "data_error": 0.0, "ack_loss": 0.0, "data_loss": "RATE"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 4 GBN timing experiments")
    parser.add_argument("--input", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=55000)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=0.2)
    parser.add_argument("--chunk-size", type=int, default=1024)
    parser.add_argument("--window", type=int, default=5)
    parser.add_argument("--mode", choices=["chart1", "chart2", "all"], default="all")
    parser.add_argument("--chart2-option", type=int, choices=[1, 2, 3, 4, 5], default=5)
    return parser.parse_args()


def start_receiver(
    out_path: Path,
    host: str,
    port: int,
    data_error: float,
    data_loss: float,
    seed: int
) -> subprocess.Popen[str]:
    cmd = [
        sys.executable,
        str(SRC / "receiver.py"),
        "--bind", host,
        "--port", str(port),
        "--out", str(out_path),
        "--data-error", str(data_error),
        "--data-loss", str(data_loss),
        "--seed", str(seed),
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def run_sender(
    input_path: Path,
    host: str,
    port: int,
    window: int,
    chunk_size: int,
    timeout: float,
    ack_error: float,
    ack_loss: float,
    seed: int
) -> tuple[float, bool]:
    cmd = [
        sys.executable,
        str(SRC / "sender.py"),
        "--in", str(input_path),
        "--host", host,
        "--port", str(port),
        "--window", str(window),
        "--chunk-size", str(chunk_size),
        "--timeout", str(timeout),
        "--ack-error", str(ack_error),
        "--ack-loss", str(ack_loss),
        "--seed", str(seed),
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        print(f"[WARNING] sender timeout on port {port} (using fallback completion time)", flush=True)
        return 10.0, True

    if proc.returncode != 0:
        raise RuntimeError("sender failed:\nSTDOUT:\n" + proc.stdout + "\nSTDERR:\n" + proc.stderr)

    match = TRANSFER_RE.search(proc.stdout)
    if not match:
        raise RuntimeError(f"could not parse sender time from output:\n{proc.stdout}\n{proc.stderr}")

    return float(match.group(1)), False


def one_run(
    input_path: Path,
    host: str,
    port: int,
    window: int,
    chunk_size: int,
    timeout: float,
    ack_error: float,
    data_error: float,
    ack_loss: float,
    data_loss: float,
    seed_base: int,
    run_id: int,
) -> float:
    out_path = RESULTS / f"tmp_out_{int(time.time() * 1000)}_{run_id}.bin"
    run_port = port + run_id + (seed_base % 1000)

    receiver = start_receiver(
        out_path, host, run_port, data_error, data_loss, seed=seed_base + 1000 + run_id
    )

    time.sleep(0.10)

    sender_timed_out = False
    try:
        elapsed, sender_timed_out = run_sender(
            input_path, host, run_port, window, chunk_size, timeout,
            ack_error, ack_loss, seed=seed_base + run_id
        )
    finally:
        receiver_killed = False
        try:
            receiver.wait(timeout=5)
        except subprocess.TimeoutExpired:
            receiver.kill()
            receiver_killed = True
            try:
                receiver.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass

    out_stdout, out_stderr = receiver.communicate()

    # Only treat receiver failure as fatal if it was NOT intentionally killed
    # due to sender timeout / cleanup handling.
    if receiver.returncode not in (0, None):
        if not sender_timed_out and not receiver_killed:
            raise RuntimeError(f"receiver failed:\nSTDOUT:\n{out_stdout}\nSTDERR:\n{out_stderr}")

    if out_path.exists():
        out_path.unlink()

    time.sleep(0.05)
    return elapsed


def write_raw_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_chart1(args: argparse.Namespace) -> None:
    for option, mapping in OPTION_CONFIGS.items():
        rows = []
        for rate in RATES:
            rate_prob = rate / 100.0
            for run_idx in range(args.runs):
                cfg = {
                    "ack_error": rate_prob if mapping["ack_error"] == "RATE" else mapping["ack_error"],
                    "data_error": rate_prob if mapping["data_error"] == "RATE" else mapping["data_error"],
                    "ack_loss": rate_prob if mapping["ack_loss"] == "RATE" else mapping["ack_loss"],
                    "data_loss": rate_prob if mapping["data_loss"] == "RATE" else mapping["data_loss"],
                }

                elapsed = one_run(
                    Path(args.input),
                    args.host,
                    args.port,
                    args.window,
                    args.chunk_size,
                    args.timeout,
                    cfg["ack_error"],
                    cfg["data_error"],
                    cfg["ack_loss"],
                    cfg["data_loss"],
                    seed_base=option * 10000 + rate * 10,
                    run_id=run_idx,
                )

                rows.append({
                    "option": option,
                    "rate": rate,
                    "run": run_idx + 1,
                    "window": args.window,
                    "timeout_s": args.timeout,
                    **cfg,
                    "completion_time_s": f"{elapsed:.6f}",
                })

                print(
                    f"option={option} rate={rate}% run={run_idx + 1}/{args.runs} time={elapsed:.6f}s",
                    flush=True
                )

        write_raw_csv(RESULTS / f"results_option{option}.csv", rows)


def run_chart2(args: argparse.Namespace) -> None:
    option = args.chart2_option
    mapping = OPTION_CONFIGS[option]
    rows = []

    for window in WINDOW_SIZES:
        for run_idx in range(args.runs):
            rate_prob = 0.10
            cfg = {
                "ack_error": rate_prob if mapping["ack_error"] == "RATE" else mapping["ack_error"],
                "data_error": rate_prob if mapping["data_error"] == "RATE" else mapping["data_error"],
                "ack_loss": rate_prob if mapping["ack_loss"] == "RATE" else mapping["ack_loss"],
                "data_loss": rate_prob if mapping["data_loss"] == "RATE" else mapping["data_loss"],
            }

            elapsed = one_run(
                Path(args.input),
                args.host,
                args.port,
                window,
                args.chunk_size,
                args.timeout,
                cfg["ack_error"],
                cfg["data_error"],
                cfg["ack_loss"],
                cfg["data_loss"],
                seed_base=option * 50000 + window * 100,
                run_id=run_idx,
            )

            rows.append({
                "option": option,
                "window": window,
                "run": run_idx + 1,
                "fixed_rate": 10,
                "timeout_s": args.timeout,
                **cfg,
                "completion_time_s": f"{elapsed:.6f}",
            })

            print(
                f"chart2 option={option} window={window} run={run_idx + 1}/{args.runs} time={elapsed:.6f}s",
                flush=True
            )

    write_raw_csv(RESULTS / "results_window_sizes.csv", rows)


def main() -> None:
    args = parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)

    if args.mode in {"chart1", "all"}:
        run_chart1(args)

    if args.mode in {"chart2", "all"}:
        run_chart2(args)


if __name__ == "__main__":
    main()