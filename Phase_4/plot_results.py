from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RATES = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
WINDOW_SIZES = [1, 2, 5, 10, 20, 50]

# ============================================================
# MANUALLY ENTER YOUR PHASE AVERAGES HERE FOR CHART 3
# Replace these example values with your real averages
# ============================================================
PHASE_AVERAGES = {
    "Phase 2": 0.185,
    "Phase 3": 0.218,
    "Phase 4": 3.02,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot Phase 4 results")
    parser.add_argument("--output-dir", default=str(RESULTS))
    return parser.parse_args()


def mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else float("nan")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def chart1(output_dir: Path) -> None:
    plt.figure(figsize=(10, 6))
    for option in range(1, 6):
        rows = read_csv_rows(RESULTS / f"results_option{option}.csv")
        grouped: dict[int, list[float]] = defaultdict(list)
        for row in rows:
            grouped[int(row["rate"])].append(float(row["completion_time_s"]))
        averages = [mean(grouped[rate]) for rate in RATES]
        plt.plot(RATES, averages, marker="o", label=f"Option {option}")

    plt.title("Phase 4 Performance: Completion Time vs Loss/Error Rate")
    plt.xlabel("Intentional loss/error rate (%)")
    plt.ylabel("File transfer completion time (s)")
    plt.xticks(RATES, rotation=45)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "chart1_phase4_performance.png", dpi=200)
    plt.close()


def chart2(output_dir: Path) -> None:
    rows = read_csv_rows(RESULTS / "results_window_sizes.csv")
    option = rows[0]["option"] if rows else "5"

    grouped: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        grouped[int(row["window"])].append(float(row["completion_time_s"]))

    averages = [mean(grouped[w]) for w in WINDOW_SIZES]

    plt.figure(figsize=(8, 5))
    plt.plot(WINDOW_SIZES, averages, marker="o")
    plt.title(f"Phase 4 Performance at 10% Fixed Rate (Option {option})")
    plt.xlabel("Window size")
    plt.ylabel("File transfer completion time (s)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_dir / "chart2_window_size.png", dpi=200)
    plt.close()


def chart3(output_dir: Path) -> None:
    phases = ["Phase 2", "Phase 3", "Phase 4"]
    averages = [PHASE_AVERAGES[phase] for phase in phases]

    plt.figure(figsize=(8, 5))
    plt.bar(phases, averages)
    plt.title("Completion Time Comparison Across Phases")
    plt.xlabel("Phase")
    plt.ylabel("File transfer completion time (s)")
    plt.tight_layout()
    plt.savefig(output_dir / "chart3_phase_comparison.png", dpi=200)
    plt.close()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    chart1(output_dir)
    chart2(output_dir)
    chart3(output_dir)


if __name__ == "__main__":
    main()