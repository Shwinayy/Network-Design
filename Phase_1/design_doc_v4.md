Network Design Project – Phase Proposal & Design Document (Phase 1 of 5)  

Purpose: This document is the team’s proposal for how we will implement the current phase before coding. 

Team Name: Ac/Dc 

Members: (Ashwin Srinivasan, Ashwin_Srinivasan@student.uml.edu), (Dan Burns, Daniel_Burns3@student.uml), Chris Worthley (Chris_Worthley@student.uml.edu)  

GitHub Repo URL (with GitHub usernames): https://github.com/danieljb400/Network_and_Design (shwinayy, danieljb400, worthleychristopher-dev) 

Phase: 1 

Submission Date: 1/30/25 

Version: v4 

Demo: https://youtu.be/1YCXv2ixqvw 

Executive Summary 

In this phase, we will be implementing the UDP-based client/server application using Python, which supports bidirectional messaging as well as reliable file transfer operations. To begin, we will create the UDP client application as well as the UDP server application to communicate information to each other through simple messaging operations. For the UDP application, the client will send the simple UDP “Hello” message to the UDP server application, which will then send back the same information to the client application to ensure that the operations have taken place properly. Following the implementation of the UDP application, we will begin our RDT1.0 implementation to transfer information from the UDP client application to the UDP server application. RDT1.0 is completed when the echoed message from the server has the same value as the input option as well as when the file has the same content as the original file sent from the client to the server application. Recordings will also be obtained to ensure the validation of our UDP client/server application as well as the RDT1.0 protocol implementation. 

 

     1)  Phase requirements 

1.1 Demo deliverable  

We will submit a recording demonstrating the required Phase 1 scenarios end-to-end: 

UDP “HELLO” + ECHO message exchange (client → server → client) 

UDP file transfer using RDT 1.0 (client sends file, server reconstructs and writes output) 

1.2 Required demo scenarios 

Scenario 

What you will inject / configure 

Expected observable behavior 

What we will see in the video 

1 — UDP HELLO + ECHO 

Start UDP server on port X; run UDP client targeting server IP/port; client sends "HELLO" 

Server receives message and echoes it back; client prints echoed message; both processes remain stable 

Terminal windows for client/server: client sends HELLO, server prints received data, client prints echoed HELLO 

2 — RDT 1.0 file transfer (BMP recommended) 

Select a transfer file (e.g., BMP); segment into fixed-size packets (e.g., 1024B); send one packet at a time using UDP 

Receiver accepts packets in order and reconstructs the full file; output file is produced successfully on server 

Client shows “sending packet i/N”; server shows “received packet i/N” and writes output file (e.g., output.bmp) 

3—Correctness verification (byte-for-byte) 

After transfer, compare input vs output using hash (SHA-256/MD5) or byte-compare 

Hashes match (or byte-compare passes), proving exact reconstruction 

Command outputs showing matching hashes and/or diff success; optionally open the BMP to visually confirm 

1.3 Required figures / plots 

N/A 

2) Phase plan 

2.1 Scope: what changes/additions this phase 

New behaviors added: 

UDP client–server message exchange implementing a HELLO → ECHO round-trip. 

UDP-based file transfer using RDT 1.0, sending one fixed-size packet (1024B) at a time. 

File segmentation at the sender and deterministic, in-order file reconstruction at the receiver. 

Minimal CLI configuration for server address, ports, input file, and output file. 

Behaviors unchanged from previous phase: 

N/A (this is the first implementation phase). 

Out of scope (explicitly): 

Packet loss, corruption, or reordering handling. 

Retransmissions, timeouts, sliding windows, or pipelining. 

Performance optimization or congestion control. 

Security (encryption/authentication). 

2.2 Acceptance criteria 

□ UDP client and server start successfully with standard CLI flags 
□ Client sends "HELLO" and receives the correct echoed response 
□ File is segmented into 1024-byte packets and sent one packet at a time 
□ Receiver reconstructs the file in-order without modification 
□ Output file matches input file byte-for-byte (hash or diff) 
□ Demo video clearly shows both scenarios end-to-end 
□ Code runs deterministically on re-run using the same inputs 
□ Source code follows the documented packet format and module structure 

2.3 Work breakdown (high-level) 

Workstream A— UDP socket foundation 

Implement UDP client/server sockets 

HELLO/ECHO message exchange 

Basic CLI argument parsing 

