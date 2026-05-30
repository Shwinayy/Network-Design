from __future__ import annotations

import argparse
import random
import socket
import time
import csv
from pathlib import Path

from common import chunk_bytes, sha256_file
from packet import Packet, TYPE_DATA, TYPE_ACK, NO_ACK, FLAG_EOF


MSS = 1024


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="input_path", required=True)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--timeout", type=float, default=0.8)
    p.add_argument("--verbose", action="store_true")

    p.add_argument("--debug", action="store_true")

    return p.parse_args()


def log(v, msg):
    if v:
        print(msg, flush=True)


def dlog(debug, msg):
    if debug:
        print(msg, flush=True)


def main():
    args = parse_args()

    data = Path(args.input_path).read_bytes()
    chunks = chunk_bytes(data, MSS)

    packets = [Packet(TYPE_DATA, seq=i, payload=c) for i, c in enumerate(chunks)]
    eof = len(packets)
    packets.append(Packet(TYPE_DATA, seq=eof, flags=FLAG_EOF))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.01)
    peer = (args.host, args.port)

    # TCP STATE
    base = 0
    nextseq = 0

    cwnd = 1
    ssthresh = 16

    dup_ack_count = 0
    last_ack = -1
    timer = None
    
    done =False
    
    ack_count = 0
    last_rwnd = 8
    
    in_fast_recovery = False #new 2
    recovery_point = 0

    send_time = {}

    start_time = time.perf_counter()
    cwnd_log = []

    # CONNECTION SETUP (SYN)
    syn = Packet(TYPE_DATA, seq=0, flags=0x02)
    sock.sendto(syn.encode(), peer)

    dlog(args.debug, "[DEBUG][SENT] SYN")

    while True:
        try:
            raw, _ = sock.recvfrom(65535)
            Packet.decode(raw)
            break
        except:
            continue

    sock.sendto(Packet(TYPE_ACK).encode(), peer)
    dlog(args.debug, "[DEBUG][HANDSHAKE COMPLETE]")
    
    
    while base < len(packets) and not done:
        #print(f"base={base}, nextseq={nextseq}, cwnd={cwnd}")
        #print("TOTAL PACKETS:", len(packets))
        #print("chunks:", len(chunks))
        window = min(cwnd, last_rwnd)

        # send window
        while nextseq < base + window and nextseq < len(packets):
            send_time[nextseq] = time.perf_counter()
            sock.sendto(packets[nextseq].encode(), peer)

            dlog(args.debug, f"[DEBUG][SENT] seq={nextseq} cwnd={cwnd} ssthresh={ssthresh}")

            if base == nextseq:
                timer = time.perf_counter()

            nextseq += 1

        # receive ACK
        try:
            raw, _ = sock.recvfrom(65535)
            pkt = Packet.decode(raw)
            ack = pkt.ack
            rwnd = pkt.rwnd
            last_rwnd = rwnd
            
            if base >= len(packets) - 1:
                dlog(args.debug, "[DEBUG][EOF ACK RECEIVED]")
                done = True

                break   
            
            dlog(args.debug, f"[DEBUG][ACK_RAW] ack={ack}")

            if ack in send_time:
                rtt = time.perf_counter() - send_time[ack]

            if ack > last_ack:
                
                if in_fast_recovery and ack >= recovery_point: # new 2
                    in_fast_recovery = False
                
                last_ack = ack
                dup_ack_count = 0
                base = ack + 1
                timer = time.perf_counter() #new 1

                dlog(args.debug, f"[DEBUG][COMPLETED] ack={ack} base={base}")

                cwnd_log.append([
                    rtt,
                    cwnd,
                    ssthresh,
                    "ack"
                ])

                # slow start / congestion avoidance
                if cwnd < ssthresh:
                    cwnd *= 2
                    dlog(args.debug, "[DEBUG][STATE] SLOW START (cwnd < ssthresh)")
                    dlog(args.debug, f"[DEBUG][CWND] cwnd={cwnd}")
                else:
                    cwnd += 1
                    dlog(args.debug, "[DEBUG][STATE] CONGESTION AVOIDANCE")
                    dlog(args.debug, f"[DEBUG][CWND] cwnd={cwnd}")
            elif ack == last_ack:
                dup_ack_count += 1
                dlog(args.debug, f"[DEBUG][DUP_ACK] count={dup_ack_count}")

                if dup_ack_count == 3 and not in_fast_recovery: # new 2
                    log(args.verbose, "FAST RETRANSMIT")

                    in_fast_recovery = True # new 2
                    recovery_point = base

                    ssthresh = max(cwnd // 2, 1)
                    cwnd = ssthresh + 3

                    sock.sendto(packets[base].encode(), peer)

                    dlog(args.debug, "[DEBUG][EVENT] FAST RETRANSMIT TRIGGERED")
                    dlog(args.debug, f"[DEBUG][STATE] ssthresh={ssthresh}, cwnd={cwnd}, seq={base}")

                    cwnd_log.append([
                        time.perf_counter() - start_time,
                        cwnd,
                        ssthresh,
                        "fast_retransmit"
                    ])

        except (socket.timeout):
            if timer and time.perf_counter() - timer > args.timeout: # new 2
                log(args.verbose, "TIMEOUT")

                ssthresh = max(cwnd // 2, 1)
                cwnd = 1
                nextseq = base
                timer = time.perf_counter()

                dlog(args.debug, "[DEBUG][EVENT] TIMEOUT RECOVERY")
                dlog(args.debug, f"[DEBUG][STATE] cwnd=1 ssthresh={ssthresh} base={base}")

                cwnd_log.append([
                    time.perf_counter() - start_time,
                    cwnd,
                    ssthresh,
                    "timeout"
                ])

    #CONNECTION BREAKDOWN
    
    #fin = Packet(TYPE_DATA, seq=0, flags=0x08)
    #sock.sendto(fin.encode(), peer)

    #dlog(args.debug, "[DEBUG][SENT] FIN")

    fin = Packet(TYPE_DATA, seq=0, flags=FLAG_EOF)

    fin_acked = False
    retries = 0

    dlog(args.debug, "[SENDING FIN]")

    while not fin_acked and retries < 50:
        try:
            sock.sendto(fin.encode(), peer)

            raw, _ = sock.recvfrom(65535)
            pkt = Packet.decode(raw)

            fin_acked = True

        except socket.timeout:
            retries += 1
        except ConnectionResetError:
            break


    with open("cwnd_log.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "cwnd", "ssthresh", "event"])
        writer.writerows(cwnd_log)

    sock.close()

    print("DONE")
    print("SHA256:", sha256_file(args.input_path))
    print("TIME:", time.perf_counter() - start_time)


if __name__ == "__main__":
    main()