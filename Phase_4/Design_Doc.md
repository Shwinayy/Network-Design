# Network Design Project – Phase 4 Design Document

## Purpose  
This document summarizes our completed Phase 4 implementation of the Go-Back-N (GBN) protocol over an unreliable UDP channel.

---

## Team Information  

**Team Name:** AC/DC  
**Members:**  
- Chris Worthley — chris_worthley@student.uml.edu  
- Daniel Burns — daniel_burns3@student.uml.edu  
- Ashwin Srinivasan — Ashwin_Srinivasan@student.uml.edu  

**GitHub Repo URL:**  
https://github.com/danieljb400/Network_and_Design/tree/main/Phase_4  

**Phase:** 4  
**Submission Date:** April 8, 2026  
**Version:** Final  

---

## 0) Executive Summary  

In Phase 4, we extended our reliable data transfer implementation to support the Go-Back-N (GBN) protocol over UDP. Unlike previous phases (RDT 2.2 and RDT 3.0), which relied on stop-and-wait transmission, GBN enables pipelined communication using a sliding window of size N.  

This allows the sender to transmit multiple packets without waiting for individual acknowledgments, improving throughput. Reliability is maintained through cumulative acknowledgments and timeout-based retransmission of unacknowledged packets.  

We validated our implementation across five required scenarios:  
- No loss or corruption  
- ACK corruption  
- DATA corruption  
- ACK loss  
- DATA loss  

Each scenario was tested across loss/error rates from 0% to 95% in 5% increments. Results were averaged across multiple runs and visualized using performance graphs.  

This phase demonstrates improved efficiency through pipelining while maintaining reliability under adverse network conditions.  

---

## 1) Phase Requirements  

### 1.1 Demo Deliverable  

A screen-recorded demo was created showing:  
- Successful file transfer  
- Recovery under packet loss or corruption  
- Verification using SHA-256  

**Private YouTube Link:**  
https://youtu.be/B5wwvRZpShg

• Timestamped outline:
00:00 – Code Showcase
00:30 – Option 1 No-loss/bit-error
01:00 – Option 2 ACK packet bit-error
01:22 – Option 3 Data packet bit-error
01:45 – Option 4 ACK packet loss 02:00 - Option 5 Data packet Loss

### 1.2 Required Demo Scenarios  

| Scenario | Configuration | Expected Behavior |
|--------|--------------|----------------|
| Option 1 | No loss/errors | Fast, correct transfer |
| Option 2 | ACK corruption | Sender retransmits after timeout |
| Option 3 | DATA corruption | Receiver discards and re-ACKs |
| Option 4 | ACK loss | Sender times out and retransmits |
| Option 5 | DATA loss | Receiver drops packets, sender retransmits |

---

### 1.3 Required Plots  

- Completion time vs loss/error rate (0–95%)  
- Completion time vs window size (fixed 10%)  
- Phase comparison (Phases 1–4)  

---

## 2) Phase Plan  

### 2.1 Scope  

#### New Features  
- Go-Back-N sliding window protocol  
- Pipelined transmission  
- Cumulative ACK handling  
- Timeout-based retransmission  
- Error and loss injection  

#### Unchanged Features  
- UDP communication  
- Checksum validation  
- File segmentation/reconstruction  

#### Out of Scope  
- Selective Repeat  
- Congestion control  
- Adaptive window sizing  

---

### 2.2 Acceptance Criteria  

- File transfers correctly (byte-for-byte match)  
- Sliding window operates correctly  
- Timeout retransmissions function  
- All 5 scenarios demonstrated  
- Graphs generated successfully  

---

### 2.3 Work Breakdown  

| Workstream | Owner |
|----------|------|
| Sender + window logic | Chris Worthley |
| Receiver + file handling | Daniel Burns |
| Experiments + plots | Ashwin Srinivasan |

---

## 3) Architecture  

### Sender Responsibilities  
- Maintain sliding window (base, nextseqnum)  
- Send packets within window  
- Handle ACKs  
- Retransmit on timeout  

### Receiver Responsibilities  
- Enforce in-order delivery  
- Detect corruption  
- Send cumulative ACKs  
- Discard out-of-order packets  

---

## 4) Packet Format  

| Field | Size | Description |
|------|-----|-----------|
| Type | 1 byte | DATA or ACK |
| Seq | 4 bytes | Sequence number |
| Length | 2 bytes | Payload size |
| Checksum | 2 bytes | Error detection |
| Flags | 1 byte | EOF flag |
| Payload | variable | Data |

---

## 5) Data Structures  

- Sender window buffer  
- Receiver expected sequence tracking  
- Packet abstraction  
- Timer for retransmission  
- Metrics collection  

---

## 6) Protocol Logic  

### Sender  
- Sends packets while window not full  
- Starts timer for oldest packet  
- Advances window on ACK  
- Retransmits entire window on timeout  

### Receiver  
- Accepts only expected sequence  
- Sends cumulative ACK  
- Discards out-of-order packets  

---

## 7) Experiments and Metrics  

### Measurement  
- Start: first packet sent  
- End: final ACK received  

### Methodology  
- Same file across all tests  
- 5 runs averaged  
- Loss/error rates: 0–95%  

---

## 8) Edge Cases  

- Lost EOF packets  
- Duplicate packets  
- Corrupted packets  
- Out-of-order packets  

All handled correctly via GBN logic.  

---

## 9) Repository Structure  

- src/  
- scripts/  
- docs/  
- results/  
- README.md  

---

## 10) Results Summary  

- Phase 4 significantly improves throughput vs earlier phases  
- Performance degrades under high loss due to retransmissions  
- Moderate window sizes provide best performance  

---

## Appendix  

### Option Mapping  

| Option | Flag |
|------|------|
| 1 | none |
| 2 | --ack-error |
| 3 | --data-error |
| 4 | --ack-loss |
| 5 | --data-loss |
