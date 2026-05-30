# Network Design Project – Phase Proposal & Design Document (Phase 5 of 5)

Team Name: AC/DC  
Members: Chris Worthley, Daniel Burns, Ashwin Srinivasan
GitHub Repo URL: https://github.com/danieljb400/Network_and_Design.git  
Phase: 5  
Submission Date: 4/30/26
Version: v2  

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

Phase 5 evolves the project from reliable pipelined transfer into a simplified TCP-like transport protocol over UDP. Instead of only sending reliable packets, the protocol now manages a full connection lifecycle, sender-side congestion control, receiver-side flow control, and dynamic window sizing.

Key Phase 5 additions:

Connection setup: simplified SYN → SYN-ACK → ACK handshake.
Connection teardown: reliable FIN/ACK exchange.
Dynamic sending window: sender uses min(cwnd, rwnd).
Flow control: receiver advertises available buffer space using rwnd.
Congestion control: sender implements slow start, congestion avoidance, Reno fast retransmit/fast recovery, and timeout response.
Cumulative ACKs: receiver acknowledges the highest in-order segment received.

### 3.2 Component Responsibilities

**Sender**

Reads the input file and splits it into fixed-size 1024-byte segments.
Starts the connection using a simplified TCP-style handshake.
Maintains base, nextseq, cwnd, ssthresh, duplicate ACK count, and timeout state.
Sends data using a dynamic sliding window controlled by min(cwnd, rwnd).
Processes cumulative ACKs and advances the send window.
Detects triple duplicate ACKs and performs Reno fast retransmit / fast recovery.
Detects timeout events, retransmits from the current base, reduces cwnd, updates ssthresh, and re-enters slow start.
Logs congestion window behavior for graphing.

**Receiver**

Listens on a UDP socket and receives TCP-like segments.
Buffers received segments up to the configured receiver window limit.
Delivers in-order data to the output file.
Sends cumulative ACKs for the most recently delivered segment.
Advertises remaining receiver buffer space through rwnd.
Handles EOF/FIN-style termination and closes the output file cleanly.

**Shared packet/utilities**

Packet encoding and decoding.
Internet checksum computation and validation.
Segment fields for type, sequence number, acknowledgment number, receiver window, payload length, flags, and checksum.
Loss/error helper functions and file hash verification utilities.

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

**Sender-side structures**

Sliding window variables
base: first unacknowledged segment
nextseq: next sequence number to send
Invariant: base ≤ nextseq ≤ base + window

Congestion control variables
cwnd: congestion window (dynamic)
ssthresh: slow start threshold
dup_ack_count: number of duplicate ACKs
in_fast_recovery: boolean flag
Invariant: cwnd ≥ 1, transitions follow slow start / congestion avoidance rules

Flow control variable
rwnd: last advertised receiver window
Invariant: effective send window = min(cwnd, rwnd)

Timer + retransmission tracking
timer: start time for oldest unacknowledged packet
send_time: dictionary mapping seq → send timestamp
Invariant: timer always tracks the oldest outstanding segment

Packet storage
packets[]: list of all DATA segments (including EOF)
Invariant: packets indexed by sequence number

**Receiver-side structures**

Receive buffer
buffer: dictionary mapping seq → packet
Invariant: buffer size ≤ rwnd

Sequence tracking
expected: next in-order sequence number expected
last_ack: last cumulative ACK sent
Invariant: only in-order data is delivered to file

Flow control
rwnd: configured receiver window size
Invariant: advertised window = rwnd - len(buffer)

File reconstruction
output file handle
Invariant: bytes written strictly in order

**Shared structures**

Packet structure
Fields: type, seq, ack, rwnd, flags, payload, checksum
Invariant: checksum must validate before packet is processed

Utility functions
chunking (chunk_bytes)
hashing (sha256_file) for correctness verification

---

### 5.2 Modules

CP_Sender.py
Handles connection setup, data transmission, congestion control, retransmissions, and teardown
Implements:
slow start / congestion avoidance
fast retransmit / fast recovery
timeout-based recovery

TCP_Receiver.py
Handles packet reception, buffering, flow control, cumulative ACKs, and file reconstruction
Manages advertised receive window (rwnd)

packet.py
Defines packet format and encode/decode logic
Includes checksum computation and validation

common.py
Utility functions for chunking, hashing, randomness, and file handling

---

## 6) Protocol Logic

### 6.1 Sender Behavior


While nextseq < base + effective_window:
Send DATA segment
Record send time
Start timer if first unacknowledged segment
Upon receiving ACK:
If ack > last_ack (new ACK):
Slide window: base = ack + 1
Reset duplicate ACK count
Update congestion window:
If cwnd < ssthresh: slow start → cwnd *= 2
Else: congestion avoidance → cwnd += 1
If ack == last_ack (duplicate ACK):
Increment duplicate count
On 3 duplicate ACKs:
Trigger fast retransmit
Set ssthresh = cwnd / 2
Set cwnd = ssthresh + 3
Enter fast recovery
Retransmit missing segment


---

### 6.2 Receiver Behavior


Data reception

Upon receiving DATA:
If in-order:
Deliver to file
Update expected
If out-of-order:
Buffer if space available
Send ACK:
ack = last in-order sequence
Include rwnd = available buffer space


---

### 6.3 Error Injection

Loss handling mechanisms

Duplicate ACKs → fast retransmit
Timeout → retransmission + slow start reset
Out-of-order delivery → buffering + cumulative ACK

Congestion response