Workstream B— RDT 1.0 sender 

File parsing and packetization (Make_Packet) 

Sequential packet send logic (one packet at a time) 

End-of-file handling 

Workstream C— RDT 1.0 receiver 

Packet receive and validation 

In-order file reconstruction and write to disk 

Minimal logging for demo visibility 

Workstream D— Validation & documentation 

Demo recording preparation 

File correctness verification (hash/byte-compare) 

README and design document finalization 

3) Architecture + state diagrams 

3.1 How to evolve the provided state diagram 

Current Phase (Phase 1) Sender FSM (RDT 1.0, one-at-a-time): 

WAIT_FOR_CALL_FROM_ABOVE: read next chunk of file (or message) from application 

SEND_PACKET: build packet and send via UDP 

transition back to WAIT_FOR_CALL_FROM_ABOVE until EOF, then terminate 

Current Phase (Phase 1) Receiver FSM (RDT 1.0): 

WAIT_FOR_PACKET: block on UDP receive 

DELIVER_DATA: write payload to output (file reconstruction) and return to wait state 

terminate when end-of-transfer condition is met (see Section 6 for termination condition) 

3.2 Component responsibilities 

Sender (UDP Client) 

Parse CLI args: server IP/port, input filename, mode (HELLO vs FILE) 

For HELLO mode: 

Send a single datagram containing "HELLO" 

Receive echoed response and print it 

For FILE mode (RDT 1.0): 

Open input file in binary mode 

Segment file into fixed-size chunks (1024B payload per packet) 

For each chunk: create packet, send via UDP (one at a time) 

Send explicit end-of-transfer marker (or final packet indicator) so receiver knows when to stop 

Receiver (UDP Server) 

Bind UDP socket to listen on specified port 

For HELLO mode: 

Receive datagram and echo the exact bytes back to the sender 

For FILE mode (RDT 1.0): 

Receive packets sequentially 

Extract payload and append/write to output file in deterministic order 

Detect end-of-transfer and close output file cleanly 

Shared modules / utilities 

packet encode/decode: define header + payload layout, pack/unpack bytes consistently 

logging/timing: minimal console logs for demo (packet index / bytes sent/received) 

CLI/config parsing: argparse wrapper shared between sender/receiver scripts 

3.3 Message flow overview 

1a:  

[client] -- UDP datagram: "HELLO" --> [server] 

[client] <-- UDP datagram: "HELLO" -- [server] 

1b:  

[input file] -> Sender (packetize: 1024B payloads) 

Sender -- UDP: DATA(pkt0) --> Receiver 

Sender -- UDP: DATA(pkt1) --> Receiver 

Sender -- UDP: DATA(pktN or END) --> Receiver 

Receiver (append payloads in order) -> [output file] 

4) Packet format 

4.1 Packet types 

HELLO packet 

Purpose: Verify bidirectional UDP communication (Phase 1a) 

Payload contains an ASCII string (e.g., "HELLO") 

DATA packet 

Purpose: Carry file data during RDT 1.0 file transfer (Phase 1b) 

Payload contains a binary file chunk (up to 1024 bytes) 

END packet (end-of-transfer) 

Purpose: Explicitly indicate completion of file transfer 

Payload length is zero 

Allows receiver to terminate cleanly and close the output file 

4.2 Header fields 

Field 

Size 

Type 

Description 

Notes 

type 

1 byte 

uint8 

Packet type identifier 

0 = HELLO, 1 = DATA, 2 = END 

seq 

4 bytes 

uint32 

Sequence number 

Increments by 1 per DATA packet 

len 

2 bytes 

uint16 

Payload length (bytes) 

0 ≤ len ≤ 1024 

payload 

len bytes 

bytes 

Message or file data 

Binary-safe 

5) Data structures + module map 

5.1 Key data structures 

Sender-side structures 

SenderConfig (from CLI / argparse) 

Fields: server_ip, server_port, mode (hello or file), input_path, chunk_size=1024, verbose 

Invariants: chunk_size fixed at 1024; server_port valid; input_path required for file mode 

Lives in: src/sender.py (or src/config.py if shared) 

seq_num (integer counter) 

Purpose: sequence number added to DATA packets (monotonic increasing) 

Invariants: starts at 0; increments by 1 per DATA packet 

Lives in: src/sender.py 

File read handle 

Purpose: read binary chunks from disk 

