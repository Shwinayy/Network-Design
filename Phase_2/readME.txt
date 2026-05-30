# Network Design Project – Team AC/DC

---

## Overview

This repository implements a UDP-based file transfer protocol across multiple phases, progressively adding reliability mechanisms and performance evaluation.

Phase 2 implements **RDT 2.2 (Stop-and-Wait, ACK-only, alternating-bit protocol)** over an unreliable UDP channel. The implementation supports deterministic corruption and loss injection for DATA and ACK packets and includes automated performance experiments measuring average completion time across error rates from 0% to 95%.

EOF signaling is implemented using a zero-length DATA packet with an EOF flag.

---

## Team

| Name | Email | Primary Responsibility |
|------|-------|------------------------|
| Chris Worthley | chris_worthley@student.uml.edu | Packet format, checksum, error injection |
| Daniel Burns | daniel_burns3@student.uml.edu | Sender FSM, experiments & plotting |
| Ashwin Srinivasan | Ashwin_Srinivasan@student.uml.edu | Receiver FSM |

---

## Demo Video (submission)

- Private YouTube link: https://youtu.be/VD65wKMSDzY  
- Timestamped outline: (mm:ss → scenario)
- 00:00 → Part A option 1 (Non bit error)
- 00:15 → Part B option 1 (Generates a plot and csv for the reciever - No bit error)
- 01:28 → Part B option 3 (Generates a plot and csv for the reciever - Data corruption)
- 02:45 → Part B option 2 (Generates a plot and csv for the reciever - Ack corruption)

---

## Repository Structure

Minimum layout:

```
src/        # sender, receiver, experiment runner
docs/       # design documents
results/    # CSV + plots generated from experiments
README.md
```

Optional (recommended):
- tests/
- data/
- requirements.txt

---

## Requirements

- Language/runtime: Python 3.x  
- OS tested: Windows, macOS  
- Dependencies:
  - matplotlib

Install dependencies:

```
pip install matplotlib
```

---

## Standard CLI Interface

All programs are executed using Python 3.

---

### Receiver (rdt22_receiver.py)

Required flags:

- `--bind <ip>` (default: 0.0.0.0)  
- `--port <int>`  
- `--out <path>`  
- `--seed <int>` (default: 2)  

Injection flags (Phase 2):

- `--data-error <float 0..1>` (default: 0)  
- `--data-loss <float 0..1>` (default: 0)  

Example:

```
python src/rdt22_receiver.py --port 9000 --out output.bin --seed 2
```

---

### Sender (rdt22_sender.py)

Required flags:

- `--host <ip>`  
- `--port <int>`  
- `--in <path>`  
- `--seed <int>` (default: 1)  

Timing flags:

- `--timeout <float>` (default: 0.25 seconds)  
- `--chunk <int>` (default: 1024 bytes)  

Injection flags (Phase 2):

- `--ack-error <float 0..1>` (default: 0)  
- `--ack-loss <float 0..1>` (default: 0)  

Example:

```
python src/rdt22_sender.py --host 127.0.0.1 --port 9000 --in input.bmp --timeout 0.25
```

Notes:
- Rates are probabilities per packet/ACK.
- High error rates may result in timeouts during experiments.

---

## Quick Start (Run Locally)

### Start Receiver

```
python src/rdt22_receiver.py --port 9000 --out results/received.bin --seed 2
```

### Run Sender

```
python src/rdt22_sender.py --host 127.0.0.1 --port 9000 --in data/sample.bmp --seed 1
```

Expected behavior:
- Alternating sequence numbers (0/1)
- Proper ACK responses
- Output file matches input byte-for-byte

---

## Required Demo Scenarios (Phase 2)

### Scenario 1: No errors (Option 1)

Receiver:
```
python src/rdt22_receiver.py --port 9000 --out output.bin
```

Sender:
```
python src/rdt22_sender.py --host 127.0.0.1 --port 9000 --in input.bmp
```

Expected behavior:
- No retransmissions
- Clean alternating-bit exchange
- Output matches input exactly

---

### Scenario 2: ACK corruption (Option 2)

Receiver:
```
python src/rdt22_receiver.py --port 9000 --out output.bin
```

Sender:
```
python src/rdt22_sender.py --host 127.0.0.1 --port 9000 --in input.bmp --ack-error 0.1
```

Expected behavior:
- Corrupted ACKs detected by checksum
- Sender retransmits last DATA packet
- Transfer completes successfully

---

### Scenario 3: DATA corruption (Option 3)

Receiver:
```
python src/rdt22_receiver.py --port 9000 --out output.bin --data-error 0.1
```

Sender:
```
python src/rdt22_sender.py --host 127.0.0.1 --port 9000 --in input.bmp
```

Expected behavior:
- Receiver detects corrupted DATA
- Receiver re-sends previous ACK
- Sender retransmits
- Transfer completes successfully

---

## Figures / Plots

Phase 2 includes automated performance experiments.

---

### Reproduce Experiment Runs

Run experiment sweep:

```
python src/rdt22_experiment.py --in input.bmp --out output.bmp --option 1 --runs 5
python src/rdt22_experiment.py --in input.bmp --out output.bmp --option 2 --runs 5
python src/rdt22_experiment.py --in input.bmp --out output.bmp --option 3 --runs 5
```

This sweeps error rates from 0% to 95% in 5% increments.

---

### Generate Plots

Plots are generated automatically by the experiment script:

- `results_optionX.csv`
- `plot_optionX.png`

Each point represents the average of 5 runs.

---

## Results Files

- results_option1.csv  
- results_option2.csv  
- results_option3.csv  
- plot_option1.png  
- plot_option2.png  
- plot_option3.png  

---

## Known Issues / Limitations

- Stop-and-wait protocol limits throughput at high error rates.
- Very high error rates (≥ 90%) may cause long runtimes or timeouts.
- No sliding window or congestion control implemented.
- No packet reordering support (out of scope for Phase 2).

---

## Academic Integrity / External Tools

Debugging tools (IDE debugger, logging) and LLMs were used for learning and troubleshooting. Final implementation decisions, understanding, and integration were completed by the team.


---




