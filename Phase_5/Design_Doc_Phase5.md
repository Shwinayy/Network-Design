
# Network Design Project – Phase Proposal & Design Document (Phase 5 of 5)

Team Name: AC/DC  
Members: Chris Worthley, Daniel Burns, Ashwin Srinivasan
GitHub Repo URL: https://github.com/danieljb400/Network_and_Design.git  
Phase: 5  
Submission Date: 4/17/26
Version: v1  

---

## 0) Executive Summary

In Phase 5, we extend our reliable UDP-based transport into a TCP-like protocol supporting connection-oriented communication, dynamic windowing, flow control, and congestion control. Specifically, we implement a simplified TCP three-way handshake (SYN, SYN-ACK, ACK), reliable data transfer using cumulative ACKs, and a connection teardown using FIN/ACK exchange. 

We introduce a dynamic sender window governed by both congestion window (cwnd) and receiver-advertised window (rwnd), ensuring correct flow-control behavior. Additionally, we implement TCP Reno congestion control, including slow start, congestion avoidance, fast retransmit, fast recovery, and timeout-based recovery.

“Done” means: successful file transfer with byte-for-byte correctness, correct behavior across all five required scenarios, and generation of required plots (completion time vs loss, cwnd evolution, phase comparison). Validation is performed through demo scenarios, automated testing, and reproducible experiments.

---

## 1) Phase Requirements

### 1.1 Demo Deliverable

• Private YouTube link: (fill at final submission)  
• Timestamp outline: (TBD)

---

### 1.2 Required Demo Scenarios

| Scenario | Injection/Config | Expected Behavior | What We Show |
|----------|----------------|------------------|--------------|
| 1 | No loss | Successful handshake, transfer, teardown | Full clean run |
| 2 | Small rwnd | Sender throttled by rwnd | Window-limited sending |
| 3 | Normal run | cwnd exponential then linear | cwnd plot |
| 4 | Packet loss (dup ACKs) | Fast retransmit + recovery | triple ACK behavior |
| 5 | Packet loss (timeout) | cwnd reset, slow start restart | timeout recovery |

---

### 1.3 Required Figures / Plots

| Plot | X-axis | Y-axis | Range | Data Source | Output |
|------|--------|--------|-------|-------------|--------|
| Chart 1 | Loss rate (%) | Completion time | 0–95 step 5 | CSV | results/phase5_loss.png |
| Chart 2 | Time/RTT | cwnd | full run | log | results/cwnd.png |
| Chart 3 | Phase | Completion time | P1–P5 | CSV | results/phase_compare.png |

---

## 2) Phase Plan

### 2.1 Scope

**New behaviors:**
- TCP 3-way handshake (SYN, SYN-ACK, ACK)
- FIN-based teardown
- Dynamic window (cwnd + rwnd)
- TCP Reno congestion control
- Flow control via advertised window

**Unchanged:**
- UDP transport layer
- Checksum logic
- Packet segmentation (~1024 bytes)

**Out of scope:**
- SACK
- Multiplexing
- Byte-level sequence numbering (segment-based used)

---

### 2.2 Acceptance Criteria

- [ ] Successful handshake and teardown
- [ ] Byte-for-byte file correctness
- [ ] cwnd and rwnd enforced properly
- [ ] All 5 scenarios demonstrated
- [ ] Reno behavior correctly implemented
- [ ] Plots generated correctly
- [ ] Results reproducible

---

### 2.3 Work Breakdown

- Transport logic (sender/receiver)
- Congestion control module
- Flow control + rwnd handling
- Experiment scripts + plotting

---

## 3) Architecture + State Diagrams

### 3.1 Evolution

New states added:
- CLOSED → SYN_SENT → ESTABLISHED → FIN_WAIT → CLOSED

### 3.2 Component Responsibilities

**Sender**
- Manage cwnd, ssthresh
- Handle retransmissions
- Perform handshake/teardown

**Receiver**
- Buffer + reassemble data
- Advertise rwnd
- Send cumulative ACKs

**Shared**
- packet encoding/decoding
- checksum
- logging

---

### 3.3 Message Flow


[file] → Sender → UDP → Receiver → [output file]
↑ ↓
└──── ACK / rwnd ─────┘


---

## 4) Packet Format

### 4.1 Packet Types
- SYN
- SYN-ACK
- ACK
- DATA
- FIN

---

### 4.2 Header Fields

| Field | Size | Description |
|------|------|-------------|
| type | 1B | packet type |
| seq | 4B | sequence number |
| ack | 4B | acknowledgment number |
| flags | 1B | SYN/ACK/FIN |
| rwnd | 2B | receiver window |
| len | 2B | payload size |
| checksum | 2B | integrity |
| payload | ≤1024B | data |

---

## 5) Data Structures + Module Map

### 5.1 Structures

- sender_window
- receiver_buffer
- cwnd, ssthresh
- timers
- metrics collector

---

### 5.2 Modules

- src/sender.py
- src/receiver.py
- src/packet.py
- src/checksum.py
- scripts/experiments.py
- scripts/plot.py

---

## 6) Protocol Logic

### 6.1 Sender Behavior


initialize
perform handshake
while data:
send min(cwnd, rwnd)
wait for ACK
if ACK valid:
advance window
update cwnd
if duplicate ACKs:
fast retransmit
if timeout:
reduce cwnd, retransmit
send FIN


---

### 6.2 Receiver Behavior


on receive:
if corrupt: discard
if expected:
accept + ACK
if duplicate:
resend ACK
advertise rwnd


---

### 6.3 Error Injection

- Inject at sender/receiver
- Loss probability configurable
- Fixed RNG seed for reproducibility

---

## 7) Experiments + Metrics

### 7.1 Measurement

- Start: first SYN
- End: final ACK
- Disable logging during runs
- 5 runs per point

---

### 7.2 Output

- CSV format:
  - loss_rate, run_id, time
- Stored in `results/`

---

## 8) Edge Cases + Tests

### 8.1 Edge Cases

| Case | Expected |
|------|----------|
| last packet | correct size |
| duplicate ACKs | ignored |
| timeout | cwnd reset |
| FIN loss | retransmit |

---

### 8.2 Tests

- checksum validation
- encode/decode tests
- full transfer verification

---

## 9) Repo Structure


src/
scripts/
docs/
results/
README.md


---

## 10) Team Plan

### 10.1 Tasks

| Task | Owner | Done |
|------|------|------|
| Packet format | Chris | encode/decode works |
| Sender logic | Chris | passes tests |
| Receiver logic | Ashwin | correct ACK behavior |
| Congestion control | Daniel | Reno verified |
| Plots | Daniel | charts generated |

---

### 10.2 Milestones

- M1: Handshake + teardown working
- M2: Reliable transfer + flow control
- M3: Congestion control + plots complete

---

## Appendix

- Uses segment-based numbering
- cwnd units = segments