Invariants: opened in "rb"; read size = chunk_size 

Lives in: src/sender.py 

Receiver-side structures 

ReceiverConfig (from CLI / argparse) 

Fields: bind_ip (often 0.0.0.0), bind_port, mode, output_path, verbose 

Invariants: output_path required for file mode; bind_port valid 

Lives in: src/receiver.py (or src/config.py) 

File write handle 

Purpose: reconstruct and write received payload bytes to output file 

Invariants: opened in "wb"; writes exactly len bytes from each DATA payload 

Lives in: src/receiver.py 

(Optional) expected_seq 

Purpose: track expected sequence number for sanity checking / debug output (not required for RDT 1.0 correctness under perfect channel assumptions) 

Invariants: starts at 0; increments by 1 per DATA packet received 

Lives in: src/receiver.py 

Shared structures 

Packet representation (logical struct) 

Fields: type, seq, len, payload 

Invariants: len == len(payload); 0 ≤ len ≤ 1024 

Lives in: src/packet.py (encode/decode helpers) 

5.2 Module map + dependencies 

src/sender.py 

CLI parsing (client mode selection) 

HELLO send/receive 

File packetization + send loop (RDT 1.0) 

src/receiver.py 

UDP bind + receive loop 

HELLO echo handling 

File reconstruction + END handling 

src/packet.py 

encode_packet(type, seq, payload) → bytes 

decode_packet(datagram) → (type, seq, payload) 

Field packing/unpacking per Section 4 

src/utils.py (optional but clean) 

Common helpers (argument validation, logging wrappers) 

scripts/ (optional for demo/test convenience) 

scripts/run_hello_demo.sh / .py 

scripts/run_file_demo.sh / .py 

scripts/verify_transfer.py (hash compare) 

Dependency sketch: 

sender  -> packet, (utils) 

receiver -> packet, (utils) 

scripts -> sender/receiver CLI + verify helpers 

6) Protocol logic 

6.1 Sender behavior 

Mode A — HELLO/ECHO sender behavior 

Create UDP socket. 

Build a HELLO packet containing the payload "HELLO" (or user-provided text). 

Send HELLO datagram to (server_ip, server_port). 

Block on recvfrom() to receive echoed response. 

Print received payload and exit cleanly. 

Mode B — File transfer sender behavior (RDT 1.0) 

Create UDP socket. 

Open input file in binary mode. 

Initialize seq = 0. 

Repeatedly read up to 1024 bytes from the file. 

If bytes were read: build a DATA packet with (type=DATA, seq, len, payload) and send it. 

Increment seq by 1. 

After EOF, send an END packet (type=END, seq=last_seq+1, len=0, payload=b""). 

Close file and socket; terminate. 

Sender termination condition 

Sender terminates immediately after transmitting the END marker 

6.2 Receiver behavior 

Mode A — HELLO/ECHO receiver behavior 

Create UDP socket and bind() to (bind_ip, bind_port). 

Block on recvfrom() for a datagram. 

Decode packet; if type is HELLO: 

Echo the payload back to clientAddress (either raw datagram or re-encoded packet, consistently with sender). 

Continue listening (or exit after one exchange, depending on CLI option; for demo simplicity we can run continuously). 

Mode B — File transfer receiver behavior (RDT 1.0) 

Create UDP socket and bind() to (bind_ip, bind_port). 

Open output file in binary write mode. 

Initialize expected_seq = 0 (optional sanity check). 

Loop receiving datagrams: 

Decode packet into (type, seq, payload). 

If type == DATA: 

(Optional) if seq != expected_seq, log warning (not expected in perfect channel). 

Write payload bytes to output file. 

expected_seq += 1 

If type == END: 

Close output file and terminate cleanly. 

Close socket. 

6.3 Error/loss injection spec 

N/A 

7) Experiments + metrics plan 

7.1 Measurement definition 

N/A, Phase 1 focuses on implementing UDP sockets and RDT 1.0 semantics (one packet at a time) and does not require performance experiments or timing-based evaluation. 

7.2 Output artifacts 

N/A, no CSV outputs or plots are required. The primary artifacts for validation are 

Demo recording (HELLO/ECHO + file transfer) 

Output file generated by receiver 

8) Edge cases + test plan 

8.1 Edge cases you expect 

Edge case 

Why it matters 

Expected behavior 

Last packet smaller than payload size (file size not multiple of 1024) 