Packet loss interpreted as congestion:
Triple duplicate ACK → fast recovery
Timeout → severe congestion → cwnd reset

---

## 7) Experiments + Metrics

### 7.1 Measurement

Primary metric: Completion time

Start time: when the sender begins transmission (after connection setup completes)
End time: when the sender finishes receiving the final ACK (after all data is delivered)

Measurement rules

Each experiment is run multiple times (e.g., 5 runs) per configuration.
The reported value is the average completion time.
All debug/print statements are disabled during timing runs to avoid skewing results.
The same input file is used across all experiments for consistency.

---

### 7.2 Output

Chart 1: Completion time under packet loss
| Field       | Description                                     |
| ----------- | ----------------------------------------------- |
| X-axis      | Packet loss probability (0% → 95%, step 5%)     |
| Y-axis      | Average file transfer completion time (seconds) |
| Data source | CSV file (e.g., `results/completion_time.csv`)  |
| Output      | `results/phase5_completion_time.png`            |


Chart 2: Congestion window evolution
| Field       | Description                                           |
| ----------- | ----------------------------------------------------- |
| X-axis      | Time (or RTT / transmission round)                    |
| Y-axis      | Congestion window size (`cwnd`)                       |
| Data source | Logged values during execution (e.g., `cwnd_log.csv`) |
| Output      | `results/cwnd_evolution.png`                          |

Chart 3: Phase comparison
| Field       | Description                      |
| ----------- | -------------------------------- |
| X-axis      | Phase 1 → Phase 5                |
| Y-axis      | Completion time                  |
| Data source | Aggregated results across phases |
| Output      | `results/phase_comparison.png`   |


---

**7.3 Data collection process**

Use a script or loop to:
Set packet loss rate (0% → 95%, step 5%)
Run the sender/receiver
Record completion time
Repeat 5 times
Compute average
Store results in CSV format for plotting.

**7.4 Analysis expectations**

The following observations will be discussed in the report:

Effect of flow control
Small rwnd limits throughput and increases completion time.
Effect of congestion control
cwnd growth improves throughput but reacts to loss.
Slow start vs congestion avoidance
Initial exponential growth followed by linear increase.
Fast retransmit vs timeout
Fast retransmit recovers faster than timeout-based recovery.
Parameter tuning
Values of cwnd, ssthresh, rwnd, and timeout impact performance.
Overall performance
Identify whether the implementation reaches a reasonable operating point.

## 8) Edge Cases + Tests

### 8.1 Edge Cases

| Edge case                          | Why it matters                    | Expected behavior                                                        |
| ---------------------------------- | --------------------------------- | ------------------------------------------------------------------------ |
| Duplicate ACKs (same ACK repeated) | Triggers fast retransmit          | After 3 duplicates → retransmit missing segment and enter fast recovery  |
| Packet loss in data stream         | Tests congestion control response | Sender retransmits and adjusts `cwnd`/`ssthresh` correctly               |
| Timeout event                      | Severe congestion scenario        | `cwnd` resets to 1, `ssthresh` updated, slow start restarts              |
| Receiver buffer full (`rwnd = 0`)  | Flow control limit                | Sender stops sending until window opens                                  |
| Out-of-order packet arrival        | Tests buffering logic             | Receiver buffers packet but only delivers in-order data                  |
| Lost ACK                           | Tests retransmission logic        | Sender times out and retransmits segment                                 |
| Small file (fits in one segment)   | Boundary condition                | Transfer completes correctly with proper handshake and teardown          |
| Large file (many segments)         | Stress test                       | Sliding window, congestion control, and buffering all function correctly |
| EOF/FIN handling                   | Connection termination            | Sender and receiver close connection cleanly                             |
| Connection setup failure           | Handshake robustness              | Sender retries or exits gracefully                                       |


---

### 8.2 Tests

- Packet encode/decode correctness (header + checksum)
- Checksum validation (detect corrupted packets)
- Window calculation: min(cwnd, rwnd)

---

**8.3 Test artifacts**

Console logs (debug mode)
Sender: cwnd, ssthresh, ACK events, retransmissions
Receiver: buffer state, ACKs, delivered segments

Output files
Reconstructed file at receiver side
Verified using SHA-256 hash comparison

CSV files
Completion time measurements
Congestion window logs (cwnd_log.csv)

Plots
Completion time vs loss
Congestion window evolution
Phase comparison

## 9) Repo Structure

src/
  TCP_Sender.py        # TCP-like sender over UDP
  TCP_Receiver.py      # TCP-like receiver over UDP
  packet.py            # Segment format, checksum, encode/decode
  common.py            # Chunking, hashing, file/path helpers

scripts/
  run_phase5_demo.py   # Runs required demo scenarios
  run_experiments.py   # Runs loss sweeps and repeated trials
  plot_results.py      # Generates required graphs

docs/
  DESIGN_DOCUMENT.md
  README.md

results/
  completion_time.csv
  cwnd_log.csv
  phase5_completion_time.png
  cwnd_evolution.png
  phase_comparison.png
  received_output_file


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

Milestone 1 — TCP connection framework
Basic packet format, handshake, teardown, and no-loss transfer work.

Milestone 2 — Dynamic reliability
Sliding window, cumulative ACKs, retransmissions, and receiver flow control work.

Milestone 3 — Congestion control
Slow start, congestion avoidance, Reno fast retransmit/recovery, and timeout response are visible.

Milestone 4 — Final validation
Required demos, plots, README, design document, and correctness checks are complete.

---

## Appendix

- Uses segment-based numbering
- cwnd units = segments
