# RDT 3.0 over UDP with Bit Errors and Packet Loss

This project implements **RDT 3.0** as a stop-and-wait reliable data transfer protocol on top of an unreliable UDP channel. It extends the Phase 2 design by adding **timeout-based retransmission** so the sender recovers from **lost ACK packets** and **lost DATA packets**, while still handling **bit-corrupted ACKs** and **bit-corrupted DATA packets** through checksums and duplicate ACK behavior.

The codebase includes:
- a sender that transmits a file in fixed-size chunks
- a receiver that reconstructs the file in order
- configurable fault injection for the five required Phase 3 options
- an experiment script that runs timing sweeps from 0% to 95% in 5% increments and generates CSV + plot outputs

---

## Team

**Team Name:** AC/DC

**Members**
- Chris Worthley
- Daniel Burns
- Ashwin Srinivasan

**GitHub Repo URL:** https://github.com/danieljb400/Network_and_Design/tree/main/Phase_3

**Video of Option 5 Data Loss:** https://youtu.be/vF6qiYO3UgM

---

## Project files

### Core files
- `rdt30_sender.py` — RDT 3.0 sender over UDP
- `rdt30_receiver.py` — RDT 3.0 receiver over UDP
- `rdt30_experiment.py` — experiment runner and plot generator

### Expected repo layout

```text
src/
scripts/
docs/
results/
README.md
```

If the repo remains flat during development, these three Python files can remain in the top-level folder until final cleanup.

---

## Protocol summary

This implementation uses a **stop-and-wait alternating-bit protocol**:
- sequence numbers alternate between `0` and `1`
- the sender transmits one packet at a time
- the receiver accepts only the expected sequence number
- corrupt or unexpected packets are rejected
- the receiver replies with the most recent valid ACK when needed
- the sender retransmits on timeout if it does not get a usable ACK

### Supported packet types
- **DATA**
- **ACK**
- **EOF marker** implemented as a DATA packet with:
  - zero-length payload
  - EOF flag set

### Header format

The packet header is **7 bytes** long.

| Field | Size | Description |
|---|---:|---|
| `type` | 1 byte | `0 = DATA`, `1 = ACK` |
| `seq` | 1 byte | alternating-bit sequence number |
| `len` | 2 bytes | payload length |
| `checksum` | 2 bytes | 16-bit Internet checksum |
| `flags` | 1 byte | includes EOF marker flag |

Payload follows the header and is binary-safe.

---

## Phase 3 required options

This project supports all five required Phase 3 scenarios.

| Option | Scenario | How it is injected |
|---|---|---|
| 1 | No loss / no bit-errors | No injection enabled |
| 2 | ACK packet bit-error | Sender corrupts received ACK packet using `--ack-error` |
| 3 | DATA packet bit-error | Receiver corrupts received DATA packet using `--data-error` |
| 4 | ACK packet loss | Sender drops received ACK packet using `--ack-loss` |
| 5 | DATA packet loss | Receiver drops received DATA packet using `--data-loss` |

---

## Requirements

- Python 3.10+ recommended
- `matplotlib` required for experiment plots

Install matplotlib if needed:

```bash
pip install matplotlib
```

---

## How to run

### 1. Start the receiver

Basic receiver run:

```bash
python3 rdt30_receiver.py --port 5000 --out output.bmp
```

Receiver options:
- `--bind` bind address, default `0.0.0.0`
- `--port` UDP port, default `5000`
- `--out` output file path
- `--mtu` receive buffer size, default `2048`
- `--data-error` probability of corrupting a received DATA packet
- `--data-loss` probability of dropping a received DATA packet
- `--seed` RNG seed, default `2`

### 2. Start the sender

Basic sender run:

```bash
python3 rdt30_sender.py --host 127.0.0.1 --port 5000 --in input.bmp
```

Sender options:
- `--host` destination host, default `127.0.0.1`
- `--port` destination port, default `5000`
- `--in` input file path
- `--chunk` file chunk size, default `1024`
- `--timeout` retransmission timeout in seconds, default `0.25`
- `--ack-error` probability of corrupting a received ACK packet
- `--ack-loss` probability of dropping a received ACK packet
- `--seed` RNG seed, default `1`

---

## Example runs for each required option

### Option 1 — No loss / no bit-errors

Receiver:
```bash
python3 rdt30_receiver.py --port 5000 --out output.bmp
```

Sender:
```bash
python3 rdt30_sender.py --host 127.0.0.1 --port 5000 --in input.bmp
```

### Option 2 — ACK packet bit-error

Receiver:
```bash
python3 rdt30_receiver.py --port 5000 --out output.bmp
```

Sender:
```bash
python3 rdt30_sender.py --host 127.0.0.1 --port 5000 --in input.bmp --ack-error 0.20
```

### Option 3 — DATA packet bit-error

Receiver:
```bash
python3 rdt30_receiver.py --port 5000 --out output.bmp --data-error 0.20
```

Sender:
```bash
python3 rdt30_sender.py --host 127.0.0.1 --port 5000 --in input.bmp
```

### Option 4 — ACK packet loss

Receiver:
```bash
python3 rdt30_receiver.py --port 5000 --out output.bmp
```