Ensures correct file reconstruction and no extra bytes appended 

Sender sets len to actual bytes read; receiver writes exactly len bytes; output matches input 

Empty file (0 bytes) 

Validates clean termination and correct handling of EOF 

Sender immediately sends END packet; receiver creates empty output file and terminates 

Very small file (<1024B) 

Common case; exercises “single DATA packet then END” 

Receiver writes one chunk, then stops on END; output matches input 

HELLO message with non-ASCII / different length 

Confirms program is binary-safe / robust for arbitrary message payloads 

Server echoes exact bytes; client prints received payload correctly 

Unexpected packet type received in current mode 

Prevents crashes if a user runs mismatched modes (client file mode, server hello mode) 

Receiver logs and ignores unknown packet type (or exits with a clear error), does not crash 

Output path already exists 

Avoids overwriting issues or unclear behavior 

Receiver either overwrites deterministically (documented) or refuses unless a --force flag is used (documented) 

Running client/server on same host but different ports 

Required by spec; easy to misconfigure 

Client and server communicate correctly when ports are distinct and correctly specified 

 

8.2 Tests you will write because of these edge cases 

Unit tests (optional but recommended) 

Packet encode/decode round-trip 

Create a packet with known fields/payload; encode then decode; verify all fields match. 

Header field sanity 

Verify len == len(payload) and 0 ≤ len ≤ 1024 before send. 

Integration tests (recommended) 

HELLO/ECHO correctness 

Start server, run client sending "HELLO", assert returned payload equals sent payload. 

File transfer correctness — hash match 

Transfer a BMP (or any binary file) and compute hashes for input and output (e.g., SHA-256); assert equality. 

Last-packet size handling 

Transfer a file whose size is not divisible by 1024; verify output hash matches input. 

Empty file transfer 

Transfer an empty file; verify output exists and is 0 bytes. 

Small file transfer 

Transfer a tiny file (<1024B) and verify output hash matches input. 

8.3 Test artifacts 

Console logs (minimal): 

Client: packet index/seq, bytes sent, “END sent” 

Server: packet index/seq, bytes received, “END received—closing output” 

Test locations: 

Quick integration scripts under scripts/ (e.g., scripts/run_hello_demo.py, scripts/run_file_demo.py, scripts/verify_transfer.py) 

Optional unit tests 

Correctness proof artifacts: 

Hash outputs (printed in terminal and optionally recorded in the demo video) 

Output file saved to disk on receiver side for manual inspection 

9) Repo structure + reproducibility 

src/ 

  sender.py          # UDP client: HELLO/ECHO + RDT 1.0 file sender 

  receiver.py        # UDP server: echo + file receiver/reconstruction 

  packet.py          # Packet encode/decode logic (header + payload) 

  utils.py           # (optional) shared helpers: logging, arg checks 

 

scripts/ 

  run_hello_demo.py  # Convenience script to run HELLO/ECHO demo 

  run_file_demo.py   # Convenience script to run file transfer demo 

  verify_transfer.py # Hash/byte-compare to verify correctness 

  

docs/ 

  DESIGN_DOCUMENT.md (or .pdf)  # Phase 1 design document 

  diagrams/                     # FSM or architecture diagrams (if included) 

  

results/ 

  output_files/     # Receiver-generated output files (e.g., output.bmp) 

  logs/             # Optional demo/test logs 

README.md           # How to run, demo, and reproduce results 

 

10) Team plan, ownership, and milestones 

10.1 Task ownership 

Task 

Owner 

Target date 

Definition of done 

Packet format + encode/decode 

Team Member A 

Day 1 

Header fields implemented; encode/decode round-trip verified 

sender logic 

Team Member B 

Day 2 

File segmented into 1024B packets; DATA + END packets sent sequentially 

receiver logic 

Team Member C 

Day 2 

File reconstructed deterministically; END handled cleanly 

README + design doc finalization 

ALL 

Day 3 

Docs are complete, accurate, and reproducible 

10.2 Milestones 

Milestone 1— UDP foundation complete 

UDP client and server implemented 

HELLO/ECHO message exchange verified 

Milestone 2— RDT 1.0 file transfer working 

File packetization and sequential send complete 

Receiver reconstructs file and detects END-of-transfer 

Milestone 3— Validation and submission-ready 

All edge cases tested 

Demo video recorded 

Design document and README finalized and reviewed 
