# Network Design Project – Team AC/DC

## Overview
This repository implements a UDP-based file transfer protocol across multiple phases, progressively adding reliability mechanisms and performance evaluation.  

Phase 4 focuses on implementing the Go-Back-N (GBN) protocol, enabling pipelined transmission, cumulative acknowledgments, and timeout-based retransmissions over an unreliable UDP channel.

---

## Team

| Name | Email | Primary Responsibility |
|------|------|----------------------|
| Chris Worthley | chris_worthley@student.uml.edu | Sender + GBN window logic |
| Daniel Burns | daniel_burns3@student.uml.edu | Receiver + file handling |
| Ashwin Srinivasan | Ashwin_Srinivasan@student.uml.edu | Experiments + plotting |

---

## Demo Video (submission)

• Private YouTube link: https://youtu.be/B5wwvRZpShg   

• Timestamped outline:  
00:00 – Code Showcase  
00:30 – Option 1 No-loss/bit-error  
01:00 – Option 2 ACK packet bit-error  
01:22 – Option 3 Data packet bit-error  
01:45 – Option 4 ACK packet loss
02:00 - Option 5 Data packet Loss 

---

## Repository Structure (required)

- src/ → sender, receiver, protocol utilities  
- scripts/ → experiment runner and plotting scripts  
- docs/ → design documents  
- results/ → CSV files and plots  
- README.md  

Optional:
- tests/  
- data/  
- requirements.txt  

---

## Requirements

• Language/runtime: Python 3.x  
• OS tested: Windows  

### Dependencies
Install required packages:
pip install matplotlib  

---

## Standard CLI Interface (required)

### Receiver (supported flags)

- --bind <ip>  
- --port <int>  
- --out <path>  
- --seed <int>  
- --data-error <float>  
- --data-loss <float>  

### Sender (supported flags)

- --host <ip>  
- --port <int>  
- --in <path>  
- --seed <int>  
- --window <int>  
- --timeout <float>  
- --ack-error <float>  
- --ack-loss <float>  

---

## Quick Start (Run Locally)

### Start Receiver

python src/receiver.py --bind 127.0.0.1 --port 55000 --out results/output.bin

### Run Sender

python src/sender.py --in sample_input.bin --host 127.0.0.1 --port 55000 --window 5 --timeout 0.2

---

## Required Demo Scenarios (Current Phase)

### Option 1: No Loss / No Error

Receiver:
python src/receiver.py --bind 127.0.0.1 --port 55000 --out results/output.bin

Sender:
python src/sender.py --in sample_input.bin --host 127.0.0.1 --port 55000 --window 5 --timeout 0.2

Expected behavior:
- Fast transfer  
- No retransmissions  
- Output matches input exactly  

---

### Option 2: ACK Packet Bit-Error (Recovery)

Receiver:
python src/receiver.py --bind 127.0.0.1 --port 55000 --out results/output.bin

Sender:
python src/sender.py --in sample_input.bin --host 127.0.0.1 --port 55000 --window 5 --timeout 0.2 --ack-error 0.2

Expected behavior:
- ACK packets are corrupted at the sender  
- Sender detects invalid/corrupted ACKs (ex. checksum failure)  
- Sender ignores bad ACKs  
- Sender eventually times out
- Sender retransmits window
- Transfer completes correctly despite ACK corruption  

---

### Option 3: Data Packet Bit-Error (Recovery)

Receiver:
python src/receiver.py --bind 127.0.0.1 --port 55000 --out results/output.bin --data-error 0.2

Sender:
python src/sender.py --in sample_input.bin --host 127.0.0.1 --port 55000 --window 5 --timeout 0.2

Expected behavior:
- DATA packets are corrupted at the receiver  
- Receiver detects corruption (ex. checksum mismatch)
- Receiver discards corrupted packets
- Receiver does not send ACK for bad packets (or re-ACKs last valid packet)
- Sender times out or receives duplicate ACKs
- Sender retransmits missing packets/window
- Transfer completes correctly

---

### Option 4: ACK Packet Loss (Recovery)

Receiver:
python src/receiver.py --bind 127.0.0.1 --port 55000 --out results/output.bin

Sender:
python src/sender.py --in sample_input.bin --host 127.0.0.1 --port 55000 --window 5 --timeout 0.2 --ack-loss 0.2

Expected behavior:
- ACK packets are dropped at the sender
- Sender does not receive expected ACKs
- Sender times out waiting for ACKs
- Sender retransmits entire window
- Receiver handles duplicate DATA packets correctly (no duplicate writes)
- Transfer completes correctly  

---

### Option 5: Data Packet Loss (Recovery)

Receiver:
python src/receiver.py --bind 127.0.0.1 --port 55000 --out results/output.bin --data-loss 0.2

Sender:
python src/sender.py --in sample_input.bin --host 127.0.0.1 --port 55000 --window 5 --timeout 0.2

Expected behavior:
- DATA packets are dropped at the receiver
- Receiver does not ACK missing packets
- Sender detects loss via timeout or duplicate ACKs
- Sender retransmits entire window (Go-Back-N behavior)
- Receiver correctly reassembles data without duplication
- Transfer completes successfully 

---

## Figures / Plots

### Reproduce experiment runs

python scripts/run_experiments.py --input sample_input.bin --runs 5 --window 5 --timeout 0.2 --mode all

---

### Generate plots

python scripts/plot_results.py

---

### Results files

- results_option1.csv  
- results_option2.csv  
- results_option3.csv  
- results_option4.csv  
- results_option5.csv  
- results_window_sizes.csv  

Generated plots:
- chart1_phase4_performance.png  
- chart2_window_size.png  
- chart3_phase_comparison.png  

---

## Known Issues / Limitations

- At very high loss/error rates, retransmissions may significantly increase completion time  
- Some runs may require timeout handling to prevent long execution  
- Go-Back-N retransmits entire window, leading to inefficiency under heavy loss  

---

## Academic Integrity / External Tools

Debugging tools such as IDE debuggers and logging were used.  

Large Language Models (LLMs) were used for assistance with debugging and structuring code. All final implementation decisions, logic, and understanding are our own.

---
