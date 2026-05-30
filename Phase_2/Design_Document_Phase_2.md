# Network Design Project – Phase Proposal & Design Document  
**Phase 2 of 5**

**Team Name:** AC/DC – Phase 2  
**Members:**  
- Chris Worthley (chris_worthley@student.uml.edu)  
- Daniel Burns (daniel_burns3@student.uml.edu)  
- Ashwin Srinivasan (Ashwin_Srinivasan@student.uml.edu)  

**GitHub Repo URL:** https://github.com/danieljb400/Network_and_Design.git  
**Phase:** 2  
**Submission Date:** 02/20/2026  
**Version:** v1  

---

## 0) Executive Summary

In this phase, the existing Phase 1 UDP channel-based file transfer system is enhanced to support implementation of the RDT 2.2 reliable data transfer protocol over an unreliable channel with bit errors. Unlike Phase 1, the UDP channel is treated as unreliable in accordance with RFC 768.

The RDT 2.2 protocol implements reliable data transfer over an unreliable channel using a stop-and-wait approach. The sender transmits one DATA packet at a time and waits for a valid ACK. If a corrupted DATA packet is detected at the receiver, the receiver re-sends the previous ACK. If a corrupted ACK is detected at the sender, the sender retransmits the last DATA packet. Packet integrity is verified using a 16-bit Internet checksum.

EOF signaling is implemented using a zero-length DATA packet with an EOF flag set. Reliability is demonstrated through required demo scenarios, byte-for-byte file verification, and performance experiments measuring average completion time across error rates from 0% to 95%.

---

## 1) Phase Requirements

### 1.1 Demo Deliverable

A screen recording demonstrating all required scenarios.

YouTube link: https://youtu.be/VD65wKMSDzY  

Timestamped outline (mm:ss → scenario):  
-  

---

### 1.2 Required Demo Scenarios

**Scenario 1 – No loss / no bit-errors**  
Configuration: Error rate = 0%  
Expected Behavior: File transfers successfully with alternating sequence numbers (0/1) and ACKs; no retransmissions occur. Output file matches input byte-for-byte.

**Scenario 2 – ACK packet bit-error (Option 2)**  
Configuration: ACK corruption enabled at sender after `recvfrom`  
Expected Behavior: Sender detects corrupted ACK via checksum and retransmits the last DATA packet. Transfer completes correctly.

**Scenario 3 – DATA packet bit-error (Option 3)**  
Configuration: DATA corruption enabled at receiver after `recvfrom`  
Expected Behavior: Receiver discards corrupted DATA packet and re-ACKs the last correctly received sequence number. Sender retransmits. Transfer completes correctly.

---

### 1.3 Required Figures / Plots

Figure 1 plots average completion time versus error rate.

X-axis: Error rate (%)  
Y-axis: Average completion time (seconds)  
Sweep range: 0% to 95% in increments of 5%  

Generated files per option:  
- results_optionX.csv  
- plot_optionX.png  

Each data point is the average of 5 runs.

---

## 2) Phase Plan

### 2.1 Scope

New behaviors added:

- Implement RDT 2.2 over UDP  
- Add checksum validation for DATA and ACK packets  
- Add alternating sequence numbers (0/1)  
- Enforce stop-and-wait transmission  
- Implement ACK-only (NAK-free) recovery  
- Add configurable corruption and loss simulation  
- Add automated experiment runner and plotting  

Unchanged from Phase 1:

- UDP socket usage  
- CLI-based execution  
- Fixed-size packet segmentation (1024 bytes)  
- In-order file reconstruction  
- Explicit end-of-transfer signaling  

Out of scope:

- Sliding windows or pipelining  
- Congestion control  
- Packet reordering  
- Security features  

---

### 2.2 Acceptance Criteria

- Sender and receiver accept configurable error rates  
- Checksums detect corrupted DATA and ACK packets  
- Sequence numbers alternate correctly  
- Corrupted ACK triggers retransmission  
- Corrupted DATA triggers duplicate ACK behavior  
- All three required demo scenarios complete successfully  
- Output file matches input byte-for-byte  
- Completion time measured from 0% to 95% in 5% increments  
- Each data point averaged over 5 runs  
- CSV and plot files generated correctly  

---

## 3) Architecture

Phase 2 implements stop-and-wait RDT 2.2 over an unreliable UDP channel.

Key additions compared to Phase 1:

- Internet checksum validation  
- Alternating sequence numbers  
- ACK-only recovery  
- Deterministic corruption and loss injection  
- EOF implemented via flagged DATA packet  

Sender and receiver follow the RDT 2.2 finite state machine semantics described in Kurose & Ross Section 3.4.1.

---

## 4) Packet Format

Packet types:

- DATA (type = 0)  
- ACK (type = 1)  

EOF is represented as a DATA packet with zero-length payload and the EOF flag set.

Header fields:

- type (1 byte)  
- seq (1 byte, 0 or 1)  
- len (2 bytes, payload length)  
- checksum (2 bytes, Internet checksum over header + payload)  
- flags (1 byte, bit0 = EOF)  
- payload (up to 1024 bytes for DATA packets)  

---

## 5) Implementation Modules

Repository files:

- rdt22_sender.py – Sender FSM and ACK corruption/loss simulation  
- rdt22_receiver.py – Receiver FSM and DATA corruption/loss simulation  
- rdt22_experiment.py – Experiment runner, CSV generation, and plotting  

---

## 6) Protocol Logic

### Sender

- Sends one DATA packet at a time  
- Waits for ACK  
- Retransmits on timeout  
- Retransmits if ACK is corrupted  
- Ignores duplicate or incorrect ACKs  
- Toggles sequence number on successful ACK  
- Sends EOF DATA packet and waits for its ACK  

### Receiver

- Parses and validates incoming packet  
- Verifies checksum  
- If corrupted or unexpected sequence number, resends last ACK  
- Writes valid payload to output file  
- On valid EOF packet, sends final ACK and terminates  

---

## 7) Experiments and Metrics

Error rates tested:

0, 5, 10, 15, 20, 25, 30, 35, 40, 45,  
50, 55, 60, 65, 70, 75, 80, 85, 90, 95  

For each rate:

- Run 5 transfers  
- Receiver launched in subprocess  
- Sender execution time measured using wall-clock timing  
- Timeouts recorded as NaN  
- Average computed ignoring NaN values  

Outputs per option:

- results_optionX.csv (columns: rate, avg_time_s)  
- plot_optionX.png  

---

## 8) Edge Cases and Testing

Edge cases handled:

- Corrupted ACK  
- Corrupted DATA  
- Duplicate DATA  
- EOF retransmissions  
- High error rate behavior  

Testing performed:

- Checksum validation test  
- Packet encode/decode consistency test  
- Byte-for-byte file comparison  
- High-error stress testing  

---

## 9) Repository Structure

src/  
docs/  
results/  
README.md  

Design document stored in docs/.  
Experiment outputs may be stored at the repository root or moved into results/.

---

## 10) Team Plan

### Task Ownership

| Task | Owner |
|------|-------|
| Packet format + checksum | Chris |
| Sender FSM | Daniel |
| Receiver FSM | Ashwin |
| Error injection | Chris |
| Plotting + experiments | Daniel |
| Documentation + demo | All |

---

### Milestones

- Packet + checksum complete  
- FSM working in no-error mode  
- Error scenarios validated  
- Performance plots generated  
- Final documentation + demo complete  

---

## Appendix

N/A