Sender:
```bash
python3 rdt30_sender.py --host 127.0.0.1 --port 5000 --in input.bmp --ack-loss 0.20
```

### Option 5 — DATA packet loss

Receiver:
```bash
python3 rdt30_receiver.py --port 5000 --out output.bmp --data-loss 0.20
```

Sender:
```bash
python3 rdt30_sender.py --host 127.0.0.1 --port 5000 --in input.bmp
```

---

## Experiment script

The experiment runner automates the Phase 3 timing requirement.

It:
- starts the receiver as a subprocess
- starts the sender
- measures sender completion time
- repeats each rate multiple times
- averages the results
- writes CSV output
- generates a PNG plot

### Usage

```bash
python3 rdt30_experiment.py --in input.bmp --out output.bmp --option 4 --runs 5 --port 5000
```

### Arguments

- `--in` input file to send
- `--out` output file to write
- `--option` one of `1, 2, 3, 4, 5`
- `--runs` number of runs per rate, default `5`
- `--port` UDP port, default `5000`
- `--timeout` sender retransmission timeout, default `0.25`
- `--chunk` sender chunk size, default `1024`

### Output files

For each selected option, the experiment script produces:
- `results_optionX.csv`
- `plot_optionX.png`

Where `X` is the option number.

### CSV format

| Column | Description |
|---|---|
| `rate` | error/loss rate from `0.00` to `0.95` |
| `avg_time_s` | average completion time over the configured number of runs |

---

## Running all required plots

Run the experiment script once for each option:

```bash
python3 rdt30_experiment.py --in input.bmp --out output.bmp --option 1 --runs 5 --port 5000
python3 rdt30_experiment.py --in input.bmp --out output.bmp --option 2 --runs 5 --port 5000
python3 rdt30_experiment.py --in input.bmp --out output.bmp --option 3 --runs 5 --port 5000
python3 rdt30_experiment.py --in input.bmp --out output.bmp --option 4 --runs 5 --port 5000
python3 rdt30_experiment.py --in input.bmp --out output.bmp --option 5 --runs 5 --port 5000
```

After generation, move the outputs into `results/` if needed.

---

## Correctness checks

Recommended validation steps:
1. Run Option 1 at 0% error/loss and confirm the output file opens correctly.
2. Compare input and output files byte-for-byte.
3. Re-run the same scenario using the same seeds and confirm behavior is consistent.
4. Check that higher loss/error rates generally increase completion time.
5. Confirm the sender always exits only after EOF is acknowledged.

### Example file comparison

Linux/macOS:
```bash
cmp input.bmp output.bmp
```

Or hash comparison:
```bash
sha256sum input.bmp output.bmp
```

Windows PowerShell:
```powershell
Get-FileHash input.bmp
Get-FileHash output.bmp
```

---

## Design choices

### 1. Stop-and-wait with alternating bit
We use sequence numbers `0` and `1` because Phase 3 still uses a non-pipelined protocol.

### 2. Internet checksum
The checksum is computed over the header and payload and is used to detect bit corruption.

### 3. Timeout-based recovery
This is the main addition for RDT 3.0. If an ACK is lost or the DATA packet never reaches the receiver, the sender eventually times out and retransmits.

### 4. Receiver behavior matches RDT 2.2
The receiver does not need a timer. It:
- accepts expected in-order packets
- discards corrupt or unexpected packets
- sends ACKs for the last valid packet

### 5. EOF as a flagged DATA packet
Instead of using a separate packet type for termination, this design uses a zero-length DATA packet with an EOF flag.

---

## Reproducibility

The sender and receiver both use fixed default seeds:
- sender seed default: `1`
- receiver seed default: `2`

Because loss/corruption injection is pseudo-random and seeded, the same run configuration is reproducible.

To keep results more consistent:
- use the same input file for all options
- keep timeout and chunk size constant during experiments
- avoid extra console printing during timing runs
- run all five trials for every rate

---

## Known limitations

- This is a **stop-and-wait** design, so performance drops significantly at high loss/error rates.
- The protocol does not support pipelining or multiple outstanding packets.
- There is no congestion control or adaptive timeout calculation.
- The experiment script may time out on extremely high loss scenarios depending on file size and timeout value.

---

## Suggested final repo organization

```text
.
├── README.md
├── docs/
│   └── DESIGN_DOCUMENT_PHASE3.md
├── results/
│   ├── results_option1.csv
│   ├── results_option2.csv
│   ├── results_option3.csv
│   ├── results_option4.csv
│   ├── results_option5.csv
│   ├── plot_option1.png
│   ├── plot_option2.png
│   ├── plot_option3.png
│   ├── plot_option4.png
│   └── plot_option5.png
├── scripts/
│   └── rdt30_experiment.py
└── src/
    ├── rdt30_sender.py
    └── rdt30_receiver.py
```

---

## Submission checklist

- [x] Design document completed
- [x] README completed
- [x] Sender and receiver tested
- [x] All five options demonstrated
- [x] Output file verified against input file
- [x] Five CSV files generated
- [x] Five plot images generated
- [x] Demo video recorded
- [x] Final repo organized cleanly

---

## Authors

Chris Worthley, Daniel Burns, and Ashwin Srinivasan

