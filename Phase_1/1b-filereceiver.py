from socket import *
import struct

SERVER_PORT = 12000
CHUNK_SIZE = 1024

HEADER_FMT = "!IHB"   # seq (4 bytes), data_len (2 bytes), is_last (1 byte)
HEADER_SIZE = struct.calcsize(HEADER_FMT)

OUT_FILENAME = "received.bmp"

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(("", SERVER_PORT))

print(f"[1b SERVER] Ready on UDP port {SERVER_PORT}")
print(f"[1b SERVER] Writing output to {OUT_FILENAME}")

chunks = {}
last_seq = None

try:
    while True:
        packet, clientAddress = serverSocket.recvfrom(HEADER_SIZE + CHUNK_SIZE)

        if len(packet) < HEADER_SIZE:
            print("[1b SERVER] Ignored malformed packet")
            continue

        seq, data_len, is_last = struct.unpack(HEADER_FMT, packet[:HEADER_SIZE])
        data = packet[HEADER_SIZE:HEADER_SIZE + data_len]

        chunks[seq] = data
        print(f"[1b SERVER] <- received seq={seq}, bytes={data_len}, is_last={is_last}")

        # Send ACK (one-packet-at-a-time)
        serverSocket.sendto(f"ACK:{seq}".encode(), clientAddress)
        print(f"[1b SERVER] -> sent ACK:{seq}")

        if is_last == 1:
            last_seq = seq

        if last_seq is not None and all(i in chunks for i in range(last_seq + 1)):
            with open(OUT_FILENAME, "wb") as f:
                for i in range(last_seq + 1):
                    f.write(chunks[i])

            total_bytes = sum(len(chunks[i]) for i in range(last_seq + 1))
            print(f"[1b SERVER] File received successfully ({total_bytes} bytes)")
            break

except KeyboardInterrupt:
    print("\n[1b SERVER] Shutting down.")
except Exception as e:
    print(f"[1b SERVER] ERROR: {e}")
finally:
    serverSocket.close()
